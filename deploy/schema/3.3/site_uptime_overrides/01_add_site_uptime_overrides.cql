USE impactvizor;

CREATE TABLE uptime_override (
  override_id uuid,
  label text,
  start_date timestamp,
  end_date timestamp,
  match_expression_json text,
  override_type text,
  applied_date timestamp,
  notes text,
  PRIMARY KEY ((override_id))
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

ALTER TABLE uptime_check_stat ADD original_avg_response_ms int;
ALTER TABLE uptime_check_stat ADD original_total_up_sec int;
ALTER TABLE uptime_check_stat ADD original_total_down_sec int;
ALTER TABLE uptime_check_stat ADD original_total_unknown_sec int;
ALTER TABLE uptime_check_stat ADD override boolean;
