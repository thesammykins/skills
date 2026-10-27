#!/usr/bin/env python3
"""Local sampled OCR + trained PII detection + secret/context rules; propose masks."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import ipaddress
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

sys.dont_write_bytecode = True
from video_workflow import Job, digest, frames, probe, save, vision_binary, vision_call
from detect_pii import PiiDetector

PATTERNS = {
    'email': r'\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b',
    'url_review_context': r'\bhttps?://[^\s<>]+',
    'ipv4_review_context': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'credential_like': r'\b(?:AKIA[A-Z0-9]{16}|gh[pousr]_[A-Z0-9_]{20,}|github_pat_[A-Z0-9_]{20,}|xox[baprs]-[A-Z0-9-]{15,}|sk-[A-Z0-9_-]{20,})\b',
    'jwt_like': r'\beyJ[A-Z0-9_-]{8,}\.[A-Z0-9_-]{8,}\.[A-Z0-9_-]{8,}\b',
    'private_key_header': r'\bBEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY\b',
    'sensitive_field_review_context': r'\b(?:password|passwd|secret|api[ _-]?key|access[ _-]?token|client[ _-]?secret|recovery[ _-]?code|one[ _-]?time[ _-]?code|ssws)\s*[\"\x27]?\s*[:=]\s*\S+',
    'bearer_credential': r'\bBearer\s+[A-Z0-9._~+/=-]{12,}',
    'credential_connection_url': r'\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@]+:[^\s@]+@',
    'business_context_review': r'\b(?:confidential|internal[ -]only|customer|incident|vulnerability|tenant[ _-]?id|roadmap|salary|payroll|contract|account[ _-]?number|security\s+(?:policy|configuration)|access[ -]review|employee[ -]id)\b',
    'australian_identifier_context': r'\b(?:TFN|tax\s+file\s+number|Medicare|driver[\x27s ]+licen[cs]e|ABN|passport)\b',
}


def classify(text, terms):
    kinds = []
    for kind,pattern in PATTERNS.items():
        matches = re.findall(pattern,text,re.IGNORECASE)
        if kind=='ipv4_review_context':
            matches = [v for v in matches if valid_ip(v)]
        if matches:
            kinds.append(kind)
    if any(term.casefold() in text.casefold() for term in terms):
        kinds.append('configured_literal')
    if any(luhn(value) for value in re.findall(r'(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)',text)):
        kinds.append('payment_card_luhn')
    for value in re.findall(r'[A-Z0-9_+/=-]{20,128}',text,re.IGNORECASE):
        classes=sum(bool(re.search(pattern,value)) for pattern in ('[a-z]','[A-Z]','[0-9]','[_+/=-]'))
        entropy=-sum((n/len(value))*math.log2(n/len(value)) for n in Counter(value).values())
        if classes>=3 and entropy>=3.5:
            kinds.append('high_entropy_token_review')
            break
    return kinds


def rule_line_kinds(lines, terms):
    result=[];private_key=False;next_value=False
    for row in lines:
        text=row['text']
        kinds=set(classify(text,terms))
        if 'private_key_header' in kinds:
            private_key=True
        if private_key:
            kinds.add('private_key_block')
        if next_value:
            kinds.add('sensitive_value_after_label')
        next_value=bool(re.search(r'\b(?:password|passwd|api[ _-]?key|client[ _-]?secret|access[ _-]?token|recovery[ _-]?code|one[ _-]?time[ _-]?code|TFN|Medicare|passport)\s*[\"\x27]?\s*:\s*[\"\x27]?\s*$',text,re.IGNORECASE))
        if re.search(r'\bEND\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY\b',text,re.IGNORECASE):
            private_key=False
        result.append(sorted(kinds))
    return result


def luhn(value):
    digits = [int(c) for c in value if c.isdigit()]
    if not 13<=len(digits)<=19 or len(set(digits))<2:
        return False
    total = 0
    for i,digit in enumerate(reversed(digits)):
        if i%2:
            digit *= 2
            if digit>9:digit-=9
        total += digit
    return total%10==0


def valid_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def privacy_summary(report):
    groups = {}
    for row in report['candidates']:
        key = row['text_sha256']
        groups.setdefault(key,[]).append(row)
    summaries = []
    for index,(key,rows) in enumerate(sorted(groups.items())):
        boxes = [r['box'] for r in rows]
        x,y = min(b[0] for b in boxes),min(b[1] for b in boxes)
        right,bottom = max(b[0]+b[2] for b in boxes),max(b[1]+b[3] for b in boxes)
        representatives = [rows[i] for i in sorted(set([0,len(rows)//2,len(rows)-1]))]
        summaries.append(dict(id=f'G{index:04}',text_sha256=key,
                              kinds=sorted({kind for row in rows for kind in row['kinds']}),
                              observations=len(rows),first_sample=min(r['sample_time'] for r in rows),
                              last_sample=max(r['sample_time'] for r in rows),
                              observed_union_box=[x,y,right-x,bottom-y],
                              representative_candidates=[r['id'] for r in representatives],
                              representative_frames=[r['frame'] for r in representatives]))
    return dict(source_sha256=report['source_sha256'],sampled_frames=report['sampled_frames'],
                interval_seconds=report['interval_seconds'],total_observations=len(report['candidates']),groups=summaries,
                interpretation='Grouped OCR observations, not continuous exposure intervals or verified mask bounds')


def mask_proposals(report):
    """Stationary observation runs only; timing between samples still needs review."""
    result = []
    interval = report['interval_seconds']
    for key in sorted({c['text_sha256'] for c in report['candidates']}):
        runs = []
        for row in sorted((c for c in report['candidates'] if c['text_sha256']==key),key=lambda c:c['sample_time']):
            x,y,w,h = row['box']
            start,end = max(0,row['sample_time']-interval*.6),min(report['duration'],row['sample_time']+interval*.6)
            if runs and start<=runs[-1]['source_end'] and max(abs(a-b) for a,b in zip(runs[-1]['box'],row['box']))<=8:
                run = runs[-1]
                a,b,c,d = run['box']
                left,top = min(a,x),min(b,y)
                run['box']=[left,top,max(a+c,x+w)-left,max(b+d,y+h)-top]
                run['source_end']=end
            else:
                runs.append(dict(source_start=start,source_end=end,box=row['box'],style='solid',reviewed=False,
                                 privacy_group_sha256=key,reason='Unapproved stationary-run mask proposal; review exposure times, bounds and context'))
        result += runs
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--interval',type=float,default=1,help='Seconds between sampled frames; not continuous coverage')
    p.add_argument('--terms',type=Path,help='Private JSON list of literal names, identifiers or strings to flag')
    p.add_argument('--pii-model',type=Path,required=True,help='Pinned local Gravitee model directory, including model-lock.json')
    args = p.parse_args()
    if not .1<=args.interval<=30:
        p.error('Interval must be .1–30 seconds')
    source = args.source.resolve(strict=True)
    terms = json.loads(args.terms.read_text()) if args.terms else []
    if not isinstance(terms,list) or any(not isinstance(t,str) or not t.strip() for t in terms):
        raise ValueError('Terms must be a JSON list of nonempty literal strings')
    metadata = probe(source)
    video = next(s for s in metadata['streams'] if s['codec_type']=='video')
    duration = float(video.get('duration',metadata['format']['duration']))
    times = sorted(set([round(float(t),6) for t in np.arange(0,duration,args.interval)]
                       + [round(max(0,duration-1/float(Fraction(video['r_frame_rate']))),6)]))
    job = Job(args.work,dict(phase='sensitive-scan',source=str(source),source_sha256=digest(source),
                            interval=args.interval,terms_sha256=digest(args.terms) if args.terms else None,
                            pii_model_lock_sha256=digest(args.pii_model/'model-lock.json')))
    images = frames(job,source,times,prefix='privacy')
    binary = vision_binary(job)
    report = job.root/'sensitive-candidates.json'
    summary = job.root/'sensitive-summary.json'
    review_template = job.root/'privacy-review-template.json'
    mask_draft = job.root/'mask-draft.json'
    def scan():
        candidates = []
        detector = PiiDetector(args.pii_model)
        for offset in range(0,len(images),8):
            paths = images[offset:offset+8]
            rows = vision_call(binary,paths,job.root/'vision-ocr.log',ocr=True)
            for index,row in enumerate(rows,offset):
                lines = sorted(row['text'],key=lambda r:(r['box'][1],r['box'][0]))
                model_kinds = detector.line_kinds(lines)
                rule_kinds = rule_line_kinds(lines,terms)
                for line,labels,rules in zip(lines,model_kinds,rule_kinds):
                    kinds = sorted(set(rules+labels))
                    if not kinds:
                        continue
                    x,y,w,h = line['box']
                    left,top = max(0,x-4),max(0,y-4)
                    box = [left,top,min(video['width'],x+w+4)-left,min(video['height'],y+h+4)-top]
                    candidates.append(dict(id=f'R{len(candidates):05}',sample_time=times[index],box=box,
                                           kinds=kinds,ocr_confidence=line['confidence'],frame=str(images[index]),
                                           text_sha256=hashlib.sha256(line['text'].encode()).hexdigest(),
                                           status='review_required_no_mask_applied'))
        result = dict(source_sha256=digest(source),duration=duration,sampled_frames=len(images),
                         interval_seconds=args.interval,candidates=candidates,
                         pii_model=detector.metadata,
                         raw_ocr_saved=False,processing='local Apple Vision revision 3, accurate, en-US, no language correction',
                         limitations=['Sampled frames can miss brief exposures or moving text',
                                      'Rules and trained PII model do not establish sensitivity or detect every secret or business context',
                                      'No audio redaction; spoken sensitive content needs separate review',
                                      'No detection is not a sanitization guarantee'])
        save(report,result)
        save(summary,privacy_summary(result))
        save(review_template,dict(source_sha256=result['source_sha256'],report_sha256=digest(report),
                                 context_reviewed=False,context_note='',groups=[dict(text_sha256=key,action='review',reason='')
                                 for key in sorted({c['text_sha256'] for c in result['candidates']})]))
        save(mask_draft,mask_proposals(result))
    job.stage('sensitive-scan',[report,summary,review_template,mask_draft],scan)
    result = json.loads(report.read_text())
    print(json.dumps(dict(summary=str(summary),report=str(report),sampled_frames=len(images),candidates=len(result['candidates']),
                          local_only=True,raw_ocr_saved=False,mask_applied=False)))


if __name__=='__main__':
    main()
