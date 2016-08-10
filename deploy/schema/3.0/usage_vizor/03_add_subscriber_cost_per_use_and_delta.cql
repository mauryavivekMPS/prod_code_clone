USE impactvizor;

CREATE TABLE subscription_cost_per_use (
  publisher_id text,
  membership_no text,
  bundle_name text,
  month timestamp,
  amount decimal,
  category_usage map<text, int>,
  total_usage int,
  cost_per_use decimal,
  PRIMARY KEY ((publisher_id), membership_no, bundle_name, month)
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

CREATE TABLE subscription_cost_per_use_delta (
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
