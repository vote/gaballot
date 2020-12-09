-- First, run ./load_data.sh 35209 and ./load_data.sh 35211, as suggested in the
-- README. The below SQL creates some additional views/indexes and only needs to
-- be run once, after that is done.

CREATE MATERIALIZED VIEW all_voters AS
  SELECT "First Name", "Middle Name", "Last Name", "County", "City", "Voter Registration #"
  FROM voters_35209_current
  UNION
  SELECT "First Name", "Middle Name", "Last Name", "County", "City", "Voter Registration #"
  FROM voters_35211_current;

-- CREATE INDEX name_index ON all_voters ("Last Name", "First Name");

-- this is kind of dumb but in order to make the materialized view refresh be
-- concurrent, postgres requires a unique index on the table. we need to include
-- every column to guarantee uniqueness. in practice we'll only use the first
-- two.
CREATE UNIQUE INDEX name_index ON all_voters (
  "Last Name", "First Name", "Middle Name", "County", "City", "Voter Registration #"
);

CREATE INDEX voter_reg_index ON all_voters ("Voter Registration #");

CREATE OR REPLACE VIEW voters_and_statuses AS
SELECT v.*,
         a."Application Status" as "Old App Status", a."Ballot Status" as "Old Ballot Status",
         a."Status Reason" as "Old Status Reason",
         a."Application Date" as "Old App Date", a."Ballot Issued Date" as "Old Issued Date",
         a."Ballot Return Date" as "Old Return Date", a."Ballot Style" as "Old Ballot Style",
         b."Application Status" as "New App Status", b."Ballot Status" as "New Ballot Status",
         b."Status Reason" as "New Status Reason",
         b."Application Date" as "New App Date", b."Ballot Issued Date" as "New Issued Date",
         b."Ballot Return Date" as "New Return Date", b."Ballot Style" as "New Ballot Style"
FROM all_voters v
  LEFT JOIN current_status_35209 a USING ("Voter Registration #")
  LEFT JOIN current_status_35211 b USING ("Voter Registration #");

CREATE TABLE updated_times (
  election text,
  job_time timestamp,
  file_update_time timestamp
);


CREATE MATERIALIZED VIEW stats_by_county_day AS
SELECT "County" as county, days_before,
  sum(("Application Status" = 'A' AND
        what = 'apply_general')::integer) as applied_general,
  sum(("Ballot Status" = 'A' AND
        what = 'return_general' AND
        "Ballot Style" = 'MAILED')::integer) as mailed_general,
  sum(("Ballot Status" = 'A' AND
        what = 'return_general' AND
        "Ballot Style" = 'IN PERSON')::integer) as in_person_general,
  sum(("Ballot Status" = 'A' AND
        what = 'return_general')::integer) as total_returned_general,
  sum(("Application Status" = 'A' AND
        what = 'apply_special')::integer) as applied_special,
  sum(("Ballot Status" = 'A' AND
        what = 'return_special' AND
        "Ballot Style" = 'MAILED')::integer) as mailed_special,
  sum(("Ballot Status" = 'A' AND
        what = 'return_special' AND
        "Ballot Style" = 'IN PERSON')::integer) as in_person_special,
  sum(("Ballot Status" = 'A' AND
        what = 'return_special')::integer) as total_returned_special
FROM (
  (
    SELECT "Application Date" as date,
      ('2020-11-03' - "Application Date") as days_before,
      'apply_general' as what, *
    FROM current_status_35209
  ) UNION ALL (
    SELECT "Ballot Return Date" as date,
      ('2020-11-03' - "Ballot Return Date") as days_before,
      'return_general' as what, *
    FROM current_status_35209
  ) UNION ALL (
    SELECT "Application Date" as date,
      ('2021-01-05' - "Application Date") as days_before,
      'apply_special' as what, *
    FROM current_status_35211
  ) UNION ALL (
    SELECT "Ballot Return Date" as date,
      ('2021-01-05' - "Ballot Return Date") as days_before,
      'return_special' as what, *
    FROM current_status_35211
  )
) q
GROUP BY county, days_before
ORDER BY days_before DESC;

CREATE UNIQUE INDEX stats_by_county_index ON stats_by_county_day (county, days_before);
CREATE INDEX stats_by_day_index ON stats_by_county_day (days_before);

INSERT INTO updated_times VALUES ('35209', now(), now());
INSERT INTO updated_times VALUES ('35211', now(), now());
