#!/usr/bin/env python3
"""Find acoustic filler candidates with a locally supplied Uhm ONNX model.

Uhm by Desert Ant Labs: https://desertant.com
Model terms and attribution: https://license.desertant.com/1.0
"""
import argparse
import hashlib
import json
from pathlib import Path
import wave

import numpy as np
import onnxruntime as ort

ort.disable_telemetry_events()


def detect(audio, session, threshold=.5, peak=.75, minimum=.08):
    times, probabilities = [], []
    for offset in range(0, len(audio), 24 * 16000):
        start = max(0, offset - 3 * 16000)
        stop = min(len(audio), start + 480000)
        clip = audio[start:stop]
        std = clip.std(ddof=1) if len(clip) > 1 else 0
        clip = (clip - clip.mean()) / (std + 1e-7)
        clip = np.pad(clip, (0, 480000-len(clip)))
        probs = session.run(['probs'], {'audio': clip[None, :].astype(np.float32)})[0][0]
        if (probs.ndim != 2 or probs.shape[1] != 6 or not np.isfinite(probs).all()
                or probs.min() < 0 or probs.max() > 1):
            raise ValueError('Unexpected model probabilities; inspect the current model layout')
        t = start / 16000 + np.arange(len(probs)) * .02 + .01
        valid = (t >= offset/16000) & (t < min(len(audio)/16000, offset/16000+24))
        times.extend(t[valid].tolist())
        probabilities.extend(probs[valid].tolist())
        print(f'Analyzed {min(len(audio)/16000,offset/16000+24):.1f}/{len(audio)/16000:.1f}s', flush=True)
    t = np.asarray(times)
    probs = np.asarray(probabilities)
    filler_prob = 1 - probs[:, 0]
    boundaries = np.flatnonzero(np.diff(np.r_[False, filler_prob >= threshold, False]))
    events = []
    for a, b in boundaries.reshape(-1, 2):
        if (b-a)*.02 + 1e-9 < minimum or filler_prob[a:b].max() < peak:
            continue
        label = int(probs[a:b, 1:].mean(axis=0).argmax())
        events.append({'start': max(0.,float(t[a]-.01)), 'end': min(len(audio)/16000,float(t[b-1]+.01)),
                       'peak': float(filler_prob[a:b].max()), 'mean': float(filler_prob[a:b].mean()),
                       'type': ['uh','um','hmm','and','other'][label]})
    return events, times, probabilities


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audio', type=Path, required=True, help='Mono 16 kHz 16-bit PCM WAV')
    p.add_argument('--model', type=Path, required=True, help='Local desert-ant-labs/uhm uhm.onnx')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--probabilities', type=Path)
    p.add_argument('--threshold', type=float, default=.5)
    p.add_argument('--peak', type=float, default=.75)
    p.add_argument('--minimum', type=float, default=.08)
    args = p.parse_args()
    if not (0 < args.threshold <= args.peak <= 1 and .02 <= args.minimum <= 5):
        p.error('Require 0 < threshold <= peak <= 1 and minimum between .02 and 5 seconds')
    if args.output.exists() or args.probabilities and args.probabilities.exists():
        raise FileExistsError('Choose new output paths to preserve prior scan evidence')
    with wave.open(str(args.audio), 'rb') as f:
        if (f.getframerate(),f.getnchannels(),f.getsampwidth()) != (16000,1,2):
            raise ValueError('Expected mono 16 kHz 16-bit PCM WAV')
        audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32)/32768
    if not len(audio):
        raise ValueError('Audio is empty')
    options = ort.SessionOptions()
    options.intra_op_num_threads = 6
    session = ort.InferenceSession(str(args.model), sess_options=options, providers=['CPUExecutionProvider'])
    if [(i.name,i.shape) for i in session.get_inputs()] != [('audio',[1,480000])]:
        raise ValueError('Model input layout changed; inspect the current model documentation')
    events, times, probabilities = detect(audio, session, args.threshold, args.peak, args.minimum)
    with args.model.open('rb') as model_file:
        digest = hashlib.file_digest(model_file,'sha256').hexdigest()
    result = {'audio':str(args.audio.resolve()),'duration_seconds':len(audio)/16000,
              'model_sha256':digest,
              'threshold':args.threshold,'event_peak':args.peak,'minimum_seconds':args.minimum,
              'events':events,'credit':'Uhm by Desert Ant Labs, https://desertant.com',
              'interpretation':'Acoustic candidates, not a guarantee that every hesitation was found'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2))
    if args.probabilities:
        args.probabilities.parent.mkdir(parents=True,exist_ok=True)
        args.probabilities.write_text(json.dumps(list(zip(times,probabilities))))
    print(f'{len(events)} candidates; details: {args.output}')


if __name__ == '__main__':
    main()
