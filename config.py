# DB config
# via https://realpython.com/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    if 'DATABASE_URL' in os.environ:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
        SECRET_KEY = os.environ['SECRET']
    else:
        SQLALCHEMY_DATABASE_URI = "postgres://postgres:postgres@localhost:5432/postgres"
        SECRET_KEY = 'scramble'

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
