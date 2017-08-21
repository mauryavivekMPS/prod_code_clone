USE impactvizor;

CREATE TABLE alert (
  publisher_id text,
  check_id text,
  alert_id uuid,
  name text,
  check_params text,
  enabled boolean,
  PRIMARY KEY ((publisher_id), check_id, alert_id)
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

CREATE INDEX alert_alert_id_index ON alert(alert_id);

CREATE TABLE notification (
  publisher_id text,
  alert_id uuid,
  product_id text,
  pipeline_id text,
  job_id text,
  notification_id uuid,
  values_json text,
  PRIMARY KEY ((publisher_id), alert_id, product_id, pipeline_id, job_id, notification_id)
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

CREATE TABLE notification_summary (
  publisher_id text,
  alert_id uuid,
  product_id text,
  pipeline_id text,
  job_id text,
  notification_summary_id uuid,
  values_list_json text,
  notification_date timestamp,
  dismissed boolean,
  PRIMARY KEY ((publisher_id), alert_id, product_id, pipeline_id, job_id, notification_summary_id)
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

CREATE INDEX notification_summary_notification_id_index ON notification_summary(notification_summary_id);
CREATE INDEX notification_summary_dismissed_index ON notification_summary(dismissed);
