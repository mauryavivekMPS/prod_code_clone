#!/usr/bin/env bash

IVETL_ROOT=/Users/nmehta/git/impactvizor-pipeline
export IVETL_ROOT

IVETL_LOCAL=1
export IVETL_LOCAL

unset IVETL_QA
unset IVETL_PROD

CQLSH=/Users/john/Projects/dse/bin/cqlsh
export CQLSH

DJANGO_SETTINGS_MODULE=ivweb.settings.local
export DJANGO_SETTINGS_MODULE