"""Editorial completion checks; technical decode success cannot waive these."""


def union_overlap(start, end, cuts):
    cursor,total = start,0.
    for a,b in sorted(cuts):
        left,right = max(cursor,start,a),min(end,b)
        if right>left:
            total += right-left
            cursor = right
    return total


def retentions(rows, known_ids):
    if not isinstance(rows,list):
        raise ValueError('Retained filler decisions must be a list')
    result = {}
    for row in rows:
        if (not isinstance(row,dict) or row.get('id') not in known_ids or row['id'] in result
                or row.get('classification') not in ('false_positive','meaningful_vocalization')
                or not isinstance(row.get('spoken_words'),str) or not row['spoken_words'].strip()
                or not isinstance(row.get('reason'),str) or len(row['reason'].strip())<12):
            raise ValueError('Every retained candidate needs a unique valid ID, specific classification, actual spoken words and reason')
        result[row['id']] = row
    return result


def audit_source_fillers(candidates, decisions, cuts):
    known = {row['id'] for row in candidates}
    approved = decisions.get('accept_filler_ids',[])
    if not isinstance(approved,list) or any(not isinstance(i,str) for i in approved) or len(set(approved))!=len(approved) or set(approved)-known:
        raise ValueError('Accepted filler IDs must be unique IDs from this review packet')
    retained = retentions(decisions.get('retain_fillers',[]),known)
    manual = {}
    by_id = {row['id']:row for row in candidates}
    for cut in decisions.get('cuts',[]):
        key = cut.get('candidate_id')
        if key is None:
            continue
        if (key not in known or key in manual or cut.get('kind')!='filler'
                or max(cut['start'],by_id[key]['start'])>=min(cut['end'],by_id[key]['end'])):
            raise ValueError('Manual filler decisions need a unique known candidate_id and an overlapping filler cut')
        manual[key]=cut
    if set(approved)&set(retained) or set(manual)&(set(approved)|set(retained)):
        raise ValueError('A candidate cannot be both removed and retained')
    unresolved = []
    for row in candidates:
        duration = row['end']-row['start']
        covered = duration>0 and union_overlap(row['start'],row['end'],cuts)>=duration*.9-1e-8
        if row['id'] not in approved and row['id'] not in retained and row['id'] not in manual and not covered:
            unresolved.append(row['id'])
    if unresolved:
        raise ValueError(f'Unresolved source fillers ({len(unresolved)}): '+','.join(unresolved)+'. Review every candidate; omitted IDs are not an implicit keep decision.')
    return dict(candidates=len(candidates),retained=len(retained),unresolved=0)


def source_parts(start, end, keep, fps):
    elapsed,parts = 0.,[]
    for a,b in keep:
        duration = (b-a)/fps
        left,right = max(start,elapsed),min(end,elapsed+duration)
        if right>left:
            parts.append([round(a/fps+left-elapsed,6),round(a/fps+right-elapsed,6)])
        elapsed += duration
    return parts


def audit_residuals(events, decisions, video_sha256, scan_sha256):
    ids = {f'R{i:04}' for i in range(len(events))}
    if not events:
        return dict(status='passed',unresolved=0,retained=0)
    if decisions is None:
        return dict(status='review_required',unresolved=len(events),retained=0)
    if decisions.get('video_sha256')!=video_sha256 or decisions.get('scan_sha256')!=scan_sha256:
        raise ValueError('Residual reviews must match this exact export and acoustic scan')
    retained = retentions(decisions.get('retain_fillers',[]),ids)
    return dict(status='passed' if set(retained)==ids else 'review_required',
                unresolved=len(ids-set(retained)),retained=len(retained))


def audit_privacy(report, decisions, source_sha256, report_sha256, plan):
    if report is None:
        return dict(status='scan_required',unresolved=None)
    if report.get('source_sha256')!=source_sha256:
        raise ValueError('Privacy scan belongs to a different source recording')
    if not report.get('pii_model'):
        return dict(status='trained_pii_scan_required',unresolved=None)
    for mask in plan.get('redactions',[]):
        links = mask.get('privacy_group_sha256s',[])
        if (not isinstance(links,list) or any(not isinstance(key,str) or not key for key in links)
                or len(links)!=len(set(links))):
            raise ValueError('Shared privacy mask hashes must be a unique list of nonempty strings')
    ids = {row['text_sha256'] for row in report['candidates']}
    if decisions is None:
        return dict(status='review_required',unresolved=len(ids))
    if (decisions.get('source_sha256')!=source_sha256 or decisions.get('report_sha256')!=report_sha256
            or decisions.get('context_reviewed') is not True
            or not isinstance(decisions.get('context_note'),str) or len(decisions['context_note'].strip())<12):
        raise ValueError('Privacy decisions require matching source/report hashes and an actual contextual review note')
    groups = decisions.get('groups',[])
    if not isinstance(groups,list):
        raise ValueError('Privacy groups must be a list')
    reviewed = set()
    for row in groups:
        key = row.get('text_sha256')
        if key not in ids or key in reviewed or row.get('action') not in ('keep','mask') or len(str(row.get('reason','')).strip())<12:
            raise ValueError('Each privacy group needs a unique scanned hash, keep/mask action and specific reason')
        reviewed.add(key)
        if row['action']=='mask':
            masks = [m for m in plan.get('redactions',[]) if (m.get('privacy_group_sha256')==key or key in m.get('privacy_group_sha256s',[])) and m.get('reviewed') is True]
            if not masks:
                raise ValueError('A masked privacy group requires corresponding reviewed plan redactions')
            for candidate in (c for c in report['candidates'] if c['text_sha256']==key):
                # An observation deleted by a content cut cannot leak into the export.
                t = candidate['sample_time']
                if not any(a/plan['fps_for_audit']<=t<b/plan['fps_for_audit'] for a,b in plan['keep_frame_ranges']):
                    continue
                x,y,w,h = candidate['box']
                if not any(m['source_start']<=t<m['source_end']
                           and m['box'][0]<=x and m['box'][1]<=y
                           and m['box'][0]+m['box'][2]>=x+w and m['box'][1]+m['box'][3]>=y+h for m in masks):
                    raise ValueError('A masked privacy observation remains outside the reviewed mask; check times, motion and bounds')
    return dict(status='passed' if reviewed==ids else 'review_required',unresolved=len(ids-reviewed))


def draft_decisions(review):
    source = review['duration']
    pauses = []
    for row in review['pause_candidates']:
        if row['end']-row['start']>1.2 and row['start']>.5 and row['end']<source-15:
            pauses.append(dict(start=round(row['start']+.2,3),end=round(row['end']-.3,3),
                               kind='pause',snap=False,reason=f'Review proposed idle-pause shortening {row["id"]}; retain 0.5s room'))
    return dict(source_sha256=review['source_sha256'],editorial_reviewed=False,
                accept_filler_ids=[r['id'] for r in review['filler_candidates'] if r['type'] in ('um','uh')],
                retain_fillers=[],cuts=pauses,camera_layouts=[],zooms=[],redactions=[],
                postroll_seconds=1.2,fade_out_seconds=.45,
                review_note='Unapproved draft: review complete filler spans, neighboring words, pauses, causal order and visual context before setting editorial_reviewed')
