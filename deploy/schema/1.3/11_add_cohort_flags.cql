USE impactvizor;

ALTER TABLE publisher_metadata DROP is_cohort;
ALTER TABLE publisher_metadata DROP cohort_publisher_id;
ALTER TABLE publisher_metadata DROP cohort_owner_publisher_id;

ALTER TABLE publisher_metadata ADD cohort_articles_issns_to_lookup list<text>;
ALTER TABLE publisher_metadata ADD cohort_articles_last_updated timestamp;
ALTER TABLE publisher_metadata ADD has_cohort boolean;

ALTER TABLE article_citations ADD is_cohort boolean;
CREATE INDEX published_article_is_cohort_index ON published_article (is_cohort);
CREATE INDEX article_citations_is_cohort_index ON article_citations (is_cohort);

DELETE FROM publisher_metadata WHERE publisher_id='blood_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='portland_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='alphamed_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='besbjs_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='cshl_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='rup_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='aan_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='asm_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='aspb_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='sfn_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='pnas_cohort';
DELETE FROM publisher_metadata WHERE publisher_id='asbmb_cohort';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['0887-6924', '0390-6078'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['b7039396d9f1bc737cbc52a9175aa167']
WHERE publisher_id='blood';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['0021-9258'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['dd404f011c7f5f556ead9f8e83d532a7', 'f126c58c77ae7c48cb6a4eac1dc6673b']
WHERE publisher_id='portland';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1527-7755'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['ea644670597406ffb98d1678a0083640']
WHERE publisher_id='alphamed';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['0021-9355', '1432-5195', '1528-1132'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['2776603f1c0685a8e96c6015085cc37c']
WHERE publisher_id='besbjs';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1460-2075', '1097-2765'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['2af8022566753a33fecab8e53544cee4']
WHERE publisher_id='cshl';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1534-5807', '1476-4679'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['f3ae3404ff8ee1689bb1499aa89ab74f']
WHERE publisher_id='rup';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1460-2083', '1474-7766', '0165-5728'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['fb56ff134b836a85b665d3abb92600cd']
WHERE publisher_id='aan';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['2168-6203'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['0e6e0e55c294b272fccc322d432a20df']
WHERE publisher_id='aap';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1931-3128', '1751-7362', '1553-7374', '0950-382X'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['498009261b692eafd3d13491de58de99']
WHERE publisher_id='asm';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['2055-0278'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['22b45a23f167bfc719a24e61a6ed09f2']
WHERE publisher_id='aspb';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['0896-6273'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['e6910a4734436b05a21c266e14d2ca57']
WHERE publisher_id='sfn';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1545-7885'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['20cb1f6ec93f53749baa7b96611f3555']
WHERE publisher_id='pnas';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1362-4962'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['caa6e88e64850e8c7fd96bfe70897306']
WHERE publisher_id='asbmb';

UPDATE publisher_metadata SET
  has_cohort=true,
  cohort_articles_last_updated='2013-01-01 00:00:00',
  cohort_articles_issns_to_lookup=['1945-7170', '1945-7197'],
  supported_products=supported_products + ['cohort_articles'],
  scopus_api_keys = scopus_api_keys + ['825df60475f266dd5abb6cfd48c88710']
WHERE publisher_id='ada';