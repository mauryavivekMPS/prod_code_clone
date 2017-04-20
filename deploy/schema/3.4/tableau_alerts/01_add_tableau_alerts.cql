USE impactvizor;

CREATE TABLE tableau_alert (
  alert_id uuid,
  publisher_id text,
  template_id text,
  name text,
  alert_params text,
  alert_filters text,
  attachment_only_emails list<text>,
  full_emails list<text>,
  custom_message text,
  send_with_no_data boolean,
  enabled boolean,
  archived boolean,
  PRIMARY KEY ((publisher_id), template_id, alert_id)
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

CREATE INDEX tableau_alert_alert_id_index ON tableau_alert(alert_id);
CREATE INDEX tableau_alert_archived_index ON tableau_alert(archived);

CREATE TABLE tableau_notification (
  notification_id uuid,
  alert_id uuid,
  publisher_id text,
  template_id text,
  notification_date timestamp,
  expiration_date timestamp,
  name text,
  alert_params text,
  alert_filters text,
  custom_message text,
  PRIMARY KEY ((notification_id))
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

CREATE INDEX tableau_notification_alert_id_index ON tableau_notification(alert_id);

CREATE TABLE workbook_url (
  publisher_id text,
  workbook_id text,
  url text,
  PRIMARY KEY ((publisher_id), workbook_id)
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
