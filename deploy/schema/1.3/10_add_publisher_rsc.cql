USE impactvizor;

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  hw_addl_metadata_available,
  issn_to_hw_journal_code,
  name,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products,
  pilot)
VALUES (
  'rsc',
  false,
  {},
  'Royal Society of Chemistry',
  ['2041-6539'],
  '2014-03-01 00:00:00',
  ['ea644670597406ffb98d1678a0083640'],
  ['rejected_article_tracker'],
  true);
