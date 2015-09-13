USE impactvizor;

UPDATE publisher_metadata SET crossref_username = 'amersochem', crossref_password = 'crpw966' WHERE publisher_id = 'blood' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'science', crossref_password = 'crpw454' WHERE publisher_id = 'aaas' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'pnas', crossref_password = 'crpw494' WHERE publisher_id = 'pnas' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'rup', crossref_password = 'crpw466' WHERE publisher_id = 'rup' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'lww', crossref_password = 'crpw486' WHERE publisher_id = 'aan' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'jbc', crossref_password = 'crpw044' WHERE publisher_id = 'asbmb' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'aap', crossref_password = 'aap1231' WHERE publisher_id = 'aap' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'aspp', crossref_password = 'crpw304' WHERE publisher_id = 'aspb' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'coldspring', crossref_password = 'crpw684' WHERE publisher_id = 'cshl' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'jbjs', crossref_password = 'jbjs1' WHERE publisher_id = 'besbjs' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'sfn', crossref_password = 'sfn1027' WHERE publisher_id = 'sfn' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'ada', crossref_password = 'ada906' WHERE publisher_id = 'ada' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'asm', crossref_password = 'crpw166' WHERE publisher_id = 'asm' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'alpha', crossref_password = 'alpha616' WHERE publisher_id = 'alphamed' IF EXISTS;
UPDATE publisher_metadata SET crossref_username = 'ppress', crossref_password = 'crpw164' WHERE publisher_id = 'portland' IF EXISTS;