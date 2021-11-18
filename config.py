# DB config
# via https://realpython.com/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
import os
import re

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    if 'DATABASE_URL' in os.environ:
        uri = os.environ['DATABASE_URL']
        if uri and uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = uri
    else:
        SQLALCHEMY_DATABASE_URI = "postgres://postgres:postgres@localhost:5432/gatrack"

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
