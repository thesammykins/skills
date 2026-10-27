#!/usr/bin/env python3
"""Convert reviewed source-time cuts into a frame-based render plan."""
import argparse
import json
from pathlib import Path
import sys
import wave

import numpy as np

sys.dont_write_bytecode = True
from render_edit import finite, probe


def snap(target, samples, sample_rate, fps, side, midpoint):
    center = round(target*fps)
    radius = round(.18*fps)
    half_window = max(1,round(sample_rate*.005))
    choices = []
    for frame in range(max(0,center-radius),min(round(len(samples)/sample_rate*fps),center+radius)+1):
        # A deeper quiet patch on the wrong side of the event can otherwise
        # pull both edges before the actual hesitation, leaving it untouched.
        if side == 'start' and frame/fps >= midpoint-.02:
            continue
        if side == 'end' and frame/fps <= midpoint+.02:
            continue
        at = round(frame/fps*sample_rate)
        clip = samples[max(0,at-half_window):min(len(samples),at+half_window)]
        if not len(clip):
            continue
        db = 20*np.log10(np.sqrt(np.mean(clip**2))+1e-9)
        choices.append((db+140*abs(frame/fps-target),frame))
    return min(choices)[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--cuts',type=Path,required=True,help='JSON list of reviewed {start,end,reason,kind} cuts')
    p.add_argument('--audio',type=Path,help='PCM WAV used only to refine kind=filler cuts at energy minima')
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    metadata = probe(args.source)
    video = next(x for x in metadata['streams'] if x['codec_type']=='video')
    from fractions import Fraction
    rate = Fraction(video['r_frame_rate'])
    if rate != Fraction(video['avg_frame_rate']):
        raise ValueError('Normalize a working copy of variable-frame-rate input before planning')
    fps = float(rate)
    frames = int(video['nb_frames'])
    samples = sample_rate = None
    if args.audio:
        with wave.open(str(args.audio),'rb') as f:
            if f.getsampwidth()!=2:
                raise ValueError('Boundary refinement requires 16-bit PCM')
            sample_rate = f.getframerate()
            samples = np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).reshape(-1,f.getnchannels()).mean(axis=1)/32768
        if abs(len(samples)/sample_rate-frames/fps)>.1:
            raise ValueError('Boundary audio must match the complete source recording')
    cuts, decisions = [], []
    for row in json.loads(args.cuts.read_text()):
        a = finite(row['start'],'cut start',0,frames/fps)
        b = finite(row['end'],'cut end',a,frames/fps)
        if b<=a or not isinstance(row.get('reason'),str) or not row['reason'].strip():
            raise ValueError('Each cut must have positive duration and a reason')
        start,end=round(a*fps),round(b*fps)
        if row.get('kind')=='filler' and row.get('snap',True):
            if samples is None:
                raise ValueError('Supply --audio to refine filler boundaries, or use snap:false for a reviewed exact cut')
            midpoint=(a+b)/2
            start=snap(a,samples,sample_rate,fps,'start',midpoint)
            end=snap(b,samples,sample_rate,fps,'end',midpoint)
        if end<=start:
            raise ValueError('Cut collapsed on the frame grid; review its boundaries')
        cuts.append([start,end])
        decisions.append({**row,'start_frame':start,'end_frame':end})
    merged=[]
    for a,b in sorted(cuts):
        if merged and a<=merged[-1][1]+round(.05*fps):
            merged[-1][1]=max(b,merged[-1][1])
        else:
            merged.append([a,b])
    keep=[];cursor=0
    for a,b in merged:
        if a>cursor:keep.append([cursor,a])
        cursor=b
    if cursor<frames:keep.append([cursor,frames])
    if not keep:
        raise ValueError('The cuts remove the entire recording')
    plan={'source':str(args.source.resolve()),'keep_frame_ranges':keep,'cut_decisions':decisions,
          'postroll_seconds':1.2,'fade_out_seconds':.45,'zooms':[]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(plan,indent=2))
    print(f'{sum(b-a for a,b in keep)/fps:.3f}s retained; review the ending and add purposeful zooms before rendering')


if __name__=='__main__':
    main()
