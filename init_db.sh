#!/usr/bin/env bash

if [ -n "$IVETL_PROD" ]
then
    echo "This script won't work on prod (without editing by hand). Be careful!"
    exit 1
fi

$CQLSH -f deploy/schema/drop_keyspace_ddl.cql
$CQLSH -f deploy/schema/create_keyspace_ddl.cql
echo "Dropped and recreated database"

$CQLSH -f deploy/schema/create_metadata_ddl.cql
$CQLSH -f deploy/schema/create_ac_article_citations_ddl.cql
$CQLSH -f deploy/schema/create_issn_journal_ddl.cql
$CQLSH -f deploy/schema/create_pa_published_article_ddl.cql
$CQLSH -f deploy/schema/create_pa_published_article_values_ddl.cql
$CQLSH -f deploy/schema/create_pipeline_status_ddl.cql
$CQLSH -f deploy/schema/create_publisher_vizor_updates_ddl.cql
$CQLSH -f deploy/schema/create_rat_rejected_articles_ddl.cql
echo "Created schema"