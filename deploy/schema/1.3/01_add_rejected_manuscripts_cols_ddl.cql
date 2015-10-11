USE impactvizor;

ALTER TABLE published_article ADD from_rejected_manuscript boolean;
ALTER TABLE published_article ADD rejected_manuscript_id text;
ALTER TABLE published_article ADD rejected_manuscript_editor text;
ALTER TABLE published_article ADD  date_of_rejection timestamp;