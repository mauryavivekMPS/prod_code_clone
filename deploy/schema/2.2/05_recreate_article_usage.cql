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

ALTER TABLE published_article ADD month_usage_48 int;
ALTER TABLE published_article ADD month_usage_60 int;

ALTER TABLE published_article ADD month_usage_full_03 int;
ALTER TABLE published_article ADD month_usage_full_06 int;
ALTER TABLE published_article ADD month_usage_full_09 int;
ALTER TABLE published_article ADD month_usage_full_12 int;
ALTER TABLE published_article ADD month_usage_full_24 int;
ALTER TABLE published_article ADD month_usage_full_36 int;
ALTER TABLE published_article ADD month_usage_full_48 int;
ALTER TABLE published_article ADD month_usage_full_60 int;

ALTER TABLE published_article ADD month_usage_pdf_03 int;
ALTER TABLE published_article ADD month_usage_pdf_06 int;
ALTER TABLE published_article ADD month_usage_pdf_09 int;
ALTER TABLE published_article ADD month_usage_pdf_12 int;
ALTER TABLE published_article ADD month_usage_pdf_24 int;
ALTER TABLE published_article ADD month_usage_pdf_36 int;
ALTER TABLE published_article ADD month_usage_pdf_48 int;
ALTER TABLE published_article ADD month_usage_pdf_60 int;

ALTER TABLE published_article ADD month_usage_abstract_03 int;
ALTER TABLE published_article ADD month_usage_abstract_06 int;
ALTER TABLE published_article ADD month_usage_abstract_09 int;
ALTER TABLE published_article ADD month_usage_abstract_12 int;
ALTER TABLE published_article ADD month_usage_abstract_24 int;
ALTER TABLE published_article ADD month_usage_abstract_36 int;
ALTER TABLE published_article ADD month_usage_abstract_48 int;
ALTER TABLE published_article ADD month_usage_abstract_60 int;
