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

CREATE TABLE subscriptions (
  id serial primary key,
  email text,
  voter_reg_num integer,

  -- this is in case we want to enable people to subscribe to a full search
  -- rather than an individual voter (in case their friend is not yet
  -- showing up in the db at all):
  search_params jsonb,

  -- whether or not the subscription is active (will come in handy if we send an
  -- email with an unsubscribe link!)
  active boolean,

  subscribe_time timestamp not null default now(),
  last_emailed timestamp
);
CREATE INDEX ON subscriptions (email);