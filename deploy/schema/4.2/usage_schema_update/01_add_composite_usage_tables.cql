USE impactvizor;

CREATE TABLE institution_usage_stat_composite (
  publisher_id text,
  counter_type text,
  journal text,
  journal_print_issn text,
  journal_online_issn text,
  subscriber_id text,
  institution_name text,
  usage_date timestamp,
  usage_category text,
  usage int,
  bundle_name text,
  amount decimal,
  trial boolean,
  trial_expiration_date timestamp,
  PRIMARY KEY ((publisher_id, counter_type, journal), subscriber_id, usage_date, usage_category)
) WITH
  bloom_filter_fp_chance=0.010000 AND
  caching='KEYS_ONLY' AND
  comment='' AND
  dclocal_read_repair_chance=0.100000 AND
  gc_grace_seconds=864000 AND
  index_interval=128 AND
  read_repair_chance=0.000000 AND
  replicate_on_write='true' AND
  populate_io_cache_on_flush='false' AND
  default_time_to_live=0 AND
  speculative_retry='99.0PERCENTILE' AND
  memtable_flush_period_in_ms=0 AND
  compaction={'class': 'SizeTieredCompactionStrategy'} AND
  compression={'sstable_compression': 'LZ4Compressor'};

CREATE INDEX institution_usage_stat_composite_usage_date_index ON institution_usage_stat_composite(usage_date);

CREATE TABLE institution_usage_journal (
  publisher_id text,
  counter_type text,
  journal text,
  PRIMARY KEY ((publisher_id), counter_type, journal)
) WITH
  bloom_filter_fp_chance=0.010000 AND
  caching='KEYS_ONLY' AND
  comment='' AND
  dclocal_read_repair_chance=0.100000 AND
  gc_grace_seconds=864000 AND
  index_interval=128 AND
  read_repair_chance=0.000000 AND
  replicate_on_write='true' AND
  populate_io_cache_on_flush='false' AND
  default_time_to_live=0 AND
  speculative_retry='99.0PERCENTILE' AND
  memtable_flush_period_in_ms=0 AND
  compaction={'class': 'SizeTieredCompactionStrategy'} AND
  compression={'sstable_compression': 'LZ4Compressor'};
