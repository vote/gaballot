# Georgia Ballot Track

## Dev environment

To begin you'll need docker, pipenv, and python 3.7 installed locally to develop ga-track

1. To spin up a Postgres database run `docker-compose up`

2. Load the data into the postgres database

3. In another shell, run `pipenv sync --dev`

4. To start the web app run `pipenv run serve`

## Extras

If you'd like to cleanup the python code formatting, run `pipenv run format`

## Deploying to Heroku

Due to Heroku's poor support for Pipenv, if you change the requirements inside Pipfile you must run `pipenv lock --requirements > requirements.txt`
