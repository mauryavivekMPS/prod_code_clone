#!/usr/bin/env bash

IVETL_QA=1
export IVETL_QA

unset IVETL_LOCAL
unset IVETL_PROD

IVETL_ROOT=/iv/impactvizor-pipeline
export IVETL_ROOT

IVETL_CASSANDRA_IP=10.0.0.115
export IVETL_CASSANDRA_IP

IVETL_EMAIL_TO_ADDRESS=john@hyperplane.io
export IVETL_EMAIL_TO_ADDRESS

DJANGO_SETTINGS_MODULE=ivweb.settings.qa
export DJANGO_SETTINGS_MODULE