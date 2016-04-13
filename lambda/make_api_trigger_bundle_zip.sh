#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $ROOT
zip -9 api_trigger_bundle.zip api_gateway_trigger_handler.py
cd $ROOT/virtualenv/lib/python2.7/site-packages/
zip -r9 $ROOT/api_trigger_bundle.zip *
cd $ROOT
