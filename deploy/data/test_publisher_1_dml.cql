USE impactvizor;

INSERT INTO impactvizor.publisher_metadata (publisher_id, name, hw_addl_metadata_available, issn_to_hw_journal_code, published_articles_issns_to_lookup, published_articles_last_updated, scopus_api_keys, crossref_username, crossref_password, supported_pipelines)
  VALUES ('test', 'Test Publisher', true, {'1528-0020':'bloodjournal', '0006-4971':'bloodjournal'}, ['1528-0020'], '2010-01-01 00:00:00', ['f5bb1dbcd2f625d729836dfcaf5eb5f1', 'f5bb1dbcd2f625d729836dfcaf5eb5f1'], 'amersochem', 'crpw966', ['published_articles', 'custom_article_data', 'article_citations', 'rejected_article_tracker']);
