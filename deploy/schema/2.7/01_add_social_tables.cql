USE impactvizor;

UPDATE publisher_metadata SET
  supported_products = ['highwire_sites', 'social']
WHERE
  publisher_id = 'hw';

CREATE TABLE altmetrics_social_data (
  doi text,
  altmetrics_id int,
  facebook int,
  blogs int,
  twitter int,
  gplus int,
  news_outlets int,
  wikipedia int,
  video int,
  policy_docs int,
  reddit int,
  PRIMARY KEY ((doi))
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

CREATE TABLE f1000_social_data (
  doi text,
  f1000_id int,
  total_score int,
  num_recommendations int,
  average_score decimal,
  PRIMARY KEY ((doi))
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

ALTER TABLE published_article ADD altmetrics_facebook int;
ALTER TABLE published_article ADD altmetrics_blogs int;
ALTER TABLE published_article ADD altmetrics_twitter int;
ALTER TABLE published_article ADD altmetrics_gplus int;
ALTER TABLE published_article ADD altmetrics_news_outlets int;
ALTER TABLE published_article ADD altmetrics_wikipedia int;
ALTER TABLE published_article ADD altmetrics_video int;
ALTER TABLE published_article ADD altmetrics_policy_docs int;
ALTER TABLE published_article ADD altmetrics_reddit int;
ALTER TABLE published_article ADD f1000_total_score int;
ALTER TABLE published_article ADD f1000_num_recommendations int;
ALTER TABLE published_article ADD f1000_average_score decimal;