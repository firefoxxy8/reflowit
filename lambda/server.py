#!/usr/bin/env python

import os, sys, traceback, json
from tornado.ioloop import IOLoop
import tornado.web

import hashlib
import requests
import shlex
from subprocess import Popen, PIPE

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger()

DEFAULT_PORT = 9900
BASEDIR      = os.path.abspath(os.path.dirname(__file__))
VERSION      = 'v1'
DATADIR_ROOT = '/tmp/reflowit'
INQUEUE      = os.path.join(DATADIR_ROOT,'inqueue')
if not os.path.exists(INQUEUE): os.makedirs(INQUEUE)
OUTDIR       = os.path.join(DATADIR_ROOT,VERSION)
if not os.path.exists(OUTDIR): os.makedirs(OUTDIR)

PDFS_DIR     = os.path.join(BASEDIR,'test_pdfs')

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        results = {}
        try:
            debug          = self.get_argument('debug','false').lower() == 'true'
            refresh        = self.get_argument('refresh','false').lower() == 'true'
            device_profile = self.get_argument('profile','default')
            url            = self.get_argument('url').lower()

            if debug: logger.setLevel(logging.DEBUG)
            logger.debug('reflowit_server.MainHandler: url=%s device_profile=%s refresh=%s debug=%s'%(url, device_profile, refresh, debug))

            uid = hashlib.md5(url).hexdigest()
            json_data_path = os.path.join(OUTDIR,uid,'%s.json'%uid)
            queue_path = os.path.join(INQUEUE,'%s.pdf'%uid)

            if os.path.exists(json_data_path):
                with open(json_data_path,'rb') as json_data_fp:
                    results = json.load(json_data_fp)
                if os.path.exists(queue_path):
                    os.remove(queue_path)
            else:
                if not os.path.exists(queue_path):
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        pdf = resp.content
                        with open(queue_path,'wb') as pdf_fp:
                            pdf_fp.write(pdf)
                        logger.debug('pdf_path=%s size=%s'%(queue_path,len(pdf)))
                        #execute_external_cmd('source %s/virtualenv/bin/activate; nohup python %s/convert.py -d -p %s -s %s'%(BASEDIR, BASEDIR, device_profile, queue_path), background=True)
                        execute_external_cmd('nohup python %s/convert.py -d -p %s -s %s'%(BASEDIR, device_profile, queue_path), background=True)
                self.set_status(202)
        except:
            logger.error(traceback.format_exc())
        self.write(results)

class PDFHandler(tornado.web.RequestHandler):

    def get(self, pdf_fname):
        pdf_path = os.path.join(PDFS_DIR,pdf_fname)
        logger.info(pdf_path)
        with open(pdf_path,'rb') as pdf_fp:
            self.set_header("Content-Type", 'application/pdf; charset="utf-8"')
            self.set_header("Content-Disposition", "attachment; filename=%s"%pdf_fname)
            self.write(pdf_fp.read())

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/?", MainHandler),
			(r"/pdf/(.*)", PDFHandler),
		]
		tornado.web.Application.__init__(self, handlers)

def execute_external_cmd(cmd, background=False):
    """
    Execute the external command and get its exitcode, stdout and stderr.
    """
    logger.debug(cmd)
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    if not background:
        out, err = proc.communicate()
        exitcode = proc.returncode
        return exitcode, out, err

def main(port=DEFAULT_PORT):
    logger.info('Starting server on port %s' % port)
    app = Application()
    app.listen(port)
    IOLoop.instance().start()

if __name__ == '__main__':
	main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT)
