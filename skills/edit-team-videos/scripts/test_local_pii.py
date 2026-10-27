#!/usr/bin/env python3
"""Opt-in inference regression on synthetic text, using existing local model assets."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
from detect_pii import PiiDetector


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    args=parser.parse_args()
    model=PiiDetector(args.model)
    examples=[
        ('Contact John Smith at john@example.com or +1 415 555 0123.',{'PERSON','EMAIL_ADDRESS','PHONE_NUMBER'}),
        ('My password is T3stOnly!NoRealSecret. My account number is 1234567890.',{'PASSWORD','US_BANK_NUMBER'}),
        ('Open the settings panel and select the blue button.',set())]
    for text,expected in examples:
        actual={s['label'] for s in model.spans(text)}
        if not expected.issubset(actual) or not expected and actual:
            raise AssertionError(f'Synthetic PII category regression: expected {expected}, got {actual}')
    long_text='Open settings and select the blue button. '*160+'Contact John Smith at john@example.com.'
    tail=long_text.index('Contact John')
    spans=model.spans(long_text)
    if not any(s['start']>=tail and s['label']=='EMAIL_ADDRESS' for s in spans):
        raise AssertionError('PII in an overflow token window was missed')
    second=PiiDetector(args.model)
    if model.spans(examples[0][0])!=second.spans(examples[0][0]):
        raise AssertionError('Repeated local inference changed under the same configuration')
    print(json.dumps(dict(synthetic_category_checks='passed',negative_control='passed',
                          token_overflow='passed',repeatability='passed',model=model.metadata)))


if __name__=='__main__':
    main()
