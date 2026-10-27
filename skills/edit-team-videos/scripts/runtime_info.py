#!/usr/bin/env python3
"""Resolve a host-local runtime profile without putting machine paths in the skill."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=Path.home()/'.agents/resources/edit-team-videos-runtime.json')
    args = parser.parse_args()
    if not args.profile.is_file():
        raise SystemExit('No host runtime profile. Follow references/workflow.md setup with an isolated local environment and licensed model; no automatic install was attempted.')
    config = json.loads(args.profile.read_text())
    if config.get('schema_version')!=1:
        raise ValueError('Unsupported runtime profile version')
    paths = {}
    for key in ('python','filler_model'):
        value = config.get(key)
        if not isinstance(value,str) or not Path(value).is_absolute() or not Path(value).is_file():
            raise ValueError(f'Configured {key} is missing; refresh the host profile or follow setup instructions')
        paths[key] = value
    with Path(paths['filler_model']).open('rb') as f:
        sha = hashlib.file_digest(f,'sha256').hexdigest()
    if sha!=config.get('filler_model_sha256'):
        raise ValueError('Configured filler-model hash changed; inspect release/terms before updating the profile')
    versions = subprocess.check_output([paths['python'],'-c',
        'import json,numpy,onnxruntime,tokenizers; onnxruntime.disable_telemetry_events(); print(json.dumps({"numpy":numpy.__version__,"onnxruntime":onnxruntime.__version__,"tokenizers":tokenizers.__version__}))'],text=True)
    tools = {name:shutil.which(name) for name in ('ffmpeg','ffprobe','swiftc')}
    if not all(tools.values()):
        raise ValueError('FFmpeg, FFprobe and macOS Swift tools are required; inspect setup instructions')
    asr = config.get('asr_model')
    if asr is not None and (not isinstance(asr,str) or not Path(asr).is_absolute() or not (Path(asr)/'model.bin').is_file()):
        raise ValueError('Configured optional ASR model is missing; refresh the profile')
    pii = config.get('pii_model')
    if pii is not None and (not isinstance(pii,str) or not Path(pii).is_absolute() or not (Path(pii)/'model-lock.json').is_file()):
        raise ValueError('Configured PII model is missing; refresh the profile')
    if pii is not None and hashlib.sha256((Path(pii)/'model-lock.json').read_bytes()).hexdigest()!=config.get('pii_model_lock_sha256'):
        raise ValueError('Configured PII model lock changed; verify assets before updating the profile')
    print(json.dumps(dict(**paths,asr_model=asr,pii_model=pii,versions=json.loads(versions),tools=tools,
                          filler_model_sha256=sha,profile=str(args.profile))))


if __name__=='__main__':
    main()
