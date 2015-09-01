#!/usr/bin/env bash

if [ -n "$IVETL_PROD" ]
then
    echo "This script won't work on prod (without editing by hand). Be careful!"
    exit 1
fi

$CQLSH -f deploy/schema/1.0/01_drop_keyspace_ddl.cql
$CQLSH -f deploy/schema/1.0/02_create_keyspace_ddl.cql
echo "Dropped and recreated database"

$CQLSH -f deploy/schema/1.0/03_create_metadata_ddl.cql
$CQLSH -f deploy/schema/1.0/04_create_ac_article_citations_ddl.cql
$CQLSH -f deploy/schema/1.0/05_create_issn_journal_ddl.cql
$CQLSH -f deploy/schema/1.0/06_create_pa_published_article_ddl.cql
$CQLSH -f deploy/schema/1.0/07_create_pa_published_article_values_ddl.cql
$CQLSH -f deploy/schema/1.0/08_create_pipeline_status_ddl.cql
$CQLSH -f deploy/schema/1.0/09_create_publisher_vizor_updates_ddl.cql
$CQLSH -f deploy/schema/1.0/10_create_rat_rejected_articles_ddl.cql
echo "Created schema for 1.0"

$CQLSH -f deploy/schema/1.0/01_add_custom_cols_ddl.cql
echo "Updated to 1.1"

