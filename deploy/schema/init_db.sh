#!/usr/bin/env bash

if [ -n "$IVETL_PROD" ]
then
    echo "This script won't work on prod (without editing by hand). Be careful!"
    exit 1
fi

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/01_drop_keyspace_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/02_create_keyspace_ddl.cql
echo "Dropped and recreated database"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/03_create_metadata_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/04_create_ac_article_citations_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/05_create_issn_journal_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/06_create_pa_published_article_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/07_create_pa_published_article_values_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/08_create_pipeline_status_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/09_create_publisher_vizor_updates_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.0/10_create_rat_rejected_articles_ddl.cql
echo "Created schema for 1.0"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.1/01_add_custom_cols_ddl.cql
echo "Updated to 1.1"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.2/01_add_crossref_login_cols.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.2/02_add_crossref_logins.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.2/03_drop_source_field.cql
echo "Updated to 1.2"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/01_add_rejected_manuscripts_cols_ddl.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/02_add_audit_log.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/03_add_supported_products.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/04_add_pilot_flag.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/05_alter_sources_list.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/06_add_cohort_flags.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/07_user_tables.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/08_add_publisher_metadata.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/09_add_cohort_publishers.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/10_add_publisher_rsc.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/11_add_cohort_flags.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.3/13_create_published_article_by_cohort.cql
echo "Updated to 1.3"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.4/01_create_publisher_journal.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.4/02_add_publisher_email.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.4/03_recreate_status_tables.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.4/04_add_publisher_journals.cql
echo "Updated to 1.4"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.5/01_add_scopus_api_keys.cql
echo "Updated to 1.5"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.6/01_add_email_to_status.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.6/02_add_report_params_to_publisher.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.6/03_add_scopus_keys_to_pool.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.6/04_add_tableu_ids.cql
echo "Updated to 1.6"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.7/01_add_article_usage.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.7/02_add_usage_to_published_articles.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.7/03_add_mendeley.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.7/04_add_report_setup_status.cql
echo "Updated to 1.7"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.8/01_add_temporary_join_tables.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.8/03_recreate_join_tables.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.8/05_delete_temp_join_tables.cql
echo "Updated to 1.8"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 1.9/01_add_mendeley_to_rejected_articles.cql
echo "Updated to 1.9"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.0/01_add_demos.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.0/02_add_demo_flag.cql
echo "Updated to 2.0"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.1/01_add_uptime_checks.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.1/02_add_highwire_metadata.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.1/03_add_highwire_publisher.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.1/04_add_system_globals.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.1/05_add_params_col.cql
echo "Updated to 2.1"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.2/01_add_doi_transform_rules.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.2/02_add_demo_flag_index.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.2/03_add_archived_flag.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.2/04_add_months_until_free.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.2/05_recreate_article_usage.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.2/06_add_use_months_flag.cql
echo "Updated to 2.2"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.3/01_add_use_benchpress.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.3/03_recreate_doi_transform.cql
echo "Updated to 2.3"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.4/01_add_drupal_metadata.cql
echo "Updated to 2.4"

/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.5/01_add_attribute_values.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.5/02_add_alert.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.5/03_add_citation_count.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.5/04_add_email_to_alert.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.5/05_add_filter_params.cql
/opt/apache-cassandra-2.1.14/bin/cqlsh -f 2.5/07_add_archived_to_alert.cql
echo "Updated to 2.5"
