#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import os
import sys
import getopt
import json
import shlex
from subprocess import Popen, PIPE
import platform
import traceback
from os import listdir
import mimetypes
import shutil
import boto3

BASEDIR = os.path.abspath(os.path.dirname(__file__))

S3_BUCKET              = 'ithaka-labs'
PREFIX                 = 'reflowit'
VERSION                = 'v1'
DEFAULT_DEVICE_PROFILE = 'default'
TMP_DIR                = '/tmp'

S3_PREFIX              = os.path.join(PREFIX,VERSION)
LOCAL_DATADIR_ROOT     = os.path.join(TMP_DIR,S3_PREFIX)
if not os.path.exists(LOCAL_DATADIR_ROOT): os.makedirs(LOCAL_DATADIR_ROOT)

IS_OSX = platform.system() == 'Darwin'
DEFAULT_IMAGE_TYPE = 'png' # 'png' or 'jpeg'
DEFAULT_DPI        = 300

if IS_OSX:
    k2pdfopt_path = '%s/k2pdfopt_osx' % BASEDIR
    gs_path = '%s/gs-916-osx' % BASEDIR
else: # linux
    k2pdfopt_path = '%s/k2pdfopt_linux' % BASEDIR
    gs_path = '%s/gs-919-linux' % BASEDIR

def convert(original_pdf_path, profile=DEFAULT_DEVICE_PROFILE, sync_with_s3=False, clean=False):
    s3_client = boto3.client('s3') if sync_with_s3 else None
    uid = original_pdf_path.split('/')[-1].split('.')[0]
    logger.info("convert: pdf_path=%s uid=%s profile=%s sync_with_s3=%s" % (original_pdf_path,uid,profile,sync_with_s3))
    metadata = {}

    try:
        # Generate file names and paths
        base_dir = os.path.join(LOCAL_DATADIR_ROOT,uid)
        logger.info(base_dir)
        if not os.path.exists(base_dir): os.makedirs(base_dir)
        original_fname = '%s.pdf'%uid
        mobile_fname = '%s-mobile.pdf'%uid
        mobile_pdf_path = os.path.join(base_dir,mobile_fname)
        images_base_dir = os.path.join(base_dir,'images')

        metadata['original_pdf'] = 'https://s3.amazonaws.com/ithaka-labs/%s/%s/%s' % (S3_PREFIX, uid, original_fname)
        metadata['mobile_pdf'] = 'https://s3.amazonaws.com/ithaka-labs/%s/%s/%s' % (S3_PREFIX, uid, mobile_fname)

        # Load PDF
        with open(original_pdf_path,'rb') as original_pdf_fp:
            original_pdf = original_pdf_fp.read()
            metadata['original_pdf_size'] = len(original_pdf)

        # Create a mobile-optimized version of the PDF
        logger.debug('Generating mobile optimized PDF...')
        convert_pdf(original_pdf_path, mobile_pdf_path)

        if os.path.exists(mobile_pdf_path):
            with open(mobile_pdf_path,'rb') as mobile_pdf_fp:
                mobile_pdf = mobile_pdf_fp.read()
                metadata['mobile_pdf_size'] = len(mobile_pdf)
            # Upload mobile pdf to S3
            if sync_with_s3: upload_to_s3(s3_client,'%s/%s/%s'%(S3_PREFIX,uid,mobile_fname), mobile_pdf, 'application/pdf')

        # Upload original pdf to S3
        if sync_with_s3: upload_to_s3(s3_client,'%s/%s/%s'%(S3_PREFIX,uid,original_fname), original_pdf, 'application/pdf')

        # Extract page images from PDFs and get metadata for each image
        metadata['original_pdf_page_images'] = extract_page_images(original_pdf_path, os.path.join(images_base_dir,'original'),uid, dpi=500)
        metadata['mobile_pdf_page_images'] = extract_page_images(mobile_pdf_path, os.path.join(images_base_dir,'mobile'),uid, dpi=500)

        for image_rec in metadata['original_pdf_page_images'] + metadata['mobile_pdf_page_images']:
            image_path = image_rec['local_path']
            logger.debug(image_path)
            with open(image_path, 'rb') as image_fp:
                image = image_fp.read()
                image_rec['size'] = len(image)
                s3_key = '%s' % (image_path.replace('%s/'%TMP_DIR,''))
                if sync_with_s3: upload_to_s3(s3_client,s3_key, image, image_rec['type'])
                del image_rec['local_path']
                #del image_rec['s3_key']

        json_data_path = os.path.join(base_dir,'%s.json'%uid)
        with open(json_data_path,'wb') as json_data_fp:
            json_data_fp.write(json.dumps(metadata,sort_keys=True))
        if sync_with_s3: upload_to_s3(s3_client,'%s/%s/%s.json'%(S3_PREFIX,uid,uid), json.dumps(metadata,sort_keys=True), 'application/json')

        # clean up
        if clean:
            logger.debug('Cleaning up...')
            shutil.rmtree(base_dir)

        return metadata

    except Exception as e:
        logger.error(traceback.format_exc())
        raise e

