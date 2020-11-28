# Georgia Ballot Track

## Dev environment

To begin you'll need docker, pipenv, and python 3.7 installed locally to develop ga-track

1. To spin up a Postgres database run `docker-compose up`

2. Load the data into the postgres database:
    1. Create a copy of `.env.sample` named `.env`, modifying the parameters to connect to your database.
    2. Download the statewide zip files from https://elections.sos.ga.gov/Elections/voterabsenteefile.do for both the November general election (35209.zip) as well as the January runoff (35211.zip).
    3. Type `./db/load_data.sh 35209` to load the general election data, and `./db/load_data.sh 35211` to load the runoff data. (This script can also be used to update the data when a new version of the zip file becomes available.)
    4. Run the SQL commands in `db/init.sql` (this only needs to be done once, after the initial batch of data has been loaded for both elections).

3. In another shell, run `pipenv sync --dev`

4. To start the web app run `pipenv run serve`

## Extras

If you'd like to cleanup the python code formatting, run `pipenv run format`

## Deploying to Heroku

Due to Heroku's poor support for Pipenv, if you change the requirements inside Pipfile you must run `pipenv lock --requirements > requirements.txt`
