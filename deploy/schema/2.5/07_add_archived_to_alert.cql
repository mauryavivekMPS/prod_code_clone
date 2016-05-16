USE impactvizor;

ALTER TABLE alert ADD archived boolean;
CREATE INDEX alert_archived_index ON alert(archived);
