#!/usr/bin/env python3
"""Render a reviewed frame-based edit plan with optional screen zooms/webcam matte."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import struct
import subprocess
import wave
import zlib

import numpy as np


def run(args):
    subprocess.run(args, check=True)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)
    ]))


def finite(value, name, lower=None, upper=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if lower is not None and value < lower or upper is not None and value > upper:
        raise ValueError(f'{name} is outside the allowed range')
    return float(value)


def balanced_sum(terms):
    if not terms:
        return '0'
    if len(terms) == 1:
        return terms[0]
    mid = len(terms) // 2
    return '(' + balanced_sum(terms[:mid]) + '+' + balanced_sum(terms[mid:]) + ')'


def rounded_mask(path, width, height, radius, shape='rounded_rectangle'):
    y, x = np.mgrid[:height, :width]
    qx = np.maximum(abs(x - (width - 1) / 2) - (width / 2 - radius), 0)
    qy = np.maximum(abs(y - (height - 1) / 2) - (height / 2 - radius), 0)
    pixels = np.rint(255 * np.clip(radius - np.hypot(qx, qy) + .5, 0, 1)).astype('uint8')
    if shape == 'rectangle':
        pixels[:] = 255
    elif shape == 'ellipse':
        distance = np.sqrt(((x-(width-1)/2)/(width/2))**2 + ((y-(height-1)/2)/(height/2))**2)
        pixels = np.rint(255*np.clip((1-distance)*min(width,height)/2+.5,0,1)).astype('uint8')

    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))

    rows = b''.join(b'\0' + row.tobytes() for row in pixels)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def map_time(source_time, keep, fps):
    elapsed = 0
    for a, b in keep:
        if a / fps <= source_time <= b / fps:
            return elapsed + source_time - a / fps
        if source_time < a / fps:
            return elapsed
        elapsed += (b - a) / fps
    return elapsed


def validate_plan(plan, metadata):
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    rate = Fraction(video['r_frame_rate'])
    average = Fraction(video['avg_frame_rate'])
    if rate != average or rate <= 0:
        raise ValueError('Expected constant frame rate; normalize a working copy before planning')
    frame_count = int(video['nb_frames'])
    keep = plan['keep_frame_ranges']
    if not isinstance(keep, list) or not keep:
        raise ValueError('keep_frame_ranges must be a nonempty list')
    previous = 0
    for row in keep:
        if (not isinstance(row, list) or len(row) != 2
                or any(type(n) is not int for n in row)):
            raise ValueError('Each retained range must contain two integer frame indexes')
        a, b = row
        if not previous <= a < b <= frame_count:
            raise ValueError('Retained ranges must be ordered, non-overlapping, and within the source')
        previous = b
    postroll = finite(plan.get('postroll_seconds', 1.2), 'postroll_seconds', 0, 10)
    fade = finite(plan.get('fade_out_seconds', .45), 'fade_out_seconds', 0, postroll)
    return video, rate, keep, round(postroll * rate), fade


def assemble_audio(source, work, keep, rate, postroll_frames):
    wav_path = work / 'source.wav'
    run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', str(source),
         '-vn', '-ar', '48000', '-c:a', 'pcm_s16le', str(wav_path)])
    with wave.open(str(wav_path), 'rb') as f:
        channels = f.getnchannels()
        if f.getsampwidth() != 2 or channels not in (1, 2):
            raise ValueError('Expected mono or stereo 16-bit PCM')
        samples = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).reshape(-1, channels)
        sample_rate = f.getframerate()
    cumulative = 0
    output = work / 'edited-audio.wav'
    with wave.open(str(output), 'wb') as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for index, (a, b) in enumerate(keep):
            start = round(Fraction(a * sample_rate, 1) / rate)
            end = round(Fraction(b * sample_rate, 1) / rate)
            target = (round(Fraction((cumulative + b - a) * sample_rate, 1) / rate)
                      - round(Fraction(cumulative * sample_rate, 1) / rate))
            clip = samples[start:end].astype(np.float32)
            if len(clip) < end - start:
                missing = end - start - len(clip)
                if missing > sample_rate * .1:
                    raise ValueError('Source audio ends unexpectedly early')
                clip = np.pad(clip, ((0, missing), (0, 0)))
            if len(clip) != target:
                if abs(len(clip) - target) > 1:
                    raise ValueError('Unexpected audio/video sample-grid mismatch')
                grid = np.linspace(0, len(clip) - 1, target)
                clip = np.stack([np.interp(grid, np.arange(len(clip)), clip[:, c])
                                 for c in range(channels)], axis=1)
            fade = min(round(sample_rate * .006), len(clip) // 2)
            if index:
                clip[:fade] *= np.linspace(0, 1, fade)[:, None]
            if index < len(keep) - 1:
                clip[-fade:] *= np.linspace(1, 0, fade)[:, None]
            f.writeframes(np.clip(clip, -32768, 32767).astype(np.int16).tobytes())
            cumulative += b - a
        tail_samples = (round(Fraction((cumulative + postroll_frames) * sample_rate, 1) / rate)
                        - round(Fraction(cumulative * sample_rate, 1) / rate))
        f.writeframes(np.zeros((tail_samples, channels), dtype=np.int16).tobytes())
    return output


def camera_for_zoom(plan, row, width, height):
    if plan.get('webcam'):
        raise ValueError('Legacy fixed webcam plans require migration to reviewed camera_layouts')
    matches = [c for c in plan.get('camera_layouts', [])
               if finite(c['source_start'], 'camera start', 0) <= row['source_start']
               and finite(c['source_end'], 'camera end', 0) >= row['source_end']]
    if len(matches) != 1 or matches[0].get('reviewed') is not True:
        raise ValueError('Every zoom needs exactly one reviewed, stable camera layout; split at layout changes')
    camera = matches[0]
    if not camera.get('evidence_frames'):
        raise ValueError('Camera layout requires inspected source-frame evidence')
    if camera['mode'] == 'absent':
        return None
    if camera['mode'] != 'overlay':
        raise ValueError('Disable zooms for unknown, moving, multiple-camera or full-camera layouts')
    crop = camera['crop']
    if not isinstance(crop, list) or len(crop) != 4 or any(type(n) is not int for n in crop):
        raise ValueError('camera crop must be integer [x,y,width,height]')
    x,y,w,h = crop
    margin = camera.get('erase_margin', 4)
    if type(margin) is not int or margin < 1 or not (margin <= x and margin <= y
            and x+w+margin < width and y+h+margin < height and w > 4 and h > 4):
        raise ValueError('Camera and erase margin must fit inside the frame; disable zoom if edge erasure is unsafe')
    shape = camera.get('shape')
    if shape not in ('rounded_rectangle','ellipse','rectangle'):
        raise ValueError('Explicitly review camera shape; no default matte geometry is assumed')
    radius = finite(camera.get('radius', 0), 'camera radius', 0, min(w,h)/2)
    if shape == 'rounded_rectangle' and radius == 0:
        raise ValueError('Review the rounded camera corner radius')
    return dict(crop=crop, shape=shape, radius=radius, erase_margin=margin)


def redaction_graph(plan, width, height, duration):
    graph, label = '', '0:v'
    for index, row in enumerate(plan.get('redactions', [])):
        if row.get('reviewed') is not True or not str(row.get('reason', '')).strip():
            raise ValueError('Redactions require an explicit reviewed decision and reason')
        start = finite(row['source_start'], 'redaction start', 0, duration)
        end = finite(row['source_end'], 'redaction end', start, duration)
        crop = row['box']
        if not isinstance(crop,list) or len(crop)!=4 or any(type(n) is not int for n in crop):
            raise ValueError('Redaction box must contain four integer pixels')
        x,y,w,h = crop
        if end<=start or min(x,y)<0 or min(w,h)<2 or x+w>width or y+h>height:
            raise ValueError('Invalid redaction bounds or duration')
        enabled = f'gte(t,{start})*lt(t,{end})'
        output = f'redacted{index}'
        if row.get('style','solid') == 'solid':
            graph += f"[{label}]drawbox=x={x}:y={y}:w={w}:h={h}:color=black:t=fill:enable='{enabled}'[{output}];"
        elif row['style'] == 'blur':
            radius = min(20,(min(w,h)-1)//4)
            if radius<1:
                raise ValueError('Blur region is too small; use a solid mask')
            graph += (f'[{label}]split[base{index}][patch{index}];'
                      f'[patch{index}]crop={w}:{h}:{x}:{y}:exact=1,boxblur=luma_radius={radius}:luma_power=2:chroma_radius={radius}:chroma_power=2[blur{index}];'
                      f"[base{index}][blur{index}]overlay={x}:{y}:format=rgb:enable='{enabled}'[{output}];")
        else:
            raise ValueError('Redaction style must be solid or blur')
        label = output
    return graph,label


def build_graph(plan, video, rate, keep, postroll_frames, fade, work):
    width, height = video['width'], video['height']
    fps = float(rate)
    source_duration = int(video['nb_frames'])/fps
    terms = [f'between(n,{a},{b-1})' for a, b in keep]
    graph,label = redaction_graph(plan,width,height,int(video['nb_frames'])/fps)
    graph += f"[{label}]select='{balanced_sum(terms)}',setpts=N/({rate.numerator}/{rate.denominator}*TB)[cut]"
    zooms = []
    previous_end = 0
    for row in plan.get('zooms', []):
        a = finite(row['source_start'], 'zoom source_start', 0, source_duration)
        b = finite(row['source_end'], 'zoom source_end', a, source_duration)
        scale = finite(row['scale'], 'zoom scale', 1, 2)
        ax = finite(row.get('anchor_x', .5), 'anchor_x', 0, 1)
        ay = finite(row.get('anchor_y', .2), 'anchor_y', 0, 1)
        start, end = map_time(a, keep, fps), map_time(b, keep, fps)
        if end <= start or start < previous_end:
            raise ValueError('Zoom intervals must retain speech, be ordered, and not overlap')
        ease = min(finite(row.get('ease_seconds', .7), 'ease_seconds', .05, 3), (end-start)/2)
        camera = camera_for_zoom(plan,row,width,height)
        zooms.append(dict(start=start, end=end, scale=scale, ax=ax, ay=ay, ease=ease, camera=camera))
        previous_end = end
    masks = []
    if zooms:
        envelopes, active = [], []
        ax, ay = '.5', '.2'
        for z in reversed(zooms):
            a, b, e = z['start'], z['end'], z['ease']
            t = f'on*{rate.denominator}/{rate.numerator}'
            inside = f'between({t},{a},{b})'
            ramp = f'if(lt({t},{a+e}),.5-.5*cos(PI*({t}-{a})/{e}),if(gt({t},{b-e}),.5-.5*cos(PI*({b}-{t})/{e}),1))'
            envelopes.append(f"{z['scale']-1}*if({inside},{ramp},0)")
            active.append(f'between(t,{a},{b})')
            ax = f"if({inside},{z['ax']},{ax})"
            ay = f"if({inside},{z['ay']},{ay})"
        enabled = balanced_sum(active)
        zoom_expr = '1+' + balanced_sum(envelopes)
        cameras = [(i,z) for i,z in enumerate(zooms) if z['camera']]
        input_label = 'cut'
        if cameras:
            graph += f';[cut]split={len(cameras)+1}[screen]' + ''.join(f'[cam{i}]' for i,_ in cameras)
            input_label = 'screen'
        for mask_index,(i,z) in enumerate(cameras):
            camera = z['camera']
            x,y,w,h = camera['crop']
            margin = camera['erase_margin']
            mask = work / f'webcam-mask-{i}.png'
            rounded_mask(mask,w,h,camera['radius'],camera['shape'])
            masks += ['-loop','1','-framerate',str(rate),'-i',str(mask)]
            graph += (f';[cam{i}]crop={w}:{h}:{x}:{y}:exact=1,format=rgb24[camrgb{i}]'
                      f';[camrgb{i}][{mask_index+2}:v]alphamerge[rgba{i}]'
                      f";[{input_label}]delogo=x={x-margin}:y={y-margin}:w={w+2*margin}:h={h+2*margin}:enable='between(t,{z['start']},{z['end']})'[clean{i}]")
            input_label = f'clean{i}'
        graph += (f";[{input_label}]zoompan=z='{zoom_expr}':x='(iw-iw/zoom)*({ax})'"
                  f":y='(ih-ih/zoom)*({ay})':d=1:s={width}x{height}:fps={rate}[zoomed]")
        label = 'zoomed'
        for i,z in cameras:
            x,y,_,_ = z['camera']['crop']
            graph += f";[{label}][rgba{i}]overlay=x={x}:y={y}:format=rgb:enable='between(t,{z['start']},{z['end']})':eof_action=endall:shortest=1[overlay{i}]"
            label = f'overlay{i}'
        graph += f';[{label}]null[composed]'
    else:
        graph += ';[cut]null[composed]'
    total_frames = sum(b-a for a,b in keep) + postroll_frames
    duration = total_frames / fps
    # Some filter chains carry the source's EOF timestamp in a different time
    # base. Reindex the exact frame-count hold before fading/encoding so a short
    # postroll cannot become thousands of duplicated frames.
    graph += (f';[composed]tpad=stop_mode=clone:stop={postroll_frames}'
              f',setpts=N/({rate.numerator}/{rate.denominator}*TB)')
    if fade:
        graph += f',fade=t=out:st={duration-fade}:d={fade}'
    graph += '[video]'
    return graph, masks, total_frames, zooms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preview-start', type=float, help='Output-time start of a private review clip')
    parser.add_argument('--preview-end', type=float, help='Output-time end; requires --preview-start')
    args = parser.parse_args()
    if (args.preview_start is None) != (args.preview_end is None):
        parser.error('Supply both --preview-start and --preview-end')
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.plan.read_text())
    source = Path(plan['source']).expanduser().resolve(strict=True)
    if plan.get('source_sha256'):
        with source.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=plan['source_sha256']:
                raise ValueError('Source changed after editorial review; prepare and review it again')
    metadata = probe(source)
    video, rate, keep, postroll_frames, fade = validate_plan(plan, metadata)
    args.work.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    graph, masks, total_frames, zooms = build_graph(plan, video, rate, keep, postroll_frames, fade, args.work)
    audio = assemble_audio(source, args.work, keep, rate, postroll_frames)
    preview = None
    original_duration = total_frames / float(rate)
    if args.preview_start is not None:
        start = finite(args.preview_start, 'preview start', 0, original_duration)
        end = finite(args.preview_end, 'preview end', start, original_duration)
        first, last = round(start*rate), round(end*rate)
        if last <= first:
            raise ValueError('Preview must contain at least one frame')
        preview = dict(start_frame=first,end_frame=last,start=first/float(rate),end=last/float(rate))
        graph = graph.removesuffix('[video]') + f'[fullvideo];[fullvideo]trim=start_frame={first}:end_frame={last},setpts=PTS-STARTPTS[video]'
        total_frames = last-first
    (args.work / 'filter.txt').write_text(graph)
    (args.work / 'mapped-zooms.json').write_text(json.dumps(zooms, indent=2))
    cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'warning', '-n',
           '-i', str(source), '-i', str(audio), *masks, '-filter_complex', graph,
           '-map', '[video]', '-map', '1:a', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
           '-threads', '6', '-pix_fmt', 'yuv420p', '-fps_mode', 'cfr', '-r', str(rate),
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-map_metadata', '-1']
    audio_filters = []
    if fade:
        audio_filters.append(f'afade=t=out:st={original_duration-fade}:d={fade}')
    if preview:
        audio_filters += [f'atrim=start={preview["start"]}:end={preview["end"]}', 'asetpts=PTS-STARTPTS']
    if audio_filters:
        cmd += ['-af', ','.join(audio_filters)]
    cmd += ['-progress', str(args.work / 'render-progress.txt'), str(args.output)]
    run(cmd)
    actual = probe(args.output)
    v = next(s for s in actual['streams'] if s['codec_type'] == 'video')
    a = next(s for s in actual['streams'] if s['codec_type'] == 'audio')
    if int(v['nb_frames']) != total_frames:
        raise RuntimeError(f'Frame count mismatch: {v["nb_frames"]} != {total_frames}')
    if (v['width'], v['height'], Fraction(v['r_frame_rate'])) != (video['width'], video['height'], rate):
        raise RuntimeError('Unexpected dimensions or frame rate')
    drift = abs(float(v['duration']) - float(a['duration']))
    if drift > 1 / float(rate) + .01:
        raise RuntimeError(f'Unexpected audio/video duration difference: {drift}')
    checked = subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(args.output),
                              '-f','null','-'], capture_output=True, text=True)
    if checked.returncode or checked.stderr.strip():
        raise RuntimeError(f'Export decode failed: {checked.stderr}')
    result = {'file': str(args.output.resolve()), 'video_frames': total_frames,
              'duration_seconds': float(v['duration']), 'audio_video_difference_seconds': drift,
              'full_decode': 'passed', 'zoom_count': len(zooms),
              'camera_masks': sum(z['camera'] is not None for z in zooms),
              'redaction_count': len(plan.get('redactions',[])), 'postroll_frames': postroll_frames,
              'review_preview': preview, 'delivery_candidate': preview is None}
    (args.work / 'validation.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
