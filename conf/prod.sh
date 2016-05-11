#!/usr/bin/env bash

IVETL_PROD=1
export IVETL_PROD

unset IVETL_LOCAL
unset IVETL_QA

IVETL_ROOT=/iv/impactvizor-pipeline
export IVETL_ROOT

IVETL_CASSANDRA_IP=10.0.1.59,10.0.1.196,10.0.1.40
export IVETL_CASSANDRA_IP

IVETL_TABLEAU_SERVER=vizors.org
export IVETL_TABLEAU_SERVER

IVETL_TABLEAU_USERNAME=nmehta
export IVETL_TABLEAU_USERNAME

IVETL_TABLEAU_PASSWORD=Reena,1275
export IVETL_TABLEAU_PASSWORD

IVETL_WEB_ADDRESS=http://manage.vizors.org
export IVETL_WEB_ADDRESS

DJANGO_SETTINGS_MODULE=ivweb.settings.prod
export DJANGO_SETTINGS_MODULE
