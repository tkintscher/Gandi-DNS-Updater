#!/bin/bash

SCRIPT=`dirname $0`/gandi.py
APIKEY=123456

$SCRIPT $APIKEY foo.example.com AAAA ::1
