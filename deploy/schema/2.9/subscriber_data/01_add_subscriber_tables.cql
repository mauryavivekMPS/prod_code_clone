USE impactvizor;

UPDATE publisher_metadata SET
  supported_products = ['highwire_sites', 'social', 'institutions']
WHERE
  publisher_id = 'hw';

ALTER TABLE publisher_metadata ADD ac_databases list<text>;

CREATE TABLE subscriber (
  publisher_id text,
  membership_no text,
  ac_database text,
  firstname text,
  lastname text,
  inst_name text,
  user_phone text,
  user_fax text,
  user_email text,
  email_domain_srch text,
  user_address text,
  address_2 text,
  title text,
  user_systemname text,
  inst_key text,
  modified_by_dt text,
  subscr_type text,
  subscr_type_desc text,
  ringgold_id text,
  affiliation text,
  user_type text,
  expired boolean,
  num_subscriptions int,
  sales_agent text,
  memo text,
  tier text,
  consortium text,
  start_date timestamp,
  country text,
  region text,
  contact text,
  institution_alternate_name text,
  institution_alternate_identifier text,
  custom1 text,
  custom2 text,
  custom3 text,
  PRIMARY KEY ((publisher_id), membership_no)
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

CREATE INDEX subscriber_membership_no_index ON subscriber(membership_no);

CREATE TABLE subscription (
  publisher_id text,
  membership_no text,
  journal_code text,
  subscr_type_cd text,
  institution_number text,
  ac_database text,
  expiration_dt timestamp,
  subscr_status text,
  last_used_dt timestamp,
  modified_by_dt timestamp,
  product_cd text,
  subscr_type text,
  subscr_type_desc text,
  PRIMARY KEY ((publisher_id), membership_no, journal_code, subscr_type_cd)
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

CREATE TABLE subscriber_values (
  publisher_id text,
  membership_no text,
  source text,
  name text,
  value_text text,
  PRIMARY KEY ((publisher_id), membership_no, source, name)
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
  compression={'sstable_compression': 'LZ4Compressor'};
