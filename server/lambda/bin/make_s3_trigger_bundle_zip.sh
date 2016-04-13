#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $ROOT
zip -9 s3_trigger_bundle.zip s3_trigger_handler.py
zip -9 s3_trigger_bundle.zip convert.py
zip -9 s3_trigger_bundle.zip k2pdfopt_linux
zip -9 s3_trigger_bundle.zip gs-919-linux
cd $ROOT/virtualenv/lib/python2.7/site-packages/
zip -r9 $ROOT/s3_trigger_bundle.zip *
cd $ROOT
