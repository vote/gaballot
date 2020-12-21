-- First, run ./load_data.sh 35209 and ./load_data.sh 35211, as suggested in the
-- README. The below SQL creates some additional views/indexes and only needs to
-- be run once, after that is done.

CREATE MATERIALIZED VIEW IF NOT EXISTS all_voters AS
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
CREATE UNIQUE INDEX IF NOT EXISTS name_index ON all_voters (
  "Last Name", "First Name", "Middle Name", "County", "City", "Voter Registration #"
);

CREATE INDEX IF NOT EXISTS voter_reg_index ON all_voters ("Voter Registration #");

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

CREATE TABLE IF NOT EXISTS updated_times (
  election text,
  job_time timestamp,
  file_update_time timestamp
);


CREATE MATERIALIZED VIEW IF NOT EXISTS stats_by_county_day AS
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

CREATE UNIQUE INDEX IF NOT EXISTS stats_by_county_index ON stats_by_county_day (county, days_before);
CREATE INDEX IF NOT EXISTS stats_by_day_index ON stats_by_county_day (days_before);

CREATE MATERIALIZED VIEW IF NOT EXISTS stats_by_county_day AS
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
    SELECT DISTINCT ON ("Voter Registration #")
      "Application Date" as date,
      ('2020-11-03' - "Application Date") as days_before,
      'apply_general' as what,
      "County",
      "Voter Registration #",
      "Application Status",
      "Ballot Status",
      "Status Reason",
      "Application Date",
      "Ballot Issued Date",
      "Ballot Return Date",
      "Ballot Style"
    FROM voters_35209_current
    ORDER BY "Voter Registration #",
            "Application Status" != 'A', -- sort successful applications first
            "Application Date" -- look for the EARLIEST application
  ) UNION ALL (
    SELECT "Ballot Return Date" as date,
      ('2020-11-03' - "Ballot Return Date") as days_before,
      'return_general' as what, *
    FROM current_status_35209
  ) UNION ALL (
    SELECT DISTINCT ON ("Voter Registration #")
      "Application Date" as date,
      ('2021-01-05' - "Application Date") as days_before,
      'apply_special' as what,
      "County",
      "Voter Registration #",
      "Application Status",
      "Ballot Status",
      "Status Reason",
      "Application Date",
      "Ballot Issued Date",
      "Ballot Return Date",
      "Ballot Style"
    FROM voters_35211_current
    ORDER BY "Voter Registration #",
            "Application Status" != 'A', -- sort successful applications first
            "Application Date" -- look for the EARLIEST application
  ) UNION ALL (
    SELECT "Ballot Return Date" as date,
      ('2021-01-05' - "Ballot Return Date") as days_before,
      'return_special' as what, *
    FROM current_status_35211
  )
) q
GROUP BY county, days_before
ORDER BY days_before DESC;

CREATE UNIQUE INDEX IF NOT EXISTS  stats_by_county_index ON stats_by_county_day (county, days_before);
CREATE INDEX IF NOT EXISTS  stats_by_day_index ON stats_by_county_day (days_before);

CREATE OR REPLACE VIEW cumulative_stats_by_day AS
  SELECT * FROM (
    SELECT DISTINCT ON (days_before)
      days_before,
      sum(applied_general) OVER w AS applied_general,
      sum(mailed_general) OVER w AS mailed_general,
      sum(in_person_general) OVER w AS in_person_general,
      sum(total_returned_general) OVER w AS total_returned_general,
      sum(applied_special) OVER w AS applied_special,
      sum(mailed_special) OVER w AS mailed_special,
      sum(in_person_special) OVER w AS in_person_special,
      sum(total_returned_special) OVER w AS total_returned_special
    FROM stats_by_county_day
    WINDOW w AS (ORDER BY days_before DESC)
    ORDER BY days_before DESC
  ) q
  WHERE days_before <= 90 AND days_before >= 0;

