#!/usr/bin/env python3
"""Regression checks: plan safety, matte geometry, caching, and actual FFmpeg output."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

import numpy as np

sys.dont_write_bytecode = True
from review_packet import cut_risks, privacy_groups, preview_windows, validate_transcript
from plan_edit import snap
from render_edit import camera_for_zoom, rounded_mask
from scan_sensitive import classify, privacy_summary, mask_proposals, rule_line_kinds
from video_workflow import Job, layout_candidates, layout_change_hints
from quality_checks import audit_source_fillers, audit_residuals, audit_privacy, draft_decisions, source_parts

SCRIPTS = Path(__file__).resolve().parent


def png_pixels(path):
    data = path.read_bytes()
    width,height = struct.unpack('>II',data[16:24])
    position,compressed = 8,b''
    while position<len(data):
        size = struct.unpack('>I',data[position:position+4])[0]
        if data[position+4:position+8]==b'IDAT':
            compressed += data[position+8:position+8+size]
        position += 12+size
    return np.frombuffer(zlib.decompress(compressed),dtype=np.uint8).reshape(height,width+1)[:,1:]


class WorkflowTests(unittest.TestCase):
    def test_soft_speech_inside_quiet_cut_requires_review(self):
        rows = [dict(start=0,end=4,text='track it',words=[dict(start=1.8,end=2.2,word='track'),dict(start=2.2,end=2.4,word='it')])]
        risk = cut_risks([dict(start=1.9,end=2.3,kind='pause')],rows,30)
        self.assertEqual(len(risk['risks']),1)
        self.assertEqual([w['word'] for w in risk['risks'][0]['boundary_words']],['track','it'])
        self.assertFalse(cut_risks([],[],30)['word_timestamps_available'])
        self.assertEqual(cut_risks([dict(start=2.5,end=3,kind='pause')],rows,30)['risks'],[])
        # Final snapped frame boundaries, rather than proposed times, drive warnings.
        self.assertEqual(len(cut_risks([dict(start=2.5,end=3,start_frame=60,end_frame=90)],rows,30)['risks']),1)

    def test_word_import_rejects_invalid_times(self):
        for start,end in [(float('nan'),1),(-1,1),(2,1),(True,1)]:
            with self.assertRaises(ValueError):
                validate_transcript([dict(start=0,end=3,text='test',words=[dict(start=start,end=end,word='test')])])
        self.assertEqual(validate_transcript([dict(start=0,end=1,text='test',words=[dict(start=.9,end=1.2,word='test')])])[0]['words'][0]['end'],1.2)
        with self.assertRaises(ValueError):
            validate_transcript([dict(start=0,end=1,text='test',words=[dict(start=0,end=1)])])

    def test_preview_packet_maps_cut_mask_and_zoom_times(self):
        plan = dict(keep_frame_ranges=[[0,300],[450,900]],
                    redactions=[dict(source_start=20,source_end=21)],
                    zooms=[dict(source_start=20,source_end=24)])
        rows = preview_windows(plan,30,780)
        self.assertTrue(any(w['start']<=10<=w['end'] and 'splice' in w['reasons'] for w in rows))
        self.assertTrue(any(w['start']<=15<=w['end'] and 'zoom entry' in w['reasons'] for w in rows))
        self.assertTrue(all(0<=w['start_frame']<w['end_frame']<=780 for w in rows))

    def test_privacy_delta_orders_new_and_moved_before_matches(self):
        prior = dict(candidates=[dict(text_sha256='seen',box=[1,2,3,4]),dict(text_sha256='moved',box=[1,2,3,4])])
        current = dict(candidates=[dict(text_sha256='seen',box=[1,2,3,4]),dict(text_sha256='moved',box=[2,2,3,4]),dict(text_sha256='new',box=[1,2,3,4])])
        self.assertEqual([g['text_sha256'] for g in privacy_groups(current,prior)],['new','moved','seen'])

    def test_shared_privacy_mask_keeps_each_group_coverage_gate(self):
        report = dict(source_sha256='source',pii_model={'id':'fixture'},candidates=[
            dict(text_sha256=k,sample_time=1,box=box) for k,box in [('one',[10,10,20,10]),('two',[35,10,10,10])]])
        decisions = dict(source_sha256='source',report_sha256='scan',context_reviewed=True,
                         context_note='Reviewed synthetic source regions and narration',
                         groups=[dict(text_sha256=k,action='mask',reason='Synthetic secret inside a shared sidebar') for k in ('one','two')])
        plan = dict(fps_for_audit=30,keep_frame_ranges=[[0,90]],redactions=[
            dict(privacy_group_sha256s=['one','two'],source_start=0,source_end=2,box=[8,8,40,14],reviewed=True)])
        self.assertEqual(audit_privacy(report,decisions,'source','scan',plan)['status'],'passed')
        plan['redactions'][0]['privacy_group_sha256s']='one'
        with self.assertRaisesRegex(ValueError,'unique list'):
            audit_privacy(report,decisions,'source','scan',plan)
        plan['redactions'][0]['privacy_group_sha256s']=['one','two']
        plan['redactions'][0]['box']=[8,8,24,14]
        with self.assertRaisesRegex(ValueError,'outside'):
            audit_privacy(report,decisions,'source','scan',plan)

    def test_trial_failure_cannot_silently_leave_unreviewed_fillers(self):
        candidates = [dict(id=f'F{i:04}',start=i*2,end=i*2+.5) for i in range(111)]
        decisions = dict(accept_filler_ids=[f'F{i:04}' for i in range(17)])
        with self.assertRaisesRegex(ValueError,'Unresolved source fillers'):
            audit_source_fillers(candidates,decisions,[])

    def test_export_with_95_unreviewed_candidates_is_not_ready(self):
        result = audit_residuals([{}]*95,None,'video','scan')
        self.assertEqual(result['status'],'review_required')
        self.assertEqual(result['unresolved'],95)

    def test_retained_false_positive_needs_actual_words_and_matching_export(self):
        review = dict(video_sha256='video',scan_sha256='scan',retain_fillers=[
            dict(id='R0000',classification='false_positive',spoken_words='another',reason='Lexical word, complete sentence retains its meaning')])
        self.assertEqual(audit_residuals([{}],review,'video','scan')['status'],'passed')
        with self.assertRaises(ValueError):audit_residuals([{}],review,'different export','scan')
        review['retain_fillers'][0]['spoken_words']=''
        with self.assertRaises(ValueError):audit_residuals([{}],review,'video','scan')

    def test_source_manual_cut_can_resolve_filler_without_duplicate_id_cut(self):
        rows = [dict(id='F0000',start=1,end=2)]
        self.assertEqual(audit_source_fillers(rows,{},[[.9,2.1]])['unresolved'],0)
        decisions = dict(cuts=[dict(candidate_id='F0000',kind='filler',start=1.2,end=1.6)])
        self.assertEqual(audit_source_fillers(rows,decisions,[[1.2,1.6]])['unresolved'],0)

    def test_draft_targets_acoustic_ums_without_asr_overlap_veto(self):
        review = dict(source_sha256='source',duration=40,pause_candidates=[dict(id='P0000',start=4,end=8)],
                      filler_candidates=[dict(id='F0000',type='um'),dict(id='F0001',type='other')])
        draft = draft_decisions(review)
        self.assertFalse(draft['editorial_reviewed'])
        self.assertEqual(draft['accept_filler_ids'],['F0000'])
        self.assertEqual(draft['cuts'][0]['start'],4.2)

    def test_no_privacy_scan_or_legacy_regex_only_is_not_a_pass(self):
        self.assertEqual(audit_privacy(None,None,'source','scan',{})['status'],'scan_required')
        self.assertEqual(audit_privacy(dict(source_sha256='source',candidates=[]),None,'source','scan',{})['status'],'trained_pii_scan_required')

    def test_privacy_mask_must_cover_retained_observation(self):
        report = dict(source_sha256='source',pii_model={'id':'fixture'},candidates=[dict(text_sha256='secret-hash',sample_time=1,box=[10,10,20,10])])
        decisions = dict(source_sha256='source',report_sha256='scan',context_reviewed=True,
                         context_note='Synthetic contextual review; no actual business data',
                         groups=[dict(text_sha256='secret-hash',action='mask',reason='Synthetic credential masking check')])
        plan = dict(fps_for_audit=30,keep_frame_ranges=[[0,90]],redactions=[])
        with self.assertRaises(ValueError):audit_privacy(report,decisions,'source','scan',plan)
        plan['redactions']=[dict(privacy_group_sha256='secret-hash',source_start=0,source_end=2,box=[8,8,24,14],reviewed=True)]
        self.assertEqual(audit_privacy(report,decisions,'source','scan',plan)['status'],'passed')

    def test_residual_times_map_across_splice_to_original_source(self):
        self.assertEqual(source_parts(.9,1.1,[[0,30],[60,90]],30),[[.9,1.0],[2.0,2.1]])

    def test_camera_must_be_reviewed_and_cover_zoom(self):
        zoom = dict(source_start=1,source_end=3)
        for mode in ('unknown','moving','multiple','full_camera'):
            camera = dict(source_start=0,source_end=4,mode=mode,reviewed=True,evidence_frames=['S0000'])
            with self.assertRaises(ValueError):
                camera_for_zoom(dict(camera_layouts=[camera]),zoom,640,360)
        absent = dict(source_start=0,source_end=4,mode='absent',reviewed=True,evidence_frames=['S0000'])
        self.assertIsNone(camera_for_zoom(dict(camera_layouts=[absent]),zoom,640,360))
        with self.assertRaises(ValueError):
            camera_for_zoom({},zoom,640,360)
        with self.assertRaises(ValueError):
            camera_for_zoom(dict(camera_layouts=[absent,absent]),zoom,640,360)

    def test_size_position_shape_are_input_specific(self):
        for crop,shape,radius in [([20,20,80,60],'rounded_rectangle',12),
                                  ([490,230,100,100],'ellipse',0),([200,30,200,120],'rectangle',0)]:
            camera = dict(source_start=0,source_end=4,mode='overlay',reviewed=True,
                          evidence_frames=['S0000'],crop=crop,shape=shape,radius=radius)
            actual = camera_for_zoom(dict(camera_layouts=[camera]),dict(source_start=1,source_end=3),640,360)
            self.assertEqual(actual['crop'],crop)
            self.assertEqual(actual['shape'],shape)

    def test_alpha_matches_shape(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'mask.png'
            for shape,radius,corner in [('ellipse',0,0),('rounded_rectangle',12,0),('rectangle',0,255)]:
                rounded_mask(path,80,60,radius,shape)
                pixels = png_pixels(path)
                self.assertEqual(pixels[0,0],corner)
                self.assertEqual(pixels[30,40],255)

    def test_face_proposal_does_not_assert_webcam(self):
        row = dict(width=640,height=360,faces=[dict(box=[510,250,30,40],confidence=.9)],
                   rectangles=[dict(box=[490,230,90,100],confidence=1)])
        proposal = layout_candidates(row)[0]
        self.assertEqual(proposal['panel_candidates'],[[490,230,90,100]])
        self.assertEqual(proposal['shape'],'unverified')
        self.assertEqual(layout_candidates(dict(width=640,height=360,faces=[],rectangles=[])),[])

    def test_sensitive_patterns_and_literals(self):
        self.assertIn('email',classify('demo.person@example.com',[]))
        self.assertIn('credential_like',classify('ghp_'+'A'*30,[]))
        self.assertIn('jwt_like',classify('eyJ'+'A'*20+'.'+'B'*20+'.'+'C'*20,[]))
        self.assertIn('configured_literal',classify('Client sample project',['SAMPLE']))
        self.assertNotIn('ipv4_review_context',classify('999.999.999.999',[]))
        self.assertEqual(classify('ordinary walkthrough text',[]),[])
        self.assertIn('payment_card_luhn',classify('4111 1111 1111 1111',[]))
        self.assertIn('bearer_credential',classify('Authorization: Bearer TestOnlyNotARealCredential',[]))
        self.assertIn('business_context_review',classify('Customer incident details and roadmap',[]))
        self.assertIn('credential_connection_url',classify('postgres://demo:test-only@example.invalid/database',[]))

    def test_mask_proposals_merge_stationary_samples_but_require_review(self):
        row = dict(text_sha256='hash',box=[10,20,100,20])
        report = dict(duration=10,interval_seconds=1,candidates=[dict(row,sample_time=1),dict(row,sample_time=2)])
        masks = mask_proposals(report)
        self.assertEqual(len(masks),1)
        self.assertFalse(masks[0]['reviewed'])
        self.assertEqual(masks[0]['style'],'solid')

    def test_secret_blocks_and_split_labels_include_the_value(self):
        rows=[dict(text=t) for t in ['-----BEGIN PRIVATE KEY-----','SyntheticPrivateKeyBodyOnly','-----END PRIVATE KEY-----','ordinary UI','API key:','SyntheticValueOnly']]
        flags=rule_line_kinds(rows,[])
        self.assertIn('private_key_block',flags[1])
        self.assertNotIn('private_key_block',flags[3])
        self.assertIn('sensitive_value_after_label',flags[5])

    def test_camera_change_hints_flag_movement_scale_and_absence(self):
        def row(box):
            return dict(width=640,height=360,faces=[dict(box=box)] if box else [])
        hints = layout_change_hints([row([20,20,40,40]),row([500,240,80,80]),row(None)],[0,1,2])
        self.assertIn('face_position_changed',hints[0]['reasons'])
        self.assertIn('face_scale_changed',hints[0]['reasons'])
        self.assertIn('detected_face_count_changed',hints[1]['reasons'])

    def test_privacy_summary_deduplicates_without_inventing_mask_intervals(self):
        row = dict(text_sha256='example hash',kinds=['email'],box=[10,20,100,20],frame='private frame')
        report = dict(source_sha256='source',sampled_frames=3,interval_seconds=1,
                      candidates=[dict(row,id='R00000',sample_time=0),dict(row,id='R00001',sample_time=2)])
        group = privacy_summary(report)['groups'][0]
        self.assertEqual(group['observations'],2)
        self.assertEqual(group['observed_union_box'],row['box'])
        self.assertNotIn('source_start',group)

    def test_boundary_snap_brackets_event(self):
        samples = np.zeros(16000)
        samples[7600:8400] = .2
        a = snap(.475,samples,16000,60,'start',.5)
        b = snap(.525,samples,16000,60,'end',.5)
        self.assertLess(a/60,.5)
        self.assertGreater(b/60,.5)

    def test_changed_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            job = Job(Path(root),dict(test=True))
            path = job.root/'evidence.txt'
            job.stage('test',[path],lambda:path.write_text('original'))
            job.stage('test',[path],lambda:self.fail('Verified cache should be reused'))
            path.write_text('changed')
            with self.assertRaises(ValueError):
                job.stage('test',[path],lambda:None)

    def test_fractional_fps_changed_camera_and_source_redaction(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source,output = root/'source.mp4',root/'edited.mp4'
            subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',
                            'color=blue:s=320x240:r=30000/1001:d=3','-f','lavfi','-i',
                            'sine=frequency=400:sample_rate=48000:duration=3','-c:v','libx264',
                            '-pix_fmt','yuv420p','-c:a','aac','-shortest',str(source)],check=True)
            camera = dict(mode='overlay',reviewed=True,evidence_frames=['synthetic fixture'])
            plan = dict(source=str(source),keep_frame_ranges=[[0,13],[19,37],[43,89]],
                        postroll_seconds=.3,fade_out_seconds=.1,
                        camera_layouts=[dict(camera,source_start=0,source_end=1.4,crop=[23,25,81,61],shape='rounded_rectangle',radius=12),
                                        dict(camera,source_start=1.4,source_end=3,crop=[201,151,61,71],shape='ellipse')],
                        zooms=[dict(source_start=.3,source_end=1.2,scale=1.2,ease_seconds=.1),
                               dict(source_start=1.6,source_end=2.7,scale=1.3,ease_seconds=.1)],
                        redactions=[dict(source_start=0,source_end=.2,box=[80,80,40,30],reviewed=True,reason='Synthetic redaction regression')])
            plan_path = root/'plan.json'
            plan_path.write_text(json.dumps(plan))
            result = subprocess.run([sys.executable,str(SCRIPTS/'render_edit.py'),'--plan',str(plan_path),
                                     '--work',str(root/'render'),'--output',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            evidence = json.loads((root/'render/validation.json').read_text())
            self.assertEqual(evidence['video_frames'],86)
            self.assertEqual(evidence['camera_masks'],2)
            self.assertEqual(evidence['full_decode'],'passed')
            preview = root/'preview.mp4'
            result = subprocess.run([sys.executable,str(SCRIPTS/'render_edit.py'),'--plan',str(plan_path),
                                     '--work',str(root/'preview-render'),'--output',str(preview),
                                     '--preview-start',str(12*1001/30000),'--preview-end',str(62*1001/30000)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            validation = json.loads((root/'preview-render/validation.json').read_text())
            self.assertEqual(validation['video_frames'],50)
            self.assertFalse(validation['delivery_candidate'])
            def decoded(path,filters):
                raw = subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(path),'-vf',filters,
                                               '-f','rawvideo','-pix_fmt','rgb24','-'])
                return np.frombuffer(raw,dtype=np.uint8).astype(float)
            full_pixels = decoded(output,'trim=start_frame=12:end_frame=62,setpts=PTS-STARTPTS')
            preview_pixels = decoded(preview,'null')
            self.assertEqual(full_pixels.shape,preview_pixels.shape)
            self.assertLess(np.abs(full_pixels-preview_pixels).mean(),3)

            pixels = subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(output),
                                              '-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
            image = np.frombuffer(pixels,dtype=np.uint8).reshape(240,320,3)
            self.assertLess(image[90,90].max(),10)
            self.assertGreater(image[120,120,2],200)

    def test_screen_only_zoom_blur_and_hold_do_not_expand_eof_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source.mp4'
            subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',
                            'testsrc2=s=320x240:r=30000/1001:d=3','-f','lavfi','-i',
                            'sine=sample_rate=48000:duration=3','-c:v','libx264','-c:a','aac',
                            '-shortest',str(source)],check=True)
            plan = dict(source=str(source),keep_frame_ranges=[[0,15],[21,89]],
                        camera_layouts=[dict(source_start=0,source_end=3,mode='absent',reviewed=True,evidence_frames=['fixture'])],
                        zooms=[dict(source_start=.3,source_end=2.7,scale=1.2)],
                        redactions=[dict(source_start=.1,source_end=.3,box=[71,71,41,31],style='blur',reviewed=True,reason='Timing regression')],
                        postroll_seconds=.3,fade_out_seconds=.1)
            path = root/'plan.json'
            path.write_text(json.dumps(plan))
            result = subprocess.run([sys.executable,str(SCRIPTS/'render_edit.py'),'--plan',str(path),
                                     '--work',str(root/'render'),'--output',str(root/'out.mp4')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            validation = json.loads((root/'render/validation.json').read_text())
            self.assertEqual(validation['video_frames'],92)
            self.assertLess(validation['duration_seconds'],3.1)


if __name__=='__main__':
    unittest.main(verbosity=2)
