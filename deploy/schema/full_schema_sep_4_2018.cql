
CREATE KEYSPACE impactvizor WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '3'}  AND durable_writes = true;

CREATE TABLE impactvizor.tableau_notification (
    notification_id uuid PRIMARY KEY,
    alert_filters text,
    alert_id uuid,
    alert_params text,
    custom_message text,
    expiration_date timestamp,
    name text,
    notification_date timestamp,
    publisher_id text,
    template_id text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX tableau_notification_alert_id_index ON impactvizor.tableau_notification (alert_id);

CREATE TABLE impactvizor.f1000_social_data (
    doi text PRIMARY KEY,
    average_score decimal,
    f1000_id int,
    num_recommendations int,
    total_score int
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.published_article_additional_metadata (
    publisher_id text,
    doi text,
    article_type text,
    custom text,
    editor text,
    last_updated_from_file timestamp,
    last_updated_from_hw timestamp,
    subject_category text,
    PRIMARY KEY (publisher_id, doi)
) WITH CLUSTERING ORDER BY (doi ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.subscription_cpu_by_bundle_stat (
    publisher_id text,
    membership_no text,
    bundle_name text,
    usage_date timestamp,
    amount decimal,
    category_usage map<text, int>,
    cost_per_use decimal,
    total_usage int,
    PRIMARY KEY (publisher_id, membership_no, bundle_name, usage_date)
) WITH CLUSTERING ORDER BY (membership_no ASC, bundle_name ASC, usage_date ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX subscription_cpu_by_bundle_stat_usage_date_index ON impactvizor.subscription_cpu_by_bundle_stat (usage_date);

CREATE TABLE impactvizor.monthly_message (
    product_id text,
    pipeline_id text,
    message text,
    PRIMARY KEY ((product_id, pipeline_id))
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.demo (
    demo_id uuid PRIMARY KEY,
    archived boolean,
    name text,
    properties text,
    requestor_id uuid,
    start_date timestamp,
    status text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX demo_archived_index ON impactvizor.demo (archived);
CREATE INDEX requestor_id_index ON impactvizor.demo (requestor_id);

CREATE TABLE impactvizor.published_article_by_cohort (
    publisher_id text,
    is_cohort boolean,
    article_doi text,
    article_scopus_id text,
    crossref_citation_count int,
    scopus_citation_count int,
    updated timestamp,
    PRIMARY KEY (publisher_id, is_cohort, article_doi)
) WITH CLUSTERING ORDER BY (is_cohort ASC, article_doi ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.altmetrics_social_data (
    doi text PRIMARY KEY,
    altmetrics_id int,
    blogs int,
    facebook int,
    gplus int,
    news_outlets int,
    policy_docs int,
    reddit int,
    twitter int,
    video int,
    wikipedia int
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.publisher_metadata (
    publisher_id text PRIMARY KEY,
    ac_databases list<text>,
    archived boolean,
    cohort_articles_issns_to_lookup list<text>,
    cohort_articles_last_updated timestamp,
    crossref_password text,
    crossref_username text,
    demo boolean,
    demo_id text,
    email text,
    has_cohort boolean,
    hw_addl_metadata_available boolean,
    issn_to_hw_journal_code map<text, text>,
    name text,
    pilot boolean,
    published_articles_issns_to_lookup list<text>,
    published_articles_last_updated timestamp,
    reports_group_id text,
    reports_password text,
    reports_project text,
    reports_project_id text,
    reports_setup_status text,
    reports_user_id text,
    reports_username text,
    scopus_api_keys list<text>,
    scopus_key_setup_status text,
    supported_product_groups list<text>,
    supported_products list<text>
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX publisher_archived_index ON impactvizor.publisher_metadata (archived);
CREATE INDEX demo_index ON impactvizor.publisher_metadata (demo);
CREATE INDEX demo_id_index ON impactvizor.publisher_metadata (demo_id);

CREATE TABLE impactvizor.tableau_notification_by_alert (
    publisher_id text,
    alert_id uuid,
    notification_id uuid,
    notification_date timestamp,
    PRIMARY KEY (publisher_id, alert_id, notification_id)
) WITH CLUSTERING ORDER BY (alert_id ASC, notification_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.pipeline_task_status (
    publisher_id text,
    product_id text,
    pipeline_id text,
    job_id text,
    task_id text,
    current_record_count int,
    duration_seconds int,
    end_time timestamp,
    error_details text,
    start_time timestamp,
    status text,
    task_args_json text,
    total_record_count int,
    updated timestamp,
    workfolder text,
    PRIMARY KEY (publisher_id, product_id, pipeline_id, job_id, task_id)
) WITH CLUSTERING ORDER BY (product_id ASC, pipeline_id ASC, job_id ASC, task_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.tableau_alert (
    publisher_id text,
    template_id text,
    alert_id uuid,
    alert_filters text,
    alert_params text,
    archived boolean,
    attachment_only_emails list<text>,
    created timestamp,
    created_by uuid,
    custom_message text,
    enabled boolean,
    full_emails list<text>,
    name text,
    send_with_no_data boolean,
    PRIMARY KEY (publisher_id, template_id, alert_id)
) WITH CLUSTERING ORDER BY (template_id ASC, alert_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX tableau_alert_alert_id_index ON impactvizor.tableau_alert (alert_id);
CREATE INDEX tableau_alert_archived_index ON impactvizor.tableau_alert (archived);
CREATE INDEX tableau_alert_created_by_index ON impactvizor.tableau_alert (created_by);

CREATE TABLE impactvizor.subscriber_values (
    publisher_id text,
    membership_no text,
    source text,
    name text,
    value_text text,
    PRIMARY KEY (publisher_id, membership_no, source, name)
) WITH CLUSTERING ORDER BY (membership_no ASC, source ASC, name ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.highwire_metadata (
    site_id int PRIMARY KEY,
    ac_db text,
    ac_machine text,
    ac_port text,
    ac_syb_server text,
    content_db text,
    content_syb_server text,
    counter_code text,
    dw_db text,
    dw_site_type text,
    dw_syb_server text,
    has_athens text,
    is_book text,
    journal_doi text,
    journal_info_feature text,
    legacy_date text,
    legacy_type text,
    name text,
    online_issn text,
    print_issn text,
    publisher text,
    sage_subject_area text,
    site_abbr text,
    site_code text,
    site_url text,
    sort_name text,
    subman_url text,
    umbrella_code text,
    umbrella_url text,
    usage_rpts_feature text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.institution_usage_stat_delta (
    publisher_id text,
    counter_type text,
    journal text,
    subscriber_id text,
    usage_date timestamp,
    usage_category text,
    time_slice text,
    absolute_delta int,
    current_usage int,
    percentage_delta float,
    previous_usage int,
    PRIMARY KEY (publisher_id, counter_type, journal, subscriber_id, usage_date, usage_category, time_slice)
) WITH CLUSTERING ORDER BY (counter_type ASC, journal ASC, subscriber_id ASC, usage_date ASC, usage_category ASC, time_slice ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 0
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.workbook_url (
    publisher_id text,
    workbook_id text,
    url text,
    PRIMARY KEY (publisher_id, workbook_id)
) WITH CLUSTERING ORDER BY (workbook_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.user (
    user_id uuid PRIMARY KEY,
    email text,
    first_name text,
    last_name text,
    password text,
    user_type int
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX email_index ON impactvizor.user (email);

CREATE TABLE impactvizor.doi_transform_rule (
    journal_code text,
    type text,
    match_expression text,
    transform_spec text,
    PRIMARY KEY (journal_code, type, match_expression)
) WITH CLUSTERING ORDER BY (type ASC, match_expression ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.audit_log_by_user (
    user_id uuid,
    event_time timestamp,
    action text,
    description text,
    publisher_id text,
    PRIMARY KEY (user_id, event_time, action)
) WITH CLUSTERING ORDER BY (event_time DESC, action ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.service_response_time (
    publisher_id text,
    name text,
    from_date timestamp,
    until_date timestamp,
    maximum bigint,
    mean float,
    minimum bigint,
    percentile_25 bigint,
    percentile_50 bigint,
    percentile_75 bigint,
    percentile_95 bigint,
    percentile_99 bigint,
    sample int,
    standard_deviation float,
    units text,
    variance float,
    PRIMARY KEY (publisher_id, name, from_date, until_date)
) WITH CLUSTERING ORDER BY (name ASC, from_date ASC, until_date ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.tableau_notification_event (
    notification_id uuid,
    event_type text,
    event_id text,
    alert_id uuid,
    email text,
    event_date timestamp,
    publisher_id text,
    PRIMARY KEY (notification_id, event_type, event_id)
) WITH CLUSTERING ORDER BY (event_type ASC, event_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.published_article (
    publisher_id text,
    article_doi text,
    altmetrics_blogs int,
    altmetrics_facebook int,
    altmetrics_gplus int,
    altmetrics_news_outlets int,
    altmetrics_policy_docs int,
    altmetrics_reddit int,
    altmetrics_twitter int,
    altmetrics_video int,
    altmetrics_wikipedia int,
    article_issue text,
    article_journal text,
    article_journal_issn text,
    article_pages text,
    article_publisher text,
    article_scopus_id text,
    article_title text,
    article_type text,
    article_volume text,
    citation_count int,
    citations_lookup_error boolean,
    citations_updated_on timestamp,
    co_authors text,
    created timestamp,
    custom text,
    custom_2 text,
    custom_3 text,
    date_of_publication timestamp,
    date_of_rejection timestamp,
    editor text,
    f1000_average_score decimal,
    f1000_num_recommendations int,
    f1000_total_score int,
    first_author text,
    from_rejected_manuscript boolean,
    has_abstract boolean,
    hw_metadata_retrieved boolean,
    is_cohort boolean,
    is_open_access text,
    is_tr_citable boolean,
    mendeley_saves int,
    meta_actual_citation_count int,
    meta_actual_ef decimal,
    meta_actual_tiers int,
    meta_pmid text,
    meta_predicted_citation_count int,
    meta_predicted_ef decimal,
    meta_predicted_tiers int,
    meta_top_1 int,
    meta_top_10 int,
    meta_top_25 int,
    meta_top_5 int,
    meta_top_50 int,
    month_usage_03 int,
    month_usage_06 int,
    month_usage_09 int,
    month_usage_12 int,
    month_usage_24 int,
    month_usage_36 int,
    month_usage_48 int,
    month_usage_60 int,
    month_usage_abstract_03 int,
    month_usage_abstract_06 int,
    month_usage_abstract_09 int,
    month_usage_abstract_12 int,
    month_usage_abstract_24 int,
    month_usage_abstract_36 int,
    month_usage_abstract_48 int,
    month_usage_abstract_60 int,
    month_usage_full_03 int,
    month_usage_full_06 int,
    month_usage_full_09 int,
    month_usage_full_12 int,
    month_usage_full_24 int,
    month_usage_full_36 int,
    month_usage_full_48 int,
    month_usage_full_60 int,
    month_usage_pdf_03 int,
    month_usage_pdf_06 int,
    month_usage_pdf_09 int,
    month_usage_pdf_12 int,
    month_usage_pdf_24 int,
    month_usage_pdf_36 int,
    month_usage_pdf_48 int,
    month_usage_pdf_60 int,
    previous_citation_count int,
    rejected_manuscript_editor text,
    rejected_manuscript_id text,
    scopus_citation_count int,
    scopus_subtype text,
    subject_category text,
    updated timestamp,
    usage_start_date timestamp,
    PRIMARY KEY (publisher_id, article_doi)
) WITH CLUSTERING ORDER BY (article_doi ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 60
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX article_scopus_id_idx ON impactvizor.published_article (article_scopus_id);

CREATE TABLE impactvizor.article_usage (
    publisher_id text,
    article_doi text,
    usage_type text,
    month_number int,
    month_usage int,
    usage_start_date timestamp,
    PRIMARY KEY (publisher_id, article_doi, usage_type, month_number)
) WITH CLUSTERING ORDER BY (article_doi ASC, usage_type ASC, month_number ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.monthly_citations_test2 (
    publisher_id text,
    article_doi text,
    citation_month timestamp,
    citation_count int,
    PRIMARY KEY (publisher_id, article_doi, citation_month)
) WITH CLUSTERING ORDER BY (article_doi ASC, citation_month ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.article_skip_rule (
    publisher_id text,
    is_cohort boolean,
    issn text,
    rule text,
    PRIMARY KEY (publisher_id, is_cohort, issn)
) WITH CLUSTERING ORDER BY (is_cohort ASC, issn ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.subscription_cpu_by_bundle_stat_delta (
    publisher_id text,
    membership_no text,
    bundle_name text,
    usage_date timestamp,
    time_slice text,
    absolute_delta decimal,
    current_amount decimal,
    current_cost_per_use decimal,
    current_total_usage int,
    percentage_delta float,
    previous_amount decimal,
    previous_cost_per_use decimal,
    previous_total_usage int,
    PRIMARY KEY (publisher_id, membership_no, bundle_name, usage_date, time_slice)
) WITH CLUSTERING ORDER BY (membership_no ASC, bundle_name ASC, usage_date ASC, time_slice ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.notification_summary (
    publisher_id text,
    alert_id uuid,
    product_id text,
    pipeline_id text,
    job_id text,
    notification_summary_id uuid,
    dismissed boolean,
    notification_date timestamp,
    values_list_json text,
    PRIMARY KEY (publisher_id, alert_id, product_id, pipeline_id, job_id, notification_summary_id)
) WITH CLUSTERING ORDER BY (alert_id ASC, product_id ASC, pipeline_id ASC, job_id ASC, notification_summary_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX notification_summary_notification_id_index ON impactvizor.notification_summary (notification_summary_id);
CREATE INDEX notification_summary_dismissed_index ON impactvizor.notification_summary (dismissed);

CREATE TABLE impactvizor.subscriber (
    publisher_id text,
    membership_no text,
    ac_database text,
    address_2 text,
    affiliation text,
    consortium text,
    contact text,
    country text,
    custom1 text,
    custom2 text,
    custom3 text,
    email_domain_srch text,
    expired boolean,
    final_expiration_date timestamp,
    firstname text,
    inst_key text,
    inst_name text,
    institution_alternate_identifier text,
    institution_alternate_name text,
    lastname text,
    memo text,
    modified_by_dt text,
    num_subscriptions int,
    region text,
    ringgold_id text,
    sales_agent text,
    start_date timestamp,
    subscr_type text,
    subscr_type_desc text,
    tier text,
    title text,
    user_address text,
    user_email text,
    user_fax text,
    user_phone text,
    user_systemname text,
    user_type text,
    PRIMARY KEY (publisher_id, membership_no)
) WITH CLUSTERING ORDER BY (membership_no ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX subscriber_membership_no_index ON impactvizor.subscriber (membership_no);
CREATE INDEX subscriber_user_type_index ON impactvizor.subscriber (user_type);

CREATE TABLE impactvizor.publisher_user (
    user_id uuid,
    publisher_id text,
    uid uuid,
    PRIMARY KEY (user_id, publisher_id, uid)
) WITH CLUSTERING ORDER BY (publisher_id ASC, uid ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX publisher_id_index ON impactvizor.publisher_user (publisher_id);

CREATE TABLE impactvizor.content_block (
    block_id text PRIMARY KEY,
    markdown text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.issn_journal (
    issn text PRIMARY KEY,
    journal text,
    publisher text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 86400
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.subscription_cpu_by_subscriber_stat (
    publisher_id text,
    membership_no text,
    usage_date timestamp,
    bundle_amount map<text, decimal>,
    bundle_usage map<text, int>,
    cost_per_use decimal,
    total_amount decimal,
    total_usage int,
    PRIMARY KEY (publisher_id, membership_no, usage_date)
) WITH CLUSTERING ORDER BY (membership_no ASC, usage_date ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX subscription_cpu_by_subscriber_stat_usage_date_index ON impactvizor.subscription_cpu_by_subscriber_stat (usage_date);

CREATE TABLE impactvizor.uploaded_file (
    publisher_id text,
    uploaded_file_id uuid,
    processed_time timestamp,
    job_id text,
    original_name text,
    path text,
    pipeline_id text,
    product_id text,
    user_id uuid,
    validated boolean,
    PRIMARY KEY (publisher_id, uploaded_file_id, processed_time)
) WITH CLUSTERING ORDER BY (uploaded_file_id ASC, processed_time DESC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.institution_usage_stat_composite (
    publisher_id text,
    counter_type text,
    journal text,
    subscriber_id text,
    usage_date timestamp,
    usage_category text,
    amount decimal,
    bundle_name text,
    institution_name text,
    journal_online_issn text,
    journal_print_issn text,
    trial boolean,
    trial_expiration_date timestamp,
    usage int,
    PRIMARY KEY ((publisher_id, counter_type, journal), subscriber_id, usage_date, usage_category)
) WITH CLUSTERING ORDER BY (subscriber_id ASC, usage_date ASC, usage_category ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX institution_usage_stat_composite_usage_date_index ON impactvizor.institution_usage_stat_composite (usage_date);

CREATE TABLE impactvizor.institution_usage_stat_delta_composite (
    publisher_id text,
    counter_type text,
    journal text,
    subscriber_id text,
    usage_date timestamp,
    usage_category text,
    time_slice text,
    absolute_delta int,
    current_usage int,
    percentage_delta float,
    previous_usage int,
    PRIMARY KEY ((publisher_id, counter_type, journal), subscriber_id, usage_date, usage_category, time_slice)
) WITH CLUSTERING ORDER BY (subscriber_id ASC, usage_date ASC, usage_category ASC, time_slice ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.rejected_articles (
    publisher_id text,
    rejected_article_id timeuuid,
    article_type text,
    authors_match_score decimal,
    citation_lookup_status text,
    citations int,
    co_authors text,
    corresponding_author text,
    created timestamp,
    crossref_doi text,
    crossref_match_score decimal,
    custom text,
    custom_2 text,
    custom_3 text,
    date_of_publication timestamp,
    date_of_rejection timestamp,
    editor text,
    first_author text,
    keywords text,
    manuscript_id text,
    manuscript_title text,
    mendeley_saves int,
    preprint_doi text,
    published_co_authors text,
    published_first_author text,
    published_journal text,
    published_journal_issn text,
    published_publisher text,
    published_title text,
    reject_reason text,
    scopus_doi_status text,
    scopus_id text,
    source_file_name text,
    status text,
    subject_category text,
    submitted_journal text,
    updated timestamp,
    PRIMARY KEY (publisher_id, rejected_article_id)
) WITH CLUSTERING ORDER BY (rejected_article_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 0
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX manuscript_id_index ON impactvizor.rejected_articles (manuscript_id);
CREATE INDEX submmited_journal_index ON impactvizor.rejected_articles (submitted_journal);

CREATE TABLE impactvizor.uptime_check_metadata (
    publisher_id text,
    check_id int,
    check_name text,
    check_type text,
    check_url text,
    drupal_launch_date timestamp,
    pingdom_account text,
    publisher_code text,
    publisher_name text,
    site_code text,
    site_name text,
    site_platform text,
    site_type text,
    PRIMARY KEY (publisher_id, check_id)
) WITH CLUSTERING ORDER BY (check_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.publisher_vizor_updates (
    publisher_id text,
    vizor_id text,
    updated timestamp,
    PRIMARY KEY (publisher_id, vizor_id)
) WITH CLUSTERING ORDER BY (vizor_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.scopus_api_key (
    key text PRIMARY KEY
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.institution_usage_stat (
    publisher_id text,
    counter_type text,
    journal text,
    subscriber_id text,
    usage_date timestamp,
    usage_category text,
    amount decimal,
    bundle_name text,
    institution_name text,
    journal_online_issn text,
    journal_print_issn text,
    trial boolean,
    trial_expiration_date timestamp,
    usage int,
    PRIMARY KEY (publisher_id, counter_type, journal, subscriber_id, usage_date, usage_category)
) WITH CLUSTERING ORDER BY (counter_type ASC, journal ASC, subscriber_id ASC, usage_date ASC, usage_category ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 0
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX institution_usage_stat_usage_date_index ON impactvizor.institution_usage_stat (usage_date);

CREATE TABLE impactvizor.service_response_code (
    publisher_id text,
    name text,
    from_date timestamp,
    until_date timestamp,
    status_code text,
    count int,
    sample int,
    PRIMARY KEY (publisher_id, name, from_date, until_date, status_code)
) WITH CLUSTERING ORDER BY (name ASC, from_date ASC, until_date ASC, status_code ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.alert (
    publisher_id text,
    check_id text,
    alert_id uuid,
    archived boolean,
    check_params text,
    emails list<text>,
    enabled boolean,
    filter_params text,
    name text,
    PRIMARY KEY (publisher_id, check_id, alert_id)
) WITH CLUSTERING ORDER BY (check_id ASC, alert_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX alert_alert_id_index ON impactvizor.alert (alert_id);
CREATE INDEX alert_archived_index ON impactvizor.alert (archived);

CREATE TABLE impactvizor.article_citations (
    publisher_id text,
    article_doi text,
    citation_doi text,
    article_date_of_publication timestamp,
    citation_count int,
    citation_date timestamp,
    citation_first_author text,
    citation_issue text,
    citation_journal_issn text,
    citation_journal_title text,
    citation_pages text,
    citation_scopus_id text,
    citation_source text,
    citation_source_scopus boolean,
    citation_source_xref boolean,
    citation_sources list<text>,
    citation_title text,
    citation_volume text,
    created timestamp,
    is_cohort boolean,
    updated timestamp,
    PRIMARY KEY (publisher_id, article_doi, citation_doi)
) WITH CLUSTERING ORDER BY (article_doi ASC, citation_doi ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 0
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX article_citations_is_cohort_index ON impactvizor.article_citations (is_cohort);

CREATE TABLE impactvizor.subscription_cpu_by_subscriber_stat_delta (
    publisher_id text,
    membership_no text,
    usage_date timestamp,
    time_slice text,
    absolute_delta decimal,
    current_cost_per_use decimal,
    current_total_amount decimal,
    current_total_usage int,
    percentage_delta float,
    previous_cost_per_use decimal,
    previous_total_amount decimal,
    previous_total_usage int,
    PRIMARY KEY (publisher_id, membership_no, usage_date, time_slice)
) WITH CLUSTERING ORDER BY (membership_no ASC, usage_date ASC, time_slice ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.tableau_users (
    tableau_username text PRIMARY KEY,
    publisher_id text,
    tableau_project text,
    vizors set<text>
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.institution_usage_journal (
    publisher_id text,
    counter_type text,
    journal text,
    PRIMARY KEY (publisher_id, counter_type, journal)
) WITH CLUSTERING ORDER BY (counter_type ASC, journal ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.subscription_pricing (
    publisher_id text,
    membership_no text,
    year int,
    bundle_name text,
    amount decimal,
    trial boolean,
    trial_expiration_date timestamp,
    PRIMARY KEY (publisher_id, membership_no, year, bundle_name)
) WITH CLUSTERING ORDER BY (membership_no ASC, year ASC, bundle_name ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.drupal_metadata (
    site_id text PRIMARY KEY,
    created timestamp,
    launch_date timestamp,
    name text,
    product text,
    publisher text,
    site_code text,
    site_url text,
    type text,
    umbrella_code text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.system_global (
    name text PRIMARY KEY,
    date_value timestamp,
    int_value int,
    text_value text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.citable_section (
    publisher_id text,
    journal_issn text,
    article_type text,
    PRIMARY KEY (publisher_id, journal_issn, article_type)
) WITH CLUSTERING ORDER BY (journal_issn ASC, article_type ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.publisher_journal (
    publisher_id text,
    product_id text,
    uid uuid,
    electronic_issn text,
    journal_code text,
    months_until_free int,
    print_issn text,
    use_benchpress boolean,
    use_months_until_free boolean,
    PRIMARY KEY (publisher_id, product_id, uid)
) WITH CLUSTERING ORDER BY (product_id ASC, uid ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX publisher_journal_use_benchpress_index ON impactvizor.publisher_journal (use_benchpress);

CREATE TABLE impactvizor.subscription (
    publisher_id text,
    membership_no text,
    journal_code text,
    subscr_type_cd text,
    ac_database text,
    expiration_dt timestamp,
    institution_number text,
    last_used_dt timestamp,
    modified_by_dt timestamp,
    product_cd text,
    subscr_status text,
    subscr_type text,
    subscr_type_desc text,
    PRIMARY KEY (publisher_id, membership_no, journal_code, subscr_type_cd)
) WITH CLUSTERING ORDER BY (membership_no ASC, journal_code ASC, subscr_type_cd ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.attribute_values (
    publisher_id text,
    name text,
    values_json text,
    PRIMARY KEY (publisher_id, name)
) WITH CLUSTERING ORDER BY (name ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.audit_log_by_time (
    month text,
    event_time timestamp,
    action text,
    description text,
    publisher_id text,
    user_id uuid,
    PRIMARY KEY (month, event_time, action)
) WITH CLUSTERING ORDER BY (event_time DESC, action ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.audit_log_by_publisher (
    publisher_id text,
    event_time timestamp,
    action text,
    description text,
    user_id uuid,
    PRIMARY KEY (publisher_id, event_time, action)
) WITH CLUSTERING ORDER BY (event_time DESC, action ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.value_mapping (
    publisher_id text,
    mapping_type text,
    original_value text,
    canonical_value text,
    PRIMARY KEY (publisher_id, mapping_type, original_value)
) WITH CLUSTERING ORDER BY (mapping_type ASC, original_value ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX value_mapping_canonical_value_index ON impactvizor.value_mapping (canonical_value);

CREATE TABLE impactvizor.published_article_values (
    publisher_id text,
    article_doi text,
    source text,
    name text,
    value_text text,
    PRIMARY KEY (publisher_id, article_doi, source, name)
) WITH CLUSTERING ORDER BY (article_doi ASC, source ASC, name ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.uptime_override (
    override_id uuid PRIMARY KEY,
    applied_date timestamp,
    end_date timestamp,
    label text,
    match_expression_json text,
    notes text,
    override_type text,
    start_date timestamp
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.singleton_task_status (
    task_type text,
    task_id text,
    end_time timestamp,
    properties_json text,
    start_time timestamp,
    status text,
    PRIMARY KEY (task_type, task_id)
) WITH CLUSTERING ORDER BY (task_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.product_bundle (
    publisher_id text,
    bundle_name text,
    journal_issns list<text>,
    PRIMARY KEY (publisher_id, bundle_name)
) WITH CLUSTERING ORDER BY (bundle_name ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX product_bundle_journal_issns_index ON impactvizor.product_bundle (journal_issns);

CREATE TABLE impactvizor.notification (
    publisher_id text,
    alert_id uuid,
    product_id text,
    pipeline_id text,
    job_id text,
    notification_id uuid,
    values_json text,
    PRIMARY KEY (publisher_id, alert_id, product_id, pipeline_id, job_id, notification_id)
) WITH CLUSTERING ORDER BY (alert_id ASC, product_id ASC, pipeline_id ASC, job_id ASC, notification_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.pipeline_status (
    publisher_id text,
    product_id text,
    pipeline_id text,
    job_id text,
    current_task text,
    current_task_count int,
    duration_seconds int,
    end_time timestamp,
    error_details text,
    params_json text,
    start_time timestamp,
    status text,
    stop_instruction text,
    total_count int,
    total_task_count int,
    updated timestamp,
    user_email text,
    workfolder text,
    PRIMARY KEY (publisher_id, product_id, pipeline_id, job_id)
) WITH CLUSTERING ORDER BY (product_id ASC, pipeline_id ASC, job_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.monthly_citations_test (
    publisher_id text,
    article_doi text,
    citation_doi text,
    article_date_of_publication timestamp,
    citation_count int,
    citation_date timestamp,
    PRIMARY KEY (publisher_id, article_doi, citation_doi)
) WITH CLUSTERING ORDER BY (article_doi ASC, citation_doi ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.uptime_check_stat (
    publisher_id text,
    check_id int,
    check_date timestamp,
    avg_response_ms int,
    original_avg_response_ms int,
    original_total_down_sec int,
    original_total_unknown_sec int,
    original_total_up_sec int,
    override boolean,
    total_down_sec int,
    total_unknown_sec int,
    total_up_sec int,
    PRIMARY KEY (publisher_id, check_id, check_date)
) WITH CLUSTERING ORDER BY (check_id ASC, check_date ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.value_mapping_display (
    publisher_id text,
    mapping_type text,
    canonical_value text,
    display_value text,
    PRIMARY KEY (publisher_id, mapping_type, canonical_value)
) WITH CLUSTERING ORDER BY (mapping_type ASC, canonical_value ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';

CREATE TABLE impactvizor.audit_log (
    user_id uuid,
    event_time timestamp,
    action text,
    entity_id text,
    entity_type text,
    PRIMARY KEY (user_id, event_time, action, entity_id)
) WITH CLUSTERING ORDER BY (event_time ASC, action ASC, entity_id ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.1
    AND speculative_retry = '99.0PERCENTILE';

