USE impactvizor;

ALTER TABLE publisher_journal ADD use_benchpress boolean;
CREATE INDEX publisher_journal_use_benchpress_index ON publisher_journal(use_benchpress);
