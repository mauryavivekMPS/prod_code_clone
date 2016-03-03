USE impactvizor;

CREATE TABLE uptime_check_metadata (
  publisher_id text,
  check_id int,
  check_type text,
  check_name text,
  check_url text,
  pingdom_account text,
  site_code text,
  site_name text,
  site_type text,
  site_platform text,
  publisher_name text,
  publisher_code text,
  PRIMARY KEY ((publisher_id), check_id)
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

CREATE TABLE uptime_check_stat (
  publisher_id text,
  check_id int,
  check_date timestamp,
  avg_response_ms int,
  total_up_sec int,
  total_down_sec int,
  total_unknown_sec int,
  PRIMARY KEY ((publisher_id), check_id, check_date)
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
