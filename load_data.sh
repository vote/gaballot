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

source ./env

echo "Unzipping STATEWIDE.csv from $1.zip..."
unzip $1.zip STATEWIDE.csv

DATE=`date -r STATEWIDE.csv "+%Y_%m_%d"`
ELECTION=$1
TABLE="voters_${ELECTION}_${DATE}"

echo "Setting up data types (okay if this fails)..."
psql $DB << EOM
CREATE TYPE BallotStyle AS ENUM ('MAILED', 'IN PERSON', 'ELECTRONIC');
EOM

echo "Creating table: $TABLE..."
psql $DB << EOM
DROP TABLE IF EXISTS $TABLE;
CREATE TABLE $TABLE (
  "County" varchar(20),
  "Voter Registration #" integer,
  "Last Name" varchar(30),
  "First Name" varchar(30),
  "Middle Name" varchar(30),
  "Suffix" varchar(10),
  "Street #" varchar(20),
  "Street Name" varchar,
  "Apt/Unit" varchar(20),
  "City" varchar(30),
  "State" varchar(2),
  "Zip Code" varchar(12),
  "Mailing Street #" varchar(20),
  "Mailing Street Name" varchar,
  "Mailing Apt/Unit" varchar(20),
  "Mailing City" varchar(30),
  "Mailing State" varchar(2),
  "Mailing Zip Code" varchar(12),
  "Application Status" varchar(1),
  "Ballot Status" varchar(1),
  "Status Reason" text,
  "Application Date" date,
  "Ballot Issued Date" date,
  "Ballot Return Date" date,
  "Ballot Style" BallotStyle,
  "Ballot Assisted" boolean,
  "Challenged/Provisional" boolean,
  "ID Required" boolean,
  "Municipal Precinct" varchar(6),
  "County Precinct" varchar(6),
  "CNG" integer,
  "SEN" integer,
  "HOUSE" integer,
  "JUD" varchar(6),
  "Combo #" integer,
  "Vote Center ID" integer,
  "Ballot ID" integer,
  "Post #" integer,
  "Party" varchar(2)
);
EOM

echo "Loading data into table..."

pv STATEWIDE.csv   | # display a progress indicator
  iconv -c -t utf8 | # throw out invalid utf8 characters
  grep -ax '.*'    | # filter out non-ascii stuff altogether since i still had errors after the iconv
  psql $DB -c "COPY $TABLE FROM STDIN DELIMITER ',' CSV HEADER;"

echo "Creating indices..."
psql $DB << EOM
CREATE INDEX ON $TABLE ( "Last Name", "First Name" );
CREATE INDEX ON $TABLE ( "Voter Registration #" );
EOM

echo "Updating rollup stats (disregard errors about the materialized view already existing)..."
psql $DB << EOM
CREATE OR REPLACE VIEW voters_${ELECTION}_current AS
  SELECT * FROM $TABLE;

-- this will (intentionally) fail if the table already exists
CREATE MATERIALIZED VIEW voter_status_counters_$ELECTION AS 
  SELECT
    CASE WHEN grouping("Application Status") = 1 THEN 'total' ELSE "Application Status" END AS "Application Status",
    CASE WHEN grouping("Ballot Status") = 1 THEN 'total' ELSE "Ballot Status" END AS "Ballot Status",
    count(1)
  FROM voters_${ELECTION}_current
  GROUP BY ROLLUP ("Application Status", "Ballot Status");

REFRESH MATERIALIZED VIEW voter_status_counters_$ELECTION;
EOM
