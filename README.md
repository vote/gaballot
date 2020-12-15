# Georgia Ballot Track

## Dev environment

To start up the dev environment, run `make up`.

The dev server will be running on `http://localhost:5050`.

After pulling new code, if the SQL schema has changed, run `make initsql` to migrate the database.

### Loading data

1. Download the statewide zip files from https://elections.sos.ga.gov/Elections/voterabsenteefile.do for both the November general election (35209.zip) as well as the January runoff (35211.zip). Place these two zip files in the root of this repo.

2. Run `make loaddata FILE=35209` and then `make loaddata FILE=35211`. Note that the first time you run these, you'll see a couple errors about "relation does not exist". That's OK.

3. Run `make initsql`.

To refresh the data, download and replace those two zip files, then run step 2 and 3 again.

## Extras

If you'd like to cleanup the python code formatting, run `make format`

## Deploying to Heroku

Due to Heroku's poor support for Pipenv, if you change the requirements inside Pipfile you must run `make lockdeps` to update `requirements.txt`.
