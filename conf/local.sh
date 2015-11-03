#!/usr/bin/env bash

IVETL_LOCAL=1
export IVETL_LOCAL

unset IVETL_QA
unset IVETL_PROD

DJANGO_SETTINGS_MODULE=ivweb.settings.local
export DJANGO_SETTINGS_MODULE