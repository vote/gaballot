-- download 2020.zip from 
-- https://elections.sos.ga.gov/Elections/voterhistory.do
-- unzip it and then run this script.

CREATE TABLE voter_history_2020_raw (data text);
SET client_encoding = 'latin1';
\COPY voter_history_2020_raw FROM '2020.txt';

DELETE FROM voter_history_2020;
INSERT INTO voter_history_2020
  SELECT substring(data, 1, 3)::integer,
    substring(data, 4, 8)::integer,
    substring(data, 12, 8)::date,
    substring(data, 20, 3),
    trim(substring(data, 23, 2)),
    substring(data, 25, 1)::boolean,
    substring(data, 26, 1)::boolean,
    substring(data, 27, 1)::boolean
  FROM voter_history_2020_raw;

DROP TABLE voter_history_raw;