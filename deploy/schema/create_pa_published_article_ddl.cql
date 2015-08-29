USE impactvizor;

CREATE TABLE published_article (
  publisher_id text,
  article_doi text,
  article_issue text,
  article_journal text,
  article_journal_issn text,
  article_pages text,
  article_publisher text,
  article_scopus_id text,
  article_title text,
  article_type text,
  article_volume text,
  citations_lookup_error boolean,
  citations_updated_on timestamp,
  co_authors text,
  created timestamp,
  custom text,
  date_of_publication timestamp,
  editor text,
  first_author text,
  hw_metadata_retrieved boolean,
  scopus_citation_count int,
  subject_category text,
  updated timestamp,
  PRIMARY KEY ((publisher_id), article_doi)
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


  ALTER TABLE impactvizor.published_article ADD is_open_access text;
