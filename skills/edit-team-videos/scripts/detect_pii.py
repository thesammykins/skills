"""Local pinned Gravitee BERT-small ONNX PII inference; no downloads or text logs."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

os.environ['TOKENIZERS_PARALLELISM']='false'
ort.disable_telemetry_events()


class PiiDetector:
    def __init__(self, directory, threshold=.5):
        directory = Path(directory)
        lock = json.loads((directory/'model-lock.json').read_text())
        if lock.get('repo')!='gravitee-io/bert-small-pii-detection' or lock.get('license')!='apache-2.0':
            raise ValueError('Unsupported PII model profile; validate new model layout and license first')
        for name,expected in lock['files'].items():
            path = directory/name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError(f'Pinned PII model asset changed: {name}')
        if not 0<threshold<1:
            raise ValueError('PII threshold must be between 0 and 1')
        self.threshold = threshold
        self.labels = json.loads((directory/'config.json').read_text())['id2label']
        self.tokenizer = Tokenizer.from_file(str(directory/'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=512,stride=64)
        options = ort.SessionOptions()
        options.intra_op_num_threads=4
        options.inter_op_num_threads=1
        options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(str(directory/'model.quant.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        self.metadata = dict(repo=lock['repo'],revision=lock['revision'],license=lock['license'],
                             model_sha256=lock['files']['model.quant.onnx'],threshold=threshold,
                             device='cpu',maximum_tokens=512,overlap_tokens=64)
        self.cache = {}

    def spans(self, text):
        key = hashlib.sha256(text.encode()).hexdigest()
        if key in self.cache:
            return self.cache[key]
        encoding = self.tokenizer.encode(text)
        found = {}
        for chunk in [encoding,*encoding.overflowing]:
            values = dict(input_ids=chunk.ids,attention_mask=chunk.attention_mask,token_type_ids=chunk.type_ids)
            inputs = {item.name:np.asarray([values[item.name]],dtype=np.int64 if item.type=='tensor(int64)' else np.int32)
                      for item in self.session.get_inputs()}
            logits = self.session.run(None,inputs)[0][0].astype(np.float64)
            if logits.ndim!=2 or logits.shape[0]!=len(chunk.ids) or not np.isfinite(logits).all():
                raise ValueError('Unexpected PII model output layout')
            probability = np.exp(logits-logits.max(axis=1,keepdims=True))
            probability /= probability.sum(axis=1,keepdims=True)
            for index,(start,end) in enumerate(chunk.offsets):
                label_index = int(probability[index].argmax())
                label = self.labels[str(label_index)]
                score = float(probability[index,label_index])
                if label=='O' or end<=start or score<self.threshold:
                    continue
                label = label.removeprefix('B-').removeprefix('I-')
                found[(start,end,label)] = dict(start=start,end=end,label=label,confidence=round(score,6))
        result = [found[key] for key in sorted(found)]
        self.cache[key] = result
        return result

    def line_kinds(self, lines):
        """Four nearby OCR lines supply context; returned flags preserve line geometry."""
        kinds = [set() for _ in lines]
        for offset in range(0,len(lines),4):
            block = lines[offset:offset+4]
            text = '\n'.join(row['text'] for row in block)
            spans = self.spans(text)
            cursor = 0
            for local,row in enumerate(block):
                end = cursor+len(row['text'])
                kinds[offset+local].update('pii_'+s['label'].lower() for s in spans if s['start']<end and s['end']>cursor)
                cursor = end+1
        return [sorted(row) for row in kinds]
