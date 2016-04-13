#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.WARN)

import os
import sys
import json
import requests
import shlex
from subprocess import Popen, PIPE
import boto3
import urllib
import hashlib
import traceback

BASEDIR    = os.path.abspath(os.path.dirname(__file__))
BUCKET     = 'ithaka-labs'
TMP_DIR    = '/tmp'

s3 = boto3.client('s3')

def lambda_handler(event, context):
    logger.info("Received event: %s" % json.dumps(event, indent=2))
    metadata = {}

    try:
        # Get the s3 object data from the event
        s3_data = event['Records'][0]['s3']
        bucket = s3_data['bucket']['name']
        key = urllib.unquote_plus(s3_data['object']['key']).decode('utf8')

        # Download file from S3
        job = json.loads(s3.get_object(Bucket=bucket, Key=key)['Body'].read())
        pdf_url = job['url']
        uid = job['uid']
        device_profile = job.get('profile','default')

        base_dir = os.path.join(TMP_DIR,uid)
        pdf_path = os.path.join(base_dir,'%s.pdf'%uid)
        logger.info('base_dir=%s pdf_url=%s uid=%s device_profile=%s'%(base_dir,pdf_url,uid,device_profile))
        if not os.path.exists(base_dir): os.makedirs(base_dir)

        # Download PDF and write to local file for use by converter
        resp = requests.get(pdf_url)
        if resp.status_code == 200:
            pdf = resp.content
            with open(pdf_path,'wb') as pdf_fp:
                pdf_fp.write(pdf)

        # convert pdf
        execute_external_cmd('%s/convert.py -sc -p %s %s'%(BASEDIR, device_profile, pdf_path))

        # clean up
        logger.debug('Cleaning up...')
        s3.delete_object(Bucket=BUCKET, Key=key)

    except Exception as e:
        logger.error(traceback.format_exc())
        raise e

def execute_external_cmd(cmd):
    """
    Execute the external command and get its exitcode, stdout and stderr.
    """
    logger.debug(cmd)
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err

def simulate_s3_put_trigger(url, device_profile='default', doc_profile='default', refresh=False):
    '''Simulates S3 lambda trigger for local testing.'''
    uid = hashlib.md5(url).hexdigest()
    job = {'url': url,
           'uid': uid,
           'device_profile': device_profile,
           'doc_profile': doc_profile,
           'refresh': refresh,
           'status': 'queued'
           }
    key = 'reflowit/test/%s.json' % uid
    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(job), ContentType='application/json')
    return(lambda_handler({"Records":[{"s3": {"object":{"key":key}, "bucket": {"name":BUCKET} }}]},None))

if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    device_profile = 'default'
    json.dumps(simulate_s3_put_trigger(sys.argv[1]),sort_keys=True,indent=2)
