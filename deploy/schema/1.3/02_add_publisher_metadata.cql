USE impactvizor;

ALTER TABLE publisher_metadata ADD supported_pipelines list<text>;
ALTER TABLE publisher_metadata ADD name text;

UPDATE publisher_metadata SET name = 'American Society of Hematology (blood)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'blood';
UPDATE publisher_metadata SET name = 'American Association for the Advancement of Science (aaas)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'aaas';
UPDATE publisher_metadata SET name = 'Proceedings of the National Academy of Sciences (pnas)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'pnas';
UPDATE publisher_metadata SET name = 'Rockefeller University Press (rup)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'rup';
UPDATE publisher_metadata SET name = 'American Academy of Neurology (aan)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'aan';
UPDATE publisher_metadata SET name = 'American Society for Biochemistry and Molecular Biology (asbmb)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'asbmb';
UPDATE publisher_metadata SET name = 'American Academy of Pediatrics (aap)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'aap';
UPDATE publisher_metadata SET name = 'American Society of of Plant Biologists (aspb)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'aspb';
UPDATE publisher_metadata SET name = 'Cold Spring Harbor Laboratory (cshl)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'cshl';
UPDATE publisher_metadata SET name = 'British Editorial Society of Bone and Joint Surgery (besbjs)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'besbjs';
UPDATE publisher_metadata SET name = 'Society for Neuroscience (sfn)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'sfn';
UPDATE publisher_metadata SET name = 'American Diabetes Association (ada)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'ada';
UPDATE publisher_metadata SET name = 'American Society for Microbiology (asm)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'asm';
UPDATE publisher_metadata SET name = 'AlphaMed Press (alphamed)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'alphamed';
UPDATE publisher_metadata SET name = 'Portland Press (portland)', supported_pipelines=['rejected_article_tracker', 'published_articles', 'article_citations', 'custom_article_data'] WHERE publisher_id = 'portland';
