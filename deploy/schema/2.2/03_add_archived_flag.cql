USE impactvizor;

ALTER TABLE publisher_metadata ADD archived boolean;
CREATE INDEX publisher_archived_index ON publisher_metadata(archived);

ALTER TABLE demo ADD archived boolean;
CREATE INDEX demo_archived_index ON demo(archived);