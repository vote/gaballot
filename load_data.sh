#!/bin/sh
# Usage ./load_data.sh ELECTION_NUM
# Assumes there is a file named "env" that sets a DB variable with the psql
# connection string. and that there's a file ELECTION_NUM.zip which is the zip
# downloaded off the GA web site
# https://elections.sos.ga.gov/Elections/voterabsenteefile.do

set -e # stop immediately on error...
clean_up () {
  ARG=$?
  echo "\nCleaning up..."
  rm STATEWIDE.csv
  exit $ARG
}
trap clean_up EXIT

source ./.env

echo "Unzipping STATEWIDE.csv from $1.zip..."
unzip $1.zip STATEWIDE.csv

DATE=`date -r STATEWIDE.csv "+%Y_%m_%d"`
ELECTION=$1
TABLE="voters_${ELECTION}_${DATE}"

echo "Setting up data types (okay if this fails)..."
psql $DATABASE_URL << EOM
CREATE TYPE BallotStyle AS ENUM ('MAILED', 'IN PERSON', 'ELECTRONIC');
EOM

echo "Creating table: $TABLE..."
psql $DATABASE_URL << EOM
DROP TABLE IF EXISTS $TABLE;
CREATE TABLE $TABLE (
  "County" text,
  "Voter Registration #" integer,
  "Last Name" text,
  "First Name" text,
  "Middle Name" text,
  "Suffix" text,
  "Street #" text,
  "Street Name" text,
  "Apt/Unit" text,
  "City" text,
  "State" text,
  "Zip Code" text,
  "Mailing Street #" text,
  "Mailing Street Name" text,
  "Mailing Apt/Unit" text,
  "Mailing City" text,
  "Mailing State" text,
  "Mailing Zip Code" text,
  "Application Status" text,
  "Ballot Status" text,
  "Status Reason" text,
  "Application Date" date,
  "Ballot Issued Date" date,
  "Ballot Return Date" date,
  "Ballot Style" BallotStyle,
  "Ballot Assisted" boolean,
  "Challenged/Provisional" boolean,
  "ID Required" boolean,
  "Municipal Precinct" text,
  "County Precinct" text,
  "CNG" integer,
  "SEN" integer,
  "HOUSE" integer,
  "JUD" text,
  "Combo #" integer,
  "Vote Center ID" integer,
  "Ballot ID" integer,
  "Post #" integer,
  "Party" text
);
EOM

echo "Loading data into table..."

pv STATEWIDE.csv   | # display a progress indicator
  iconv -c -t utf8 | # throw out invalid utf8 characters
  grep -ax '.*'    | # filter out non-ascii stuff altogether since i still had errors after the iconv
  psql $DATABASE_URL -c "COPY $TABLE FROM STDIN DELIMITER ',' CSV HEADER;"

echo "Creating indices..."
psql $DATABASE_URL << EOM
CREATE INDEX ON $TABLE ( "Voter Registration #" );
REFRESH MATERIALIZED VIEW all_voters;
EOM

echo "Updating derived tables (disregard errors about the materialized view already existing)..."
psql $DATABASE_URL << EOM
CREATE OR REPLACE VIEW voters_${ELECTION}_current AS
  SELECT * FROM $TABLE;

-- this will (intentionally) fail if the table already exists
CREATE MATERIALIZED VIEW current_status_${ELECTION} AS 
  SELECT DISTINCT ON("Voter Registration #")
    "Voter Registration #",
    "Application Status",
    "Ballot Status",
    "Status Reason",
    "Application Date",
    "Ballot Issued Date",
    "Ballot Return Date",
    "Ballot Style"
  FROM voters_${ELECTION}_current
  ORDER BY "Voter Registration #",
           "Ballot Status" != 'A', -- sort successful ballots first
           "Ballot Return Date" DESC, -- sort the rest by most recent first
           "Ballot Issued Date" DESC,
           "Application Date" DESC;

REFRESH MATERIALIZED VIEW current_status_${ELECTION}

-- this will (intentionally) fail if the table already exists
CREATE MATERIALIZED VIEW voter_status_counters_$ELECTION AS
  SELECT
    CASE WHEN grouping("Application Status") = 1 THEN 'total' ELSE "Application Status" END AS "Application Status",
    CASE WHEN grouping("Ballot Status") = 1 THEN 'total' ELSE "Ballot Status" END AS "Ballot Status",
    count(1)
  FROM voters_${ELECTION}_current
  GROUP BY ROLLUP ("Application Status", "Ballot Status");

REFRESH MATERIALIZED VIEW voter_status_counters_$ELECTION;

INSERT INTO updated_times VALUES ('$ELECTION', now(), '`date -r STATEWIDE.csv`');
EOM
