USE impactvizor;

ALTER TABLE publisher_metadata ADD supported_pipelines list<text>;
ALTER TABLE publisher_metadata ADD name text;
