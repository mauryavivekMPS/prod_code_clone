USE impactvizor;

ALTER TABLE pipeline_status DROP stop_at_next_task;
ALTER TABLE pipeline_status ADD stop_instruction text;
