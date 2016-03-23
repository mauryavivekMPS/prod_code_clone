USE impactvizor;

DROP TABLE article_usage;

CREATE TABLE article_usage (
  publisher_id text,
  article_doi text,
  usage_type text,
  month_number int,
  month_usage int,
  usage_start_date timestamp,
  PRIMARY KEY ((publisher_id), article_doi, usage_type, month_number)
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

ALTER TABLE published_article ADD month_pdf_usage_03 int;
ALTER TABLE published_article ADD month_pdf_usage_06 int;
ALTER TABLE published_article ADD month_pdf_usage_09 int;
ALTER TABLE published_article ADD month_pdf_usage_12 int;
ALTER TABLE published_article ADD month_pdf_usage_24 int;
ALTER TABLE published_article ADD month_pdf_usage_36 int;

ALTER TABLE published_article ADD month_abstract_usage_03 int;
ALTER TABLE published_article ADD month_abstract_usage_06 int;
ALTER TABLE published_article ADD month_abstract_usage_09 int;
ALTER TABLE published_article ADD month_abstract_usage_12 int;
ALTER TABLE published_article ADD month_abstract_usage_24 int;
ALTER TABLE published_article ADD month_abstract_usage_36 int;
