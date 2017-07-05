USE impactvizor;

ALTER TABLE tableau_alert ADD created_by uuid;

CREATE INDEX tableau_alert_created_by_index ON tableau_alert(created_by);

