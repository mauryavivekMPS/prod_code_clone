USE impactvizor;

ALTER TABLE published_article ADD month_usage_03 int;
ALTER TABLE published_article ADD month_usage_06 int;
ALTER TABLE published_article ADD month_usage_09 int;
ALTER TABLE published_article ADD month_usage_12 int;
ALTER TABLE published_article ADD month_usage_24 int;
ALTER TABLE published_article ADD month_usage_36 int;
ALTER TABLE published_article ADD usage_start_date timestamp;
