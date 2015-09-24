USE impactvizor;

ALTER TABLE publisher_metadata ADD supported_pipelines list<text>;
CREATE INDEX ON publisher_metadata (supported_pipelines);

ALTER TABLE publisher_metadata ADD name text;
