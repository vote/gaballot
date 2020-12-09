FROM python:3.7

RUN pip install pipenv && \
  apt-get update && \
  apt-get install pv lsb-release -y && \
  sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
  sh -c 'wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -' && \
  apt-get update && \
  apt-get -y install postgresql-client-12

RUN mkdir /app
WORKDIR /app

ADD Pipfile /app/Pipfile
ADD Pipfile.lock /app/Pipfile.lock

RUN pipenv install --dev

CMD pipenv run serve
