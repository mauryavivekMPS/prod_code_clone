USE impactvizor;

DROP TABLE service_response_time;

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
  minimum bigint,
  maximum bigint,
  percentile_25 bigint,
  percentile_50 bigint,
  percentile_75 bigint,
  percentile_95 bigint,
  percentile_99 bigint,
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
