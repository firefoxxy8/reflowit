#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
import boto3
import hashlib
import traceback
import requests

BUCKET         = 'ithaka-labs'
BASE_PREFIX    = 'reflowit/inqueue'

s3 = boto3.client('s3')

def upload(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        pdf = resp.content
        key = '%s/%s.pdf'%(BASE_PREFIX,hashlib.md5(url).hexdigest())
        s3.put_object(Bucket=BUCKET, Key=key, Body=pdf, ContentType='application/pdf')
    else:
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    upload(sys.argv[1])
