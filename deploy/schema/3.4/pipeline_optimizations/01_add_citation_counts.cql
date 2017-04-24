USE impactvizor;

ALTER TABLE published_article_by_cohort ADD scopus_citation_count int;
ALTER TABLE published_article_by_cohort ADD crossref_citation_count int;