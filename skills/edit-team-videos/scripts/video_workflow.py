#!/usr/bin/env python3
"""Prepare compact review evidence, compile reviewed decisions, or verify an export."""
import argparse
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import wave

import numpy as np

sys.dont_write_bytecode = True
from render_edit import build_graph, probe, validate_plan
from review_packet import validate_transcript, cut_risks
from quality_checks import audit_source_fillers, audit_residuals, audit_privacy, draft_decisions, source_parts

SCRIPTS = Path(__file__).resolve().parent


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    temporary.replace(path)


def command(args, log):
    with log.open('w') as f:
        result = subprocess.run([str(a) for a in args],stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); see {log}')


class Job:
    """One immutable input/configuration per directory; verified stage outputs are reusable."""
    def __init__(self, root, inputs):
        self.root = root.resolve()
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(self.root,0o700)
        self.path = self.root/'manifest.json'
        packages = {}
        for name in ('numpy','onnxruntime','tokenizers','faster-whisper'):
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                packages[name] = None
        self.config = dict(inputs=inputs,python=sys.version,platform=platform.platform(),packages=packages,
                           ffmpeg=subprocess.check_output(['ffmpeg','-version'],text=True),
                           ffprobe=subprocess.check_output(['ffprobe','-version'],text=True),
                           swift=subprocess.check_output(['swiftc','--version'],text=True,stderr=subprocess.STDOUT),
                           scripts={p.name:digest(p) for p in sorted(SCRIPTS.iterdir()) if p.suffix in ('.py','.swift')})
        self.data = json.loads(self.path.read_text()) if self.path.exists() else dict(config=self.config,stages={})
        if self.data['config'] != self.config:
            raise ValueError('Job inputs, tools, or configuration changed; use a fresh work directory')
        save(self.path,self.data)

    def stage(self, name, outputs, action):
        if name in self.data['stages']:
            if any(not p.exists() or digest(p)!=sha for p,sha in
                   [(self.root/k,v) for k,v in self.data['stages'][name].items()]):
                raise ValueError(f'Cached {name} evidence changed or disappeared; use a fresh job')
            return
        if any(p.exists() for p in outputs):
            raise FileExistsError(f'Untracked partial {name} outputs exist; inspect them and use a fresh job')
        action()
        self.data['stages'][name] = {str(p.relative_to(self.root)):digest(p) for p in outputs}
        save(self.path,self.data)


def vision_binary(job):
    binary = job.root/'vision-detect'
    job.stage('vision-build',[binary],lambda: command([
        'swiftc','-module-cache-path',job.root/'swift-cache',SCRIPTS/'detect_layout.swift','-o',binary
    ],job.root/'vision-build.log'))
    return binary


def vision_call(binary, images, log, ocr=False):
    result = subprocess.run([str(binary),*(['--ocr'] if ocr else []),*[str(p) for p in images]],capture_output=True)
    log.write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(f'Apple Vision failed; see {log}. A restricted sandbox may block image buffers; retry only this local stage with host permission.')
    rows = json.loads(result.stdout)
    if len(rows)!=len(images):
        raise ValueError('Vision result count differs from input frames')
    return rows


def frames(job, source, times, prefix='sample'):
    images = [job.root/f'{prefix}-{i:04}.png' for i in range(len(times))]
    def extract():
        for at,path in zip(times,images):
            command(['ffmpeg','-nostdin','-v','error','-n','-ss',f'{at:.6f}','-i',source,
                     '-frames:v','1',path],job.root/f'{prefix}-extract.log')
    job.stage(prefix+'-frames',images,extract)
    return images


