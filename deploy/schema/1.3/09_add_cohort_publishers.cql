USE impactvizor;

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'blood_cohort',
  'blood',
  false,
  true,
  {},
  '(blood_cohort) Cohort for American Society of Hematology',
  false,
  ['0887-6924', '0390-6078'],
  '2013-01-01 00:00:00',
  ['b7039396d9f1bc737cbc52a9175aa167'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'blood_cohort', is_cohort=false WHERE publisher_id='blood';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'portland_cohort',
  'portland',
  false,
  true,
  {},
  '(portland_cohort) Cohort for Portland Press',
  false,
  ['0021-9258'],
  '2013-01-01 00:00:00',
  ['dd404f011c7f5f556ead9f8e83d532a7', 'f126c58c77ae7c48cb6a4eac1dc6673b'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'portland_cohort', is_cohort=false WHERE publisher_id='portland';


INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'alphamed_cohort',
  'alphamed',
  false,
  true,
  {},
  '(alphamed_cohort) Cohort for Alphamed Press',
  false,
  ['1527-7755'],
  '2013-01-01 00:00:00',
  ['ea644670597406ffb98d1678a0083640'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'alphamed_cohort', is_cohort=false WHERE publisher_id='alphamed';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'besbjs_cohort',
  'besbjs',
  false,
  true,
  {},
  '(besbjs_cohort) Cohort for British Editorial Society of Bone and Joint Surgery',
  false,
  ['1535-1386', '1432-5195', '1528-1132'],
  '2013-01-01 00:00:00',
  ['2776603f1c0685a8e96c6015085cc37c'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'besbjs_cohort', is_cohort=false WHERE publisher_id='besbjs';


INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'cshl_cohort',
  'cshl',
  false,
  true,
  {},
  '(cshl_cohort) Cohort for British Editorial Society of Bone and Joint Surgery',
  false,
  ['1460-2075'],
  '2013-01-01 00:00:00',
  ['2af8022566753a33fecab8e53544cee4'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'cshl_cohort', is_cohort=false WHERE publisher_id='cshl';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'rup_cohort',
  'rup',
  false,
  true,
  {},
  '(rup_cohort) Cohort for Rockefeller University Press',
  false,
  ['1534-5807', '1476-4679'],
  '2013-01-01 00:00:00',
  ['f3ae3404ff8ee1689bb1499aa89ab74f'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'rup_cohort', is_cohort=false WHERE publisher_id='rup';


INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'aan_cohort',
  'aan',
  false,
  true,
  {},
  '(aan_cohort) Cohort for American Academy of Neurology',
  false,
  ['1460-2083', '1474-7766'],
  '2013-01-01 00:00:00',
  ['fb56ff134b836a85b665d3abb92600cd'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'aan_cohort', is_cohort=false WHERE publisher_id='aan';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'asm_cohort',
  'asm',
  false,
  true,
  {},
  '(asm_cohort) Cohort for American Society for Microbiology',
  false,
  ['1931-3128', '1751-7362', '1553-7374'],
  '2013-01-01 00:00:00',
  ['498009261b692eafd3d13491de58de99'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'asm_cohort', is_cohort=false WHERE publisher_id='asm';


INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'aspb_cohort',
  'aspb',
  false,
  true,
  {},
  '(aspb_cohort) Cohort for American Society of of Plant Biologists',
  false,
  ['2055-0278'],
  '2013-01-01 00:00:00',
  ['498009261b692eafd3d13491de58de99'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'aspb_cohort', is_cohort=false WHERE publisher_id='aspb';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'sfn_cohort',
  'sfn',
  false,
  true,
  {},
  '(sfn_cohort) Cohort for Society for Neuroscience',
  false,
  ['0896-6273'],
  '2013-01-01 00:00:00',
  ['e6910a4734436b05a21c266e14d2ca57'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'sfn_cohort', is_cohort=false WHERE publisher_id='sfn';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'pnas_cohort',
  'pnas',
  false,
  true,
  {},
  '(pnas_cohort) Cohort for Proceedings of the National Academy of Sciences',
  false,
  ['1545-7885'],
  '2013-01-01 00:00:00',
  ['20cb1f6ec93f53749baa7b96611f3555'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'pnas_cohort', is_cohort=false WHERE publisher_id='pnas';

INSERT INTO impactvizor.publisher_metadata (
  publisher_id,
  cohort_owner_publisher_id,
  hw_addl_metadata_available,
  is_cohort,
  issn_to_hw_journal_code,
  name,
  pilot,
  published_articles_issns_to_lookup,
  published_articles_last_updated,
  scopus_api_keys,
  supported_products)
VALUES (
  'asbmb_cohort',
  'asbmb',
  false,
  true,
  {},
  '(asbmb_cohort) Cohort for American Society for Biochemistry and Molecular Biology',
  false,
  ['1362-4962'],
  '2013-01-01 00:00:00',
  ['caa6e88e64850e8c7fd96bfe70897306'],
  ['cohort_articles']);

UPDATE publisher_metadata SET cohort_publisher_id = 'asbmb_cohort', is_cohort=false WHERE publisher_id='asbmb';