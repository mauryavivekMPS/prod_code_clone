USE impactvizor;

CREATE TABLE rejected_articles (
  publisher_id text,
  rejected_article_id timeuuid,
  article_type text,
  authors_match_score decimal,
  citation_lookup_status text,
  citations int,
  co_authors text,
  corresponding_author text,
  created timestamp,
  crossref_doi text,
  crossref_match_score decimal,
  custom text,
  date_of_publication timestamp,
  date_of_rejection timestamp,
  editor text,
  first_author text,
  keywords text,
  manuscript_id text,
  manuscript_title text,
  published_co_authors text,
  published_first_author text,
  published_journal text,
  published_journal_issn text,
  published_publisher text,
  published_title text,
  reject_reason text,
  scopus_doi_status text,
  scopus_id text,
  source_file_name text,
  status text,
  subject_category text,
  submitted_journal text,
  updated timestamp,
  PRIMARY KEY ((publisher_id), rejected_article_id)
) WITH
  bloom_filter_fp_chance=0.010000 AND
  caching='KEYS_ONLY' AND
  comment='' AND
  dclocal_read_repair_chance=0.000000 AND
  gc_grace_seconds=86400 AND
  index_interval=128 AND
  read_repair_chance=0.100000 AND
  replicate_on_write='true' AND
  populate_io_cache_on_flush='false' AND
  default_time_to_live=0 AND
  speculative_retry='99.0PERCENTILE' AND
  memtable_flush_period_in_ms=0 AND
  compaction={'class': 'SizeTieredCompactionStrategy'} AND
  compression={'sstable_compression': 'LZ4Compressor'};

CREATE INDEX manuscript_id_index ON rejected_articles (manuscript_id);

CREATE INDEX submmited_journal_index ON rejected_articles (submitted_journal);
