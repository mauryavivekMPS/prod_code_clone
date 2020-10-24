CREATE TABLE impactvizor.test_institution_usage_stat (
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
    PRIMARY KEY ((publisher_id, counter_type), journal, subscriber_id, usage_date, usage_category)
) WITH CLUSTERING ORDER BY (journal ASC, subscriber_id ASC, usage_date ASC, usage_category ASC)
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys':'ALL', 'rows_per_partition':'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND default_time_to_live = 0
    AND gc_grace_seconds = 0
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';
CREATE INDEX test_institution_usage_stat_usage_date_index ON impactvizor.test_institution_usage_stat (usage_date);
