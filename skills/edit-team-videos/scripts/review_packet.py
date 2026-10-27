#!/usr/bin/env python3
"""Build task-local cut/transition review packets; never approve findings or delivery."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
from render_edit import map_time, probe, validate_plan
from quality_checks import source_parts


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def transcript_rows(path):
    text = path.read_text()
    data = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == '.jsonl' else json.loads(text)
    return validate_transcript(data.get('segments', []) if isinstance(data, dict) else data)


def validate_transcript(rows):
    if not isinstance(rows, list):
        raise ValueError('Transcript must contain a list of segments')
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('text'), str):
            raise ValueError('Transcript segments require text')
        validate_span(row)
        if 'words' in row:
            if not isinstance(row['words'], list):
                raise ValueError('words must be a list')
            for word in row['words']:
                if not isinstance(word, dict) or not isinstance(word.get('word'), str):
                    raise ValueError('Word timestamps require word text')
                validate_span(word)
    return rows


def validate_span(row):
    if any(type(row.get(k)) not in (int, float) or not math.isfinite(row[k]) for k in ('start', 'end')) or not 0 <= row['start'] <= row['end']:
        raise ValueError('Timestamps require finite, ordered, nonnegative numbers')


def cut_risks(cuts, rows, fps):
    words = [word for row in rows for word in row.get('words', [])]
    result = []
    for index, cut in enumerate(cuts):
        a = cut.get('start_frame', round(cut['start']*fps))/fps
        b = cut.get('end_frame', round(cut['end']*fps))/fps
        overlaps = [w for w in words if w['start'] < b and w['end'] > a]
        edges = [w for w in words if any(w['start'] < t < w['end'] for t in (a, b))]
        if edges or (cut.get('kind') == 'pause' and overlaps):
            result.append(dict(cut_index=index, start=a, end=b, kind=cut.get('kind'),
                               overlapping_words=overlaps, boundary_words=edges, reviewed=False))
    result.sort(key=lambda row: (row['kind'] != 'pause',row['start']))
    return dict(word_timestamps_available=bool(words), risks=result,
                note='ASR overlap flags review; it neither proves speech damage nor approves retaining an acoustic filler.')


def preview_windows(plan, fps, total_frames):
    keep = plan['keep_frame_ranges']
    duration = total_frames/fps
    events = [(0, 'opening'), (duration, 'ending')]
    elapsed = 0
    for a, b in keep[:-1]:
        elapsed += b-a
        events.append((elapsed/fps, 'splice'))
    for mask in plan.get('redactions', []):
        events.extend((map_time(mask[key], keep, fps), 'mask '+key) for key in ('source_start', 'source_end'))
    for zoom in plan.get('zooms', []):
        a, b = zoom['source_start'], zoom['source_end']
        events.extend((map_time(t, keep, fps), label) for t, label in
                      ((a, 'zoom entry'), ((a+b)/2, 'zoom peak'), (b, 'zoom exit')))
    intervals = []
    for t, label in sorted(events):
        before, after = (20, 0) if label == 'ending' else (1.5, 1.5)
        a, b = max(0, math.floor((t-before)*fps)), min(total_frames, math.ceil((t+after)*fps))
        if a >= b:
            continue
        if intervals and a <= intervals[-1]['end_frame']:
            intervals[-1]['end_frame'] = max(b, intervals[-1]['end_frame'])
            intervals[-1]['reasons'] = sorted(set(intervals[-1]['reasons']+[label]))
        else:
            intervals.append(dict(start_frame=a, end_frame=b, reasons=[label]))
    for index, row in enumerate(intervals):
        row.update(id=f'P{index:04}', start=row['start_frame']/fps, end=row['end_frame']/fps)
    return intervals


def privacy_groups(report, prior=None):
    for scan in (report, prior):
        if scan is None:
            continue
        if not isinstance(scan, dict) or not isinstance(scan.get('candidates'), list):
            raise ValueError('Privacy report requires candidates')
        for row in scan['candidates']:
            box = row.get('box')
            if (not isinstance(row.get('text_sha256'), str) or not row['text_sha256']
                    or not isinstance(box, list) or len(box) != 4
                    or any(type(n) is not int for n in box)
                    or min(box[:2]) < 0 or min(box[2:]) <= 0):
                raise ValueError('Privacy findings require a text hash and nonnegative integer crop geometry')
    known = {}
    for row in (prior or {}).get('candidates', []):
        known.setdefault(row['text_sha256'], set()).add(tuple(row['box']))
    groups = {}
    for row in report['candidates']:
        key = row['text_sha256']
        group = groups.setdefault(key, dict(text_sha256=key, candidates=[], comparison='new_text'))
        group['candidates'].append(row)
    for key, group in groups.items():
        if key in known:
            group['comparison'] = 'previously_seen_same_boxes' if all(tuple(r['box']) in known[key] for r in group['candidates']) else 'previously_seen_changed_boxes'
    order = {'new_text': 0, 'previously_seen_changed_boxes': 1, 'previously_seen_same_boxes': 2}
    return sorted(groups.values(), key=lambda g: (order[g['comparison']], g['text_sha256']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--transcript', type=Path)
    parser.add_argument('--privacy', type=Path)
    parser.add_argument('--prior-privacy', type=Path)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--render-preview', action='append', default=[], metavar='ID', help='Render selected P IDs through render_edit; repeat as needed')
    args = parser.parse_args()
    if args.prior_privacy and not args.privacy:
        parser.error('--prior-privacy requires --privacy')
    plan = json.loads(args.plan.read_text())
    source = Path(plan['source']).resolve(strict=True)
    source_hash = digest(source)
    if plan.get('source_sha256') and plan['source_sha256'] != source_hash:
        raise ValueError('Source changed after planning')
    video, rate, keep, tail, fade = validate_plan(plan, probe(source))
    fps = float(rate)
    windows = preview_windows(plan, fps, sum(b-a for a,b in keep)+tail)
    if set(args.render_preview)-{w['id'] for w in windows}:
        raise ValueError('Unknown preview ID')
    rows = transcript_rows(args.transcript) if args.transcript else []
    report = dict(schema_version=1, plan_sha256=digest(args.plan), source_sha256=source_hash,
                  transcript_sha256=digest(args.transcript) if args.transcript else None,
                  cut_review=cut_risks(plan.get('cut_decisions', []), rows, fps), previews=windows,
                  listening_review=dict(performed=False, reviewed_preview_ids=[], note='Record actual listening separately; generating clips does not constitute listening.'))
    args.work.mkdir(parents=True, exist_ok=False, mode=0o700)
    sections = ['<h1>Private video review packet</h1><p>Unapproved evidence. Previews do not replace final export scans or verification.</p>']
    sections.append('<h1>Speech-boundary review: pause risks first</h1>')
    if not report['cut_review']['word_timestamps_available']:
        sections.append('<p>No word timestamps available; no speech-boundary screening was possible.</p>')
    for risk in report['cut_review']['risks']:
        words = ' '.join(w['word'].strip() for w in risk['overlapping_words'])
        sections.append(f'<p>Cut {risk["cut_index"]} · {risk["start"]:.3f}–{risk["end"]:.3f}s · {html.escape(str(risk["kind"]))}: {html.escape(words)}</p>')
    for row in windows:
        identity = row['id']
        sections.append(f'<h2>{identity}: {row["start"]:.3f}–{row["end"]:.3f}s</h2><p>{html.escape(", ".join(row["reasons"]))}</p>')
        if identity in args.render_preview:
            subprocess.run([sys.executable, str(Path(__file__).with_name('render_edit.py')),
                            '--plan', str(args.plan.resolve()), '--work', str(args.work/identity),
                            '--output', str(args.work/f'{identity}.mp4'), '--preview-start', str(row['start']),
                            '--preview-end', str(row['end'])], check=True)
            sections.append(f'<p>Edited composition</p><video controls preload="none" src="{identity}.mp4"></video>')
            parts = source_parts(row['start'],row['end'],keep,fps)
            if parts:
                a, b = parts[0][0], parts[-1][1]
                before = f'{identity}-source.wav'
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-ss', str(a), '-i', str(source),
                                '-t', str(b-a), '-vn', '-c:a', 'pcm_s16le', str(args.work/before)], check=True)
                sections.append(f'<p>Original audio, source {a:.3f}–{b:.3f}s (includes removed material)</p><audio controls preload="none" src="{before}"></audio>')
                context = ' '.join(segment['text'].strip() for segment in rows if segment['end']>a and segment['start']<b)
                sections.append(f'<p>Source transcript context: {html.escape(context)}</p>')
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', str(args.work/f'{identity}.mp4'),
                            '-lavfi', 'showspectrumpic=s=1000x250:legend=1:scale=log', '-frames:v', '1',
                            str(args.work/f'{identity}-spectrum.png')], check=True)
            sections.append(f'<img src="{identity}-spectrum.png" alt="Preview spectrogram">')
    if args.privacy:
        current = json.loads(args.privacy.read_text())
        prior = json.loads(args.prior_privacy.read_text()) if args.prior_privacy else None
        report['privacy_sha256'] = digest(args.privacy)
        report['prior_privacy_sha256'] = digest(args.prior_privacy) if args.prior_privacy else None
        report['privacy_groups'] = []
        sections.append('<h1>Privacy groups: changed evidence first</h1><p>Hash/box matches only suggest review order. Every group still needs a current decision and scene context review.</p>')
        for index, group in enumerate(privacy_groups(current, prior)):
            candidate = group['candidates'][0]
            x,y,w,h = candidate['box']
            # Crop actual scanner evidence locally without introducing an imaging dependency.
            crop = f'privacy-{index:04}.png'
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', str(Path(candidate['frame']).resolve(strict=True)),
                            '-vf', f'crop={w}:{h}:{x}:{y}:exact=1', '-frames:v', '1', str(args.work/crop)], check=True)
            report['privacy_groups'].append(dict(text_sha256=group['text_sha256'], comparison=group['comparison'],
                                                observation_count=len(group['candidates']), representative_crop=crop, reviewed=False))
            sections.append(f'<p>{html.escape(group["text_sha256"])} · {group["comparison"]} · {len(group["candidates"])} observations</p><img src="{crop}" alt="Private OCR finding crop">')
    (args.work/'review-packet.json').write_text(json.dumps(report, indent=2)+'\n')
    (args.work/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Private review</title><style>body{background:#171717;color:#eee;font:16px system-ui;margin:24px}video,img{max-width:100%}</style>'+''.join(sections))
    print(json.dumps(dict(packet=str(args.work/'review-packet.json'), previews=len(windows), risky_cuts=len(report['cut_review']['risks']))))


if __name__ == '__main__':
    main()
