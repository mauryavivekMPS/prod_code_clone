#!/usr/bin/env bash

if [ -n "$IVETL_PROD" ]
then
    echo "This script won't work on prod (without editing by hand). Be careful!"
    exit 1
fi

cqlsh -f deploy/schema/1.0/01_drop_keyspace_ddl.cql
cqlsh -f deploy/schema/1.0/02_create_keyspace_ddl.cql
echo "Dropped and recreated database"

cqlsh -f deploy/schema/1.0/03_create_metadata_ddl.cql
cqlsh -f deploy/schema/1.0/04_create_ac_article_citations_ddl.cql
cqlsh -f deploy/schema/1.0/05_create_issn_journal_ddl.cql
cqlsh -f deploy/schema/1.0/06_create_pa_published_article_ddl.cql
cqlsh -f deploy/schema/1.0/07_create_pa_published_article_values_ddl.cql
cqlsh -f deploy/schema/1.0/08_create_pipeline_status_ddl.cql
cqlsh -f deploy/schema/1.0/09_create_publisher_vizor_updates_ddl.cql
cqlsh -f deploy/schema/1.0/10_create_rat_rejected_articles_ddl.cql
echo "Created schema for 1.0"

cqlsh -f deploy/schema/1.1/01_add_custom_cols_ddl.cql
echo "Updated to 1.1"

cqlsh -f deploy/schema/1.2/01_add_crossref_login_cols.cql
cqlsh -f deploy/schema/1.2/02_add_crossref_logins.cql
cqlsh -f deploy/schema/1.2/03_add_sources_list.cql
python deploy/schema/1.2/04_migrate_citation_source_to_list.py
cqlsh -f deploy/schema/1.2/05_drop_source_field.cql
echo "Updated to 1.2"