CREATE OR REPLACE VIEW cumulative_stats_by_county AS
  SELECT * FROM (
    SELECT days_before, county,
      sum(applied_general) OVER w AS applied_general,
      sum(mailed_general) OVER w AS mailed_general,
      sum(in_person_general) OVER w AS in_person_general,
      sum(total_returned_general) OVER w AS total_returned_general,
      sum(applied_special) OVER w AS applied_special,
      sum(mailed_special) OVER w AS mailed_special,
      sum(in_person_special) OVER w AS in_person_special,
      sum(total_returned_special) OVER w AS total_returned_special
    FROM stats_by_county_day
    WINDOW w AS (PARTITION BY county ORDER BY days_before DESC)
    ORDER BY days_before DESC
  ) q
  WHERE days_before <= 90 AND days_before >= 0;

-- these statements are not idempotent
--INSERT INTO updated_times VALUES ('35209', now(), now());
--INSERT INTO updated_times VALUES ('35211', now(), now());

CREATE TABLE IF NOT EXISTS voter_history_2020 (
  "County" integer,
  "Voter Registration #" integer,
  "Election Date" date,
  "Election Type" varchar(3),
  "Party" varchar(2),
  "Absentee" boolean,
  "Provisional" boolean,
  "Supplemental" boolean
);
CREATE INDEX IF NOT EXISTS voter_history_reg_idx
  ON voter_history_2020 ("Voter Registration #");

CREATE MATERIALIZED VIEW IF NOT EXISTS stats_by_county_party_day AS
SELECT "County" as county, party, days_before,
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
    SELECT DISTINCT ON ("Voter Registration #")
      "Application Date" as date,
      ('2020-11-03' - "Application Date") as days_before,
      'apply_general' as what,
      "County",
      "Voter Registration #",
      "Application Status",
      "Ballot Status",
      "Status Reason",
      "Application Date",
      "Ballot Issued Date",
      "Ballot Return Date",
      "Ballot Style"
    FROM voters_35209_current
    ORDER BY "Voter Registration #",
            "Application Status" != 'A', -- sort successful applications first
            "Application Date" -- look for the EARLIEST application
  ) UNION ALL (
    SELECT "Ballot Return Date" as date,
      ('2020-11-03' - "Ballot Return Date") as days_before,
      'return_general' as what, *
    FROM current_status_35209
  ) UNION ALL (
    SELECT DISTINCT ON ("Voter Registration #")
      "Application Date" as date,
      ('2021-01-05' - "Application Date") as days_before,
      'apply_special' as what,
      "County",
      "Voter Registration #",
      "Application Status",
      "Ballot Status",
      "Status Reason",
      "Application Date",
      "Ballot Issued Date",
      "Ballot Return Date",
      "Ballot Style"
    FROM voters_35211_current
    ORDER BY "Voter Registration #",
            "Application Status" != 'A', -- sort successful applications first
            "Application Date" -- look for the EARLIEST application
  ) UNION ALL (
    SELECT "Ballot Return Date" as date,
      ('2021-01-05' - "Ballot Return Date") as days_before,
      'return_special' as what, *
    FROM current_status_35211
  )
) q1 LEFT JOIN (
  SELECT DISTINCT ON("Voter Registration #")
    "Voter Registration #", "Party" as party
  FROM voter_history_2020
  WHERE "Party" != ''
  ORDER BY "Voter Registration #", "Election Date" DESC
) q2 using ("Voter Registration #")
GROUP BY county, party, days_before
ORDER BY days_before DESC;

CREATE UNIQUE INDEX IF NOT EXISTS stats_by_party_county_index ON stats_by_county_party_day (party, county, days_before);
CREATE INDEX IF NOT EXISTS stats_by_day_party_index ON stats_by_county_party_day (days_before);

CREATE OR REPLACE VIEW cumulative_stats_by_party_day AS
  SELECT * FROM (
    SELECT DISTINCT ON (party, days_before)
      party, days_before,
      sum(applied_general) OVER w AS applied_general,
      sum(mailed_general) OVER w AS mailed_general,
      sum(in_person_general) OVER w AS in_person_general,
      sum(total_returned_general) OVER w AS total_returned_general,
      sum(applied_special) OVER w AS applied_special,
      sum(mailed_special) OVER w AS mailed_special,
      sum(in_person_special) OVER w AS in_person_special,
      sum(total_returned_special) OVER w AS total_returned_special
    FROM stats_by_county_party_day
    WINDOW w AS (PARTITION BY party ORDER BY days_before DESC)
    ORDER BY days_before DESC
  ) q
  WHERE days_before <= 90 AND days_before >= 0;