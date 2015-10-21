USE impactvizor;

ALTER TABLE publisher_metadata DROP supported_pipelines;
ALTER TABLE publisher_metadata ADD supported_products list<text>;
