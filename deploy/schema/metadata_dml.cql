USE impactvizor;

INSERT INTO impactvizor.publisher_metadata (publisher_id, hw_addl_metadata_available, issn_to_hw_journal_code, published_articles_issns_to_lookup, published_articles_last_updated, scopus_api_key)
  VALUES ('blood', true, {'1528-0020':'bloodjournal', '0006-4971':'bloodjournal'}, ['1528-0020'], '2010-01-01 00:00:00', '654944b76e7d0b335f11a187a6703d24');


INSERT INTO impactvizor.publisher_metadata (publisher_id, hw_addl_metadata_available, issn_to_hw_journal_code, published_articles_issns_to_lookup, published_articles_last_updated, scopus_api_key)
  VALUES ('aan', true, {'0028-3878':'neurology', '1526-632X':'neurology'}, ['0028-3878'], '2010-01-01 00:00:00', 'd8d7734d85f882727ccb7ab9c6db2c9e');

INSERT INTO impactvizor.publisher_metadata (publisher_id, hw_addl_metadata_available, issn_to_hw_journal_code, published_articles_issns_to_lookup, published_articles_last_updated, scopus_api_key)
  VALUES ('test', true, {'1528-0020':'bloodjournal', '0006-4971':'bloodjournal'}, ['1528-0020'], '2010-01-01 00:00:00', '654944b76e7d0b335f11a187a6703d24');