def convert_pdf(original_pdf_path, mobile_pdf_path):
    command = '%s -ui- -x -o %s -h 1334 -w 750 -dpi 250 %s' % (k2pdfopt_path, mobile_pdf_path, original_pdf_path)
    execute_external_cmd(command)

def upload_to_s3(s3_client, key, content, content_type):
    response = s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=content, ContentType=content_type, ACL='public-read')
    logger.debug(response)
    return response['ResponseMetadata']['HTTPStatusCode'] == 200

def execute_external_cmd(cmd):
    """
    Execute the external command and get its exitcode, stdout and stderr.
    """
    logger.debug(cmd)
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    #logger.debug(exitcode)
    return exitcode, out, err

def extract_page_images(pdf_path, dest, prefix, start_page=0, dpi=DEFAULT_DPI, image_type=DEFAULT_IMAGE_TYPE):
    '''Extract images from PDF using Ghostscript.'''
    image_metadata = []
    if not os.path.exists(dest): os.makedirs(dest)
    cmd = '%s -dNumRenderingThreads=4 -dNOPAUSE -dFirstPage=%s -sDEVICE=pngalpha -sOutputFile=%s/%s-%%03d.%s -r%s %s -c quit' % (gs_path, start_page+1, dest, prefix, image_type, dpi, pdf_path)
    exitcode, out, err = execute_external_cmd(cmd)
    for fname in listdir(dest):
        image_path = os.path.join(dest,fname)
        page_uri = 'https://s3.amazonaws.com/%s/%s/%s' % (S3_BUCKET,dest.replace('%s/'%TMP_DIR,''), fname)
        page_seq = int(fname.split('-')[-1].split('.')[0])
        page_content_type = mimetypes.guess_type(image_path)[0]
        image_type, width, height = get_image_metadata(image_path)
        image_metadata.append({'local_path':image_path, 'seq':page_seq, 'uri':page_uri, 'type':page_content_type, 'height':height, 'width':width})
    return image_metadata

def get_image_metadata(image_path):
    width = None
    height = None
    if os.path.exists(image_path):
        cmd = '/usr/bin/file %s' % image_path
        exitcode, out, err = execute_external_cmd(cmd)
        out = out.strip()
        rec = out.split()
        image_type = rec[1]
        width = int(rec[4])
        height = int(rec[6][:-1])
        return image_type, width, height

def usage():
	print('%s [hdp:sc] pdf_path' % sys.argv[0])
	print('   -h --help      Print help message')
	print('   -d --debug     Debug output')
	print('   -p --profile   Device profile (%s)'%DEFAULT_DEVICE_PROFILE)
	print('   -s --sync      Sync generated data to S3 bucket')
	print('   -c --clean     Delete generated files')

if __name__ == '__main__':
    kwargs = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hdp:sc', ['help', 'debug', 'profile', 'sync'])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-d', '--debug'):
            kwargs['debug'] = True
        elif o in ('-p', '--profile'):
            kwargs['profile'] = a
        elif o in ('-s', '--sync'):
            kwargs['sync'] = True
        elif o in ('-c', '--clean'):
            kwargs['clean'] = True
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    if kwargs.get('debug',False): logger.setLevel(logging.DEBUG)

    for pdf_path in args:
        logger.info(convert(pdf_path,
                    profile=kwargs.get('profile',DEFAULT_DEVICE_PROFILE),
                    sync_with_s3=kwargs.get('sync',False),
                    clean=kwargs.get('clean',False)))
