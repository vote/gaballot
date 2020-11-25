from models import db
from sqlalchemy.sql import func

class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column("id", db.Integer, primary_key=True)
    email = db.Column("email", db.String())
    voter_reg_num = db.Column("voter_reg_num", db.Integer())
    active = db.Column("active", db.Boolean(), default=True)
    search_params = db.Column("search_params", db.JSON())
    subscribe_time = db.Column("subscribe_time", db.DateTime(), default=func.now())

