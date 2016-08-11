USE impactvizor;

ALTER TABLE institution_usage_stat ADD bundle_name text;
ALTER TABLE institution_usage_stat ADD amount decimal;
ALTER TABLE institution_usage_stat ADD trial boolean;
ALTER TABLE institution_usage_stat ADD trial_expiration_date timestamp;
