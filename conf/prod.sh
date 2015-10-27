#!/usr/bin/env bash

IVETL_PROD=1
export IVETL_PROD

unset IVETL_LOCAL
unset IVETL_QA

IVETL_ROOT=/iv/impactvizor-pipeline
export IVETL_ROOT

IVETL_CASSANDRA_IP=10.0.1.12
export IVETL_CASSANDRA_IP

DJANGO_SETTINGS_MODULE=ivweb.settings.qa
export DJANGO_SETTINGS_MODULE