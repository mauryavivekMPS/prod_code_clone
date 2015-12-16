#!/usr/bin/env bash

if [ -n "$IVETL_PROD" ]
then
    echo "This script won't work on prod (without editing by hand). Be careful!"
    exit 1
fi

cqlsh -f 1.0/01_drop_keyspace_ddl.cql
cqlsh -f 1.0/02_create_keyspace_ddl.cql
echo "Dropped and recreated database"

cqlsh -f 1.0/03_create_metadata_ddl.cql
cqlsh -f 1.0/04_create_ac_article_citations_ddl.cql
cqlsh -f 1.0/05_create_issn_journal_ddl.cql
cqlsh -f 1.0/06_create_pa_published_article_ddl.cql
cqlsh -f 1.0/07_create_pa_published_article_values_ddl.cql
cqlsh -f 1.0/08_create_pipeline_status_ddl.cql
cqlsh -f 1.0/09_create_publisher_vizor_updates_ddl.cql
cqlsh -f 1.0/10_create_rat_rejected_articles_ddl.cql
echo "Created schema for 1.0"

cqlsh -f 1.1/01_add_custom_cols_ddl.cql
echo "Updated to 1.1"

cqlsh -f 1.2/01_add_crossref_login_cols.cql
cqlsh -f 1.2/02_add_crossref_logins.cql
cqlsh -f 1.2/03_drop_source_field.cql
echo "Updated to 1.2"

cqlsh -f 1.3/01_add_rejected_manuscripts_cols_ddl.cql
cqlsh -f 1.3/02_add_audit_log.cql
cqlsh -f 1.3/03_add_supported_products.cql
cqlsh -f 1.3/04_add_pilot_flag.cql
cqlsh -f 1.3/05_alter_sources_list.cql
cqlsh -f 1.3/06_add_cohort_flags.cql
cqlsh -f 1.3/07_user_tables.cql
cqlsh -f 1.3/08_add_publisher_metadata.cql
cqlsh -f 1.3/09_add_cohort_publishers.cql
cqlsh -f 1.3/10_add_publisher_rsc.cql
cqlsh -f 1.3/11_add_cohort_flags.cql
cqlsh -f 1.3/13_create_published_article_by_cohort.cql
echo "Updated to 1.3"

cqlsh -f 1.4/01_create_publisher_journal.cql
cqlsh -f 1.4/02_add_publisher_email.cql
cqlsh -f 1.4/03_recreate_status_tables.cql
cqlsh -f 1.4/04_add_publisher_journals.cql
echo "Updated to 1.4"

cqlsh -f 1.5/01_add_scopus_api_keys.cql
echo "Updated to 1.5"

cqlsh -f 1.6/01_add_email_to_status.cql
cqlsh -f 1.6/02_add_report_params_to_publisher.cql
cqlsh -f 1.6/03_add_scopus_keys_to_pool.cql
echo "Updated to 1.6"

cqlsh -f 1.7/01_add_article_usage.cql
cqlsh -f 1.7/02_add_usage_to_published_articles.cql
cqlsh -f 1.7/03_add_mendeley.cql
cqlsh -f 1.7/04_add_report_setup_status.cql
echo "Updated to 1.7"

cqlsh -f 1.8/03_recreate_join_tables.cql
echo "Updated to 1.8"
