USE impactvizor;

CREATE TABLE service_response_time (
  publisher_id text,
  name text,
  from_date timestamp,
  until_date timestamp,
  sample int,
  units text,
  mean float,
  standard_deviation float,
  variance float,
  minimum int,
  maximum int,
  percentile_25 int,
  percentile_50 int,
  percentile_75 int,
  percentile_95 int,
  percentile_99 int,
  PRIMARY KEY ((publisher_id), name, from_date, until_date)
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

CREATE TABLE service_response_code (
  publisher_id text,
  name text,
  from_date timestamp,
  until_date timestamp,
  sample int,
  status_code text,
  count int,
  PRIMARY KEY ((publisher_id), name, from_date, until_date)
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
