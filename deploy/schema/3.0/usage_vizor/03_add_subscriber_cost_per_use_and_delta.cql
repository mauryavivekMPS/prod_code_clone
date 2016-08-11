USE impactvizor;

CREATE TABLE subscription_cpu_by_bundle_stat (
  publisher_id text,
  membership_no text,
  bundle_name text,
  usage_date timestamp,
  amount decimal,
  category_usage map<text, int>,
  total_usage int,
  cost_per_use decimal,
  PRIMARY KEY ((publisher_id), membership_no, bundle_name, usage_date)
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

CREATE INDEX subscription_cpu_by_bundle_stat_usage_date_index ON subscription_cpu_by_bundle_stat(usage_date);

CREATE TABLE subscription_cpu_by_subscriber_stat (
  publisher_id text,
  membership_no text,
  usage_date timestamp,
  bundle_amount map<text, decimal>,
  total_amount decimal,
  bundle_usage map<text, int>,
  total_usage int,
  cost_per_use decimal,
  PRIMARY KEY ((publisher_id), membership_no, usage_date)
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

CREATE INDEX subscription_cpu_by_subscriber_stat_usage_date_index ON subscription_cpu_by_subscriber_stat(usage_date);

CREATE TABLE subscription_cpu_by_bundle_stat_delta (
  publisher_id text,
  membership_no text,
  bundle_name text,
  usage_date timestamp,
  time_slice text,
  previous_cost_per_use decimal,
  current_cost_per_use decimal,
  absolute_delta decimal,
  percentage_delta float,
  PRIMARY KEY ((publisher_id), membership_no, bundle_name, usage_date, time_slice)
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

CREATE TABLE subscription_cpu_by_subscriber_stat_delta (
  publisher_id text,
  membership_no text,
  usage_date timestamp,
  time_slice text,
  previous_cost_per_use decimal,
  current_cost_per_use decimal,
  absolute_delta decimal,
  percentage_delta float,
  PRIMARY KEY ((publisher_id), membership_no, usage_date, time_slice)
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
