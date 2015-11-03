USE impactvizor;

ALTER TABLE publisher_metadata ADD is_cohort boolean;
ALTER TABLE publisher_metadata ADD cohort_publisher_id text;
ALTER TABLE publisher_metadata ADD cohort_owner_publisher_id text;

ALTER TABLE published_article ADD is_cohort boolean;
ALTER TABLE published_article ADD has_abstract boolean;
