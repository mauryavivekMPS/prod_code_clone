USE impactvizor;

ALTER TABLE published_article ADD meta_pmid text;
ALTER TABLE published_article ADD meta_actual_ef decimal;
ALTER TABLE published_article ADD meta_actual_citation_count int;
ALTER TABLE published_article ADD meta_predicted_ef decimal;
ALTER TABLE published_article ADD meta_predicted_citation_count int;
ALTER TABLE published_article ADD meta_top_1 int;
ALTER TABLE published_article ADD meta_top_5 int;
ALTER TABLE published_article ADD meta_top_10 int;
ALTER TABLE published_article ADD meta_top_25 int;
ALTER TABLE published_article ADD meta_top_50 int;
ALTER TABLE published_article ADD meta_predicted_tiers int;
ALTER TABLE published_article ADD meta_actual_tiers int;
