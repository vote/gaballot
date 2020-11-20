-- First, run ./load_data.sh 35209 and ./load_data.sh 35211, as suggested in the
-- README. The below SQL creates some additional views/indexes and only needs to
-- be run once, after that is done.

CREATE MATERIALIZED VIEW all_voters AS
  SELECT "First Name", "Middle Name", "Last Name", "County", "City", "Voter Registration #"
  FROM voters_35209_current
  UNION
  SELECT "First Name", "Middle Name", "Last Name", "County", "City", "Voter Registration #"
  FROM voters_35211_current;

CREATE INDEX name_index ON all_voters ("Last Name", "First Name");

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
