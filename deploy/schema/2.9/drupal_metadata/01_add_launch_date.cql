USE impactvizor;

ALTER TABLE drupal_metadata ADD launch_date timestamp;
ALTER TABLE uptime_check_metadata ADD drupal_launch_date timestamp;
