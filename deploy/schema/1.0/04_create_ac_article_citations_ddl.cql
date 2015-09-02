USE impactvizor;

CREATE TABLE article_citations (
  publisher_id text,
  article_doi text,
  citation_doi text,
  article_date_of_publication timestamp,
  citation_count int,
  citation_date timestamp,
  citation_first_author text,
  citation_issue text,
  citation_journal_issn text,
  citation_journal_title text,
  citation_pages text,
  citation_scopus_id text,
  citation_source text,
  citation_title text,
  citation_volume text,
  created timestamp,
  updated timestamp,
  PRIMARY KEY ((publisher_id), article_doi, citation_doi)
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