def contact_sheets(job, count, prefix='sample'):
    sheets = [job.root/f'{prefix}-sheet-{i+1:03}.jpg' for i in range((count+11)//12)]
    job.stage(prefix+'-sheets',sheets,lambda: command([
        'ffmpeg','-nostdin','-v','error','-n','-framerate','1','-i',job.root/f'{prefix}-%04d.png',
        '-vf','scale=416:-2,tile=4x3:padding=4:margin=4','-frames:v',len(sheets),
        job.root/f'{prefix}-sheet-%03d.jpg'
    ],job.root/f'{prefix}-sheets.log'))
    return [str(p) for p in sheets]


def layout_candidates(row):
    proposals = []
    width,height = row['width'],row['height']
    for face in sorted(row['faces'],key=lambda f:tuple(f['box'])):
        x,y,w,h = face['box']
        panels = []
        for rectangle in row['rectangles']:
            a,b,c,d = rectangle['box']
            area_ratio = c*d/max(1,w*h)
            if (a<=x and b<=y and a+c>=x+w and b+d>=y+h
                    and 1.6<=area_ratio<=16 and .45<=c/d<=2.3 and c*d<width*height*.45):
                panels.append((abs(np.log(area_ratio/5)),rectangle['box']))
        proposals.append(dict(face=face['box'],face_confidence=face['confidence'],
                              panel_candidates=[box for _,box in sorted(panels)[:3]],shape='unverified',
                              classification='full_camera_possible' if w*h>width*height*.12 else 'overlay_or_screen_content'))
    return proposals


def layout_change_hints(rows, times):
    hints = []
    for index in range(1,len(rows)):
        before,after = rows[index-1],rows[index]
        reasons = []
        if len(before['faces'])!=len(after['faces']):
            reasons.append('detected_face_count_changed')
        elif len(after['faces'])==1:
            boxes = []
            for row in (before,after):
                x,y,w,h = row['faces'][0]['box']
                boxes.append(((x+w/2)/row['width'],(y+h/2)/row['height'],w*h/(row['width']*row['height'])))
            a,b = boxes
            if math.hypot(a[0]-b[0],a[1]-b[1])>.08:
                reasons.append('face_position_changed')
            if abs(math.log(max(a[2],1e-9)/max(b[2],1e-9)))>math.log(1.6):
                reasons.append('face_scale_changed')
        if reasons:
            hints.append(dict(between_samples=[f'S{index-1:04}',f'S{index:04}'],
                              source_interval=[times[index-1],times[index]],reasons=reasons))
    return hints


def transcribe(audio_path, model_path, output):
    from faster_whisper import WhisperModel
    with wave.open(str(audio_path),'rb') as f:
        audio = np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).astype(np.float32)/32768
    model = WhisperModel(str(model_path),device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
    segments,_ = model.transcribe(audio,beam_size=3,word_timestamps=True,condition_on_previous_text=False)
    save(output,[dict(start=s.start,end=s.end,text=s.text.strip(),
                      words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in s.words or []])
                 for s in segments])


def prepare(args):
    source = args.source.resolve(strict=True)
    model = args.model.resolve(strict=True)
    metadata = probe(source)
    video = next(s for s in metadata['streams'] if s['codec_type']=='video')
    duration = int(video['nb_frames'])/float(Fraction(video['r_frame_rate']))
    validate_plan(dict(keep_frame_ranges=[[0,int(video['nb_frames'])]]),metadata)
    if not .25<=args.interval<=60:
        raise ValueError('Sample interval must be .25–60 seconds')
    times = sorted(set([round(min(.5,duration/2),6),round(max(0,duration-.5),6)]
                       + [round(float(t),6) for t in np.arange(args.interval,duration,args.interval)]
                       + [float(t) for t in args.times.split(',') if t]))
    if any(not 0<=t<duration for t in times):
        raise ValueError('Extra sample times must be inside the source')
    inputs = dict(phase='prepare',source=str(source),source_sha256=digest(source),model_sha256=digest(model),
                  sample_times=times,transcript_sha256=digest(args.transcript) if args.transcript else None,
                  asr_model_files={str(p.relative_to(args.asr_model)):digest(p) for p in sorted(args.asr_model.rglob('*')) if p.is_file()} if args.asr_model else None)
    job = Job(args.work,inputs)
    save(job.root/'source-metadata.json',metadata)
    audio16,audio48 = job.root/'source-16k.wav',job.root/'source-48k.wav'
    for rate,path in [(16000,audio16),(48000,audio48)]:
        cmd = ['ffmpeg','-nostdin','-v','error','-n','-i',source,'-vn','-ar',rate,'-c:a','pcm_s16le']
        if rate==16000:
            cmd += ['-ac','1']
        job.stage(f'audio-{rate}',[path],lambda cmd=cmd,path=path: command(cmd+[path],job.root/f'audio-{rate}.log'))
    candidates = job.root/'filler-candidates.json'
    job.stage('fillers',[candidates],lambda: command([
        sys.executable,SCRIPTS/'detect_fillers.py','--audio',audio16,'--model',model,'--output',candidates
    ],job.root/'fillers.log'))
    images = frames(job,source,times)
    binary = vision_binary(job)
    raw = job.root/'layout-detections.json'
    def detect():
        # No shell/network; raw image analysis stays in this private job directory.
        save(raw,vision_call(binary,images,job.root/'vision-detect.log'))
    job.stage('layouts',[raw],detect)
    transcript = job.root/'transcript.json'
    if args.transcript:
        def import_transcript():
            data = json.loads(args.transcript.read_text())
            rows = validate_transcript(data.get('segments',[]) if isinstance(data,dict) else data)
            if not isinstance(rows,list) or any(not isinstance(s,dict) or not isinstance(s.get('text'),str)
                    or not all(isinstance(s.get(k),(int,float)) and not isinstance(s[k],bool)
                               and math.isfinite(s[k]) for k in ('start','end'))
                    or not 0<=s['start']<=s['end']<=duration+.1 for s in rows):
                raise ValueError('Transcript segments require finite source times and text')
            save(transcript,rows)
        job.stage('transcript',[transcript],import_transcript)
    elif args.asr_model:
        job.stage('transcript',[transcript],lambda: transcribe(audio16,args.asr_model,transcript))
    rows = json.loads(transcript.read_text()) if transcript.exists() else []
    def context(start,end):
        return [f'T{i:04}' for i,s in enumerate(rows) if s['end']>=start-2 and s['start']<=end+2]
    filler_rows = [dict(id=f'F{i:04}',start=round(event['start'],3),end=round(event['end'],3),
                        type=event['type'],peak=round(event['peak'],3),segments=context(event['start'],event['end']))
                   for i,event in enumerate(json.loads(candidates.read_text())['events'])]
    with wave.open(str(audio16),'rb') as f:
        audio = np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).astype(np.float32)/32768
    length = len(audio)//320
    quiet = np.sqrt(np.mean(audio[:length*320].reshape(-1,320)**2,axis=1)) < 10**(-42/20)
    boundaries = np.flatnonzero(np.diff(np.r_[False,quiet,False])).reshape(-1,2)
    pauses = [dict(id=f'P{i:04}',start=round(a*.02,3),end=round(b*.02,3),segments=context(a*.02,b*.02))
              for i,(a,b) in enumerate(boundaries.tolist()) if b-a>=38]
    detections = json.loads(raw.read_text())
    hints = layout_change_hints(detections,times)
    layouts = [dict(id=f'S{i:04}',time=at,frame=str(image),proposals=layout_candidates(row),
                    status='needs_review' if row['faces'] else 'no_face_detected_not_proof_of_absence')
               for i,(at,image,row) in enumerate(zip(times,images,detections))]
    packet = dict(source_sha256=inputs['source_sha256'],duration=duration,
                  dimensions=[video['width'],video['height']],fps=video['r_frame_rate'],
                  filler_candidates=filler_rows,pause_candidates=pauses,layout_samples=layouts,layout_change_hints=hints,
                  contact_sheets=contact_sheets(job,len(images)),transcript=str(transcript) if rows else None,
                  gates=['Resolve every source filler; overlapping ASR timestamps are not a keep decision',
                         'Review pacing, causal order and camera layouts',
                         'Required local secrets/PII/context scan, review, masks and final-export rescan'])
    transcript_text = '\n'.join(
        f'T{i:04} [{s["start"]:.2f}–{s["end"]:.2f}] {s["text"].strip()}' for i,s in enumerate(rows))+'\n'
    lines = ['id\tstart\tend\ttype\tpeak\ttranscript_segments']
    for row in filler_rows+pauses:
        lines.append(f'{row["id"]}\t{row["start"]:.3f}\t{row["end"]:.3f}\t{row.get("type","pause")}\t{row.get("peak","")}\t'+','.join(row['segments']))
    template = dict(source_sha256=inputs['source_sha256'],editorial_reviewed=False,accept_filler_ids=[],
                    retain_fillers=[],cuts=[],camera_layouts=[],zooms=[],redactions=[],postroll_seconds=1.2,fade_out_seconds=.45)
    # Templates are generated separately; an agent's decisions file is never overwritten.
    summary = dict(review=str(job.root/'review.json'),source_sha256=inputs['source_sha256'],duration=duration,
                   fillers=len(filler_rows),pauses=len(pauses),layout_samples=len(layouts),layout_change_hints=hints,
                   transcript_available=bool(rows),transcript=str(job.root/'transcript.txt'),
                   candidates=str(job.root/'candidates.tsv'),contact_sheets=packet['contact_sheets'],
                   decisions_template=str(job.root/'decisions-template.json'),draft=str(job.root/'decisions-draft.json'))
    def write_packet():
        save(job.root/'review.json',packet)
        (job.root/'transcript.txt').write_text(transcript_text)
        (job.root/'candidates.tsv').write_text('\n'.join(lines)+'\n')
        save(job.root/'decisions-template.json',template)
        save(job.root/'decisions-draft.json',draft_decisions(packet))
        save(job.root/'review-summary.json',summary)
    job.stage('review-packet',[job.root/name for name in
              ['review.json','transcript.txt','candidates.tsv','decisions-template.json','decisions-draft.json','review-summary.json']],write_packet)
    print(json.dumps(summary))


