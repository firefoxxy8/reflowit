#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import os
import sys
import json
import hashlib
import boto3
import botocore

BUCKET       = 'ithaka-labs'
VERSION      = 'v1'
DATA_PREFIX  = 'reflowit/%s'%VERSION
QUEUE_PREFIX = 'reflowit/inqueue'

s3 = boto3.client('s3')

def object_exists(bucket, key):
    exists = False
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            exists = False
        else:
            raise e
    else:
        exists = True
    return exists

def queue_job(job):
    job['status'] = 'queued'
    key = os.path.join(QUEUE_PREFIX,'%s.json'%job['uid'])
    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(job), ContentType='application/json')

def lambda_handler(event, context):
    url = event.get('query',{}).get('url')
    device_profile = event.get('query',{}).get('device_profile','default')
    doc_profile = event.get('query',{}).get('doc_profile','default')
    refresh = event.get('refresh',{}).get('refresh','false') == 'true'
    uid = hashlib.md5(url).hexdigest()
    metadata = {'url':url,
                'uid':uid,
                'device_profile':device_profile,
                'doc_profile':doc_profile,
                'refresh':refresh
                }
    if refresh:
        queue_job(metadata)
    else:
        try:
            json_data_key = os.path.join(DATA_PREFIX,uid,'%s.json'%uid)
            response = s3.get_object(Bucket=BUCKET, Key=json_data_key)
            metadata = json.loads(response['Body'].read())
            metadata['status'] = 'ready'
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                key = os.path.join(QUEUE_PREFIX,'%s.json'%uid)
                if object_exists(BUCKET, key):
                    metadata['status'] = 'processing'
                else:
                    queue_job(metadata)
            else:
                logger.error(e)
                metadata['status'] = 'error'
                metadata['error_message'] = e.response['Error']
    return metadata
