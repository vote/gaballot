# DB config
# via https://realpython.com/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    if 'DATABASE_URL' in os.environ:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        SQLALCHEMY_DATABASE_URI = "postgres://postgres:postgres@localhost:5432/gatrack"
    MAIL_SERVER='smtp.sendgrid.net'
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME='apikey'
    MAIL_PASSWORD=os.environ['SENDGRID_API_KEY']
    MAIL_DEFAULT_SENDER='hello@driveturnout.com'
        

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