def compile_plan(args):
    review = json.loads((args.prepared/'review.json').read_text())
    manifest = json.loads((args.prepared/'manifest.json').read_text())
    prepared_job = Job(args.prepared,manifest['config']['inputs'])
    for name in prepared_job.data['stages']:
        prepared_job.stage(name,[],lambda:None)
    source = Path(manifest['config']['inputs']['source'])
    decisions = json.loads(args.decisions.read_text())
    if decisions['source_sha256']!=review['source_sha256'] or digest(source)!=review['source_sha256']:
        raise ValueError('Review decisions do not match this source')
    if decisions.get('editorial_reviewed') is not True:
        raise ValueError('Review complete speech, caveats, opening, closing and cut transitions first')
    brief = decisions.get('edit_brief',{})
    if (not isinstance(brief,dict) or any(not isinstance(brief.get(k),str) or len(brief[k].strip())<12
            for k in ('purpose','pacing','continuity','ending'))):
        raise ValueError('Record an actual edit_brief: purpose, pacing, continuity and ending decisions')
    if args.output.exists():
        raise FileExistsError(args.output)
    candidates = {row['id']:row for row in review['filler_candidates']}
    approved = decisions.get('accept_filler_ids',[])
    if not isinstance(approved,list) or len(set(approved))!=len(approved) or any(i not in candidates for i in approved):
        raise ValueError('Accepted filler IDs must be unique IDs from this source review packet')
    cuts = [dict(start=candidates[i]['start'],end=candidates[i]['end'],kind='filler',
                 reason=f'Reviewed acoustic candidate {i}') for i in approved]
    cuts += decisions.get('cuts',[])
    filler_audit = audit_source_fillers(review['filler_candidates'],decisions,
                                      [[c['start'],c['end']] for c in decisions.get('cuts',[])])
    scratch = args.output.parent/(args.output.stem+'-evidence')
    scratch.mkdir(parents=True,exist_ok=False)
    save(scratch/'cuts.json',cuts)
    command([sys.executable,SCRIPTS/'plan_edit.py','--source',source,'--cuts',scratch/'cuts.json',
             '--audio',args.prepared/'source-48k.wav','--output',scratch/'base.json'],scratch/'planner.log')
    plan = json.loads((scratch/'base.json').read_text())
    for key in ('camera_layouts','zooms','redactions','postroll_seconds','fade_out_seconds'):
        if key in decisions:
            plan[key] = decisions[key]
    evidence = {s['id']:s for s in review['layout_samples']}
    for camera in plan.get('camera_layouts',[]):
        samples = camera.get('evidence_frames',[])
        if not samples or any(s not in evidence for s in samples):
            raise ValueError('Camera evidence must reference sampled frames in this prepared job')
        for zoom in plan.get('zooms',[]):
            if camera['source_start']<=zoom['source_start'] and camera['source_end']>=zoom['source_end']:
                # Coarse global sampling alone cannot establish a zoom layout is stable.
                checks = [zoom['source_start'],(zoom['source_start']+zoom['source_end'])/2,zoom['source_end']]
                if any(min(abs(evidence[s]['time']-t) for s in samples)>1 for t in checks):
                    raise ValueError('Add source samples within 1s of zoom start, midpoint, and end; then review layout')
    video,rate,keep,tail,fade = validate_plan(plan,probe(source))
    build_graph(plan,video,rate,keep,tail,fade,scratch)
    rows = json.loads((args.prepared/'transcript.json').read_text()) if (args.prepared/'transcript.json').exists() else []
    speech_review = cut_risks(plan.get('cut_decisions',[]),rows,float(rate))
    save(scratch/'speech-risk-review.json',speech_review)
    plan.update(source_sha256=review['source_sha256'],schema_version=2,
                source_filler_audit=filler_audit,source_retained_fillers=decisions.get('retain_fillers',[]),edit_brief=brief,
                prepared_manifest_sha256=digest(args.prepared/'manifest.json'))
    save(args.output,plan)
    print(json.dumps(dict(plan=str(args.output),retained_ranges=len(keep),zooms=len(plan.get('zooms',[])),
                          risky_cuts=len(speech_review['risks']),word_timestamps_available=speech_review['word_timestamps_available'],
                          speech_review=str(scratch/'speech-risk-review.json'))))


