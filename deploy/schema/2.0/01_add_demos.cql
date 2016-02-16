USE impactvizor;

CREATE TABLE demo (
  demo_id uuid,
  name text,
  requestor_id uuid,
  start_date timestamp,
  status text,
  properties text,
  PRIMARY KEY ((demo_id))
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

CREATE INDEX requestor_id_index ON demo (requestor_id);

ALTER TABLE publisher_metadata ADD demo_id text;

CREATE INDEX demo_id_index ON publisher_metadata(demo_id);
