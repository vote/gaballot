up:
	docker-compose up --build

upprod:
	docker-compose -f docker-compose-prod.yml up --build

shell:
	docker-compose exec app bash

pyshell:
	docker-compose exec app ipython

loaddata:
	docker-compose exec app db/load_data.sh ${FILE}

initsql:
	docker-compose exec app bash -c "PGPASSWORD=postgres psql -h postgres -U postgres -d gatrack -f db/init.sql"

lockdeps:
	docker-compose exec app bash -c "pipenv lock --requirements > requirements.txt"

format:
	docker-compose exec app pipenv run format