def verify(args):
    output = args.video.resolve(strict=True)
    plan = json.loads(args.plan.read_text())
    job = Job(args.work,dict(phase='verify',video_sha256=digest(output),plan_sha256=digest(args.plan),
                            model_sha256=digest(args.model)))
    metadata = probe(output)
    video = next(s for s in metadata['streams'] if s['codec_type']=='video')
    audio = next(s for s in metadata['streams'] if s['codec_type']=='audio')
    original = probe(plan['source'])
    if plan.get('source_sha256') and digest(plan['source'])!=plan['source_sha256']:
        raise ValueError('Source changed since plan review')
    source_video,rate,keep,tail,fade = validate_plan(plan,original)
    graph,_,expected,zooms = build_graph(plan,source_video,rate,keep,tail,fade,job.root)
    drift = abs(float(video['duration'])-float(audio['duration']))
    if (int(video['nb_frames'])!=expected or drift>1/float(rate)+.01
            or (video['width'],video['height'],Fraction(video['r_frame_rate'])) !=
               (source_video['width'],source_video['height'],rate)):
        raise ValueError('Export dimensions, frame count, FPS, or A/V duration failed verification')
    decode = job.root/'decode.log'
    job.stage('decode',[decode],lambda: command(['ffmpeg','-nostdin','-v','error','-xerror','-i',output,'-f','null','-'],decode))
    if decode.read_text().strip():
        raise ValueError(f'Decode emitted errors; inspect {decode}')
    mono = job.root/'export-16k.wav'
    job.stage('audio',[mono],lambda: command(['ffmpeg','-nostdin','-v','error','-n','-i',output,'-vn',
                                            '-ac','1','-ar','16000','-c:a','pcm_s16le',mono],job.root/'audio.log'))
    candidates = job.root/'export-candidates.json'
    job.stage('residual-fillers',[candidates],lambda: command([sys.executable,SCRIPTS/'detect_fillers.py',
              '--audio',mono,'--model',args.model,'--output',candidates],job.root/'fillers.log'))
    events = json.loads(candidates.read_text())['events']
    mapped = [dict(id=f'R{i:04}',**event,source_parts=source_parts(event['start'],event['end'],keep,float(rate)))
              for i,event in enumerate(events)]
    save(job.root/'residual-review.json',dict(video_sha256=digest(output),scan_sha256=digest(candidates),
                                            candidates=mapped,retain_fillers=[],
                                            instruction='Resolve each residual by revising source cuts and rerendering, or document actual words proving a false positive/meaningful vocalization. Never silently keep an ambiguous um.'))
    filler_decisions = json.loads(args.filler_review.read_text()) if args.filler_review else None
    filler_status = audit_residuals(events,filler_decisions,digest(output),digest(candidates))
    privacy_decisions = json.loads(args.privacy_review.read_text()) if args.privacy_review else {}
    privacy_status = {}
    for side,report_path,sha,audit_plan in [
        ('source',args.privacy_source,plan.get('source_sha256',digest(plan['source'])),dict(plan,fps_for_audit=float(rate))),
        ('export',args.privacy_export,digest(output),dict(keep_frame_ranges=[[0,expected]],redactions=[],fps_for_audit=float(rate)))]:
        report = json.loads(report_path.read_text()) if report_path else None
        privacy_status[side] = audit_privacy(report,privacy_decisions.get(side),sha,
                                             digest(report_path) if report_path else None,audit_plan)
    duration = float(video['duration'])
    # Opening/ending, every splice, and every zoom entry/peak/exit are made reviewable.
    times = [.1,min(2,duration/2),max(0,duration-2),max(0,duration-.6)]
    elapsed = 0
    for a,b in keep[:-1]:
        elapsed += (b-a)/float(rate)
        times += [elapsed-.08,elapsed+.08]
    for z in zooms:
        times += [z['start'],z['start']+.35,(z['start']+z['end'])/2,z['end']-.35,z['end']]
    times = sorted(set(round(max(0,min(duration-1/float(rate),t)),6) for t in times))
    images = frames(job,output,times,prefix='check')
    result = dict(file=str(output),duration=duration,frames=expected,full_decode='passed',av_difference=drift,
                  residual_candidates=len(events),filler_review=filler_status,privacy_review=privacy_status,
                  candidate_details=str(candidates),preview_times=times,
                  contact_sheets=contact_sheets(job,len(images),prefix='check'),
                  editorial_quality='requires model or human review; integrity checks are not listening',
                  ready_for_delivery=(bool(plan.get('source_filler_audit')) and filler_status['status']=='passed'
                                      and all(s['status']=='passed' for s in privacy_status.values())),
                  sanitization='Recorded review of sampled evidence, not a guarantee that every sensitive exposure was detected')
    save(job.root/'review.json',result)
    print(json.dumps(result))
    if not result['ready_for_delivery']:
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    phases = parser.add_subparsers(dest='phase',required=True)
    p = phases.add_parser('prepare')
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--interval',type=float,default=15)
    p.add_argument('--times',default='',help='Additional comma-separated source seconds, especially zoom boundaries/peaks')
    p.add_argument('--transcript',type=Path)
    p.add_argument('--asr-model',type=Path,help='Optional existing local faster-whisper model directory')
    p.set_defaults(action=prepare)
    p = phases.add_parser('plan')
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--decisions',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.set_defaults(action=compile_plan)
    p = phases.add_parser('verify')
    p.add_argument('--video',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--filler-review',type=Path,help='Reviewed residual false positives bound to the exact export and scan')
    p.add_argument('--privacy-source',type=Path,help='Required trained-PII scan report for the original source')
    p.add_argument('--privacy-export',type=Path,help='Required trained-PII scan report for the actual export')
    p.add_argument('--privacy-review',type=Path,help='Required source/export privacy dispositions and contextual notes')
    p.set_defaults(action=verify)
    args = parser.parse_args()
    args.action(args)


if __name__=='__main__':
    main()
