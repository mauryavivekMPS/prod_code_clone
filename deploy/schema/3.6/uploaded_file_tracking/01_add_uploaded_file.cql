use impactvizor;

CREATE TABLE uploaded_file (
  publisher_id text,
  uploaded_file_id uuid,
  processed_time timestamp,
  product_id text,
  pipeline_id text,
  job_id text,
  path text,
  user_id uuid,
  PRIMARY KEY ((publisher_id), uploaded_file_id, processed_time)
) WITH
  bloom_filter_fp_chance=0.010000 AND
  caching='KEYS_ONLY' AND
  comment='' AND
  dclocal_read_repair_chance=0.000000 AND
  gc_grace_seconds=864000 AND
  index_interval=128 AND
  read_repair_chance=0.100000 AND
  replicate_on_write='true' AND
  populate_io_cache_on_flush='false' AND
  default_time_to_live=0 AND
  speculative_retry='99.0PERCENTILE' AND
  memtable_flush_period_in_ms=0 AND
  compaction={'class': 'SizeTieredCompactionStrategy'} AND
  compression={'sstable_compression': 'LZ4Compressor'} AND
  CLUSTERING ORDER BY (uploaded_file_id ASC, processed_time DESC);
