import hashlib
import os

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
    last_emailed = db.Column("last_emailed", db.DateTime())

    @staticmethod
    def secret(data):
        m = hashlib.sha256()
        m.update(os.environ.get('UNSUBSCRIBE_KEY', 'top secret').encode())
        m.update(f'{data}'.encode())
        return m.hexdigest()

    def unsub_url(self, all):
        url = 'https://gaballot.org/unsubscribe'
        if all:
            url += '_all?email='
            data = self.email
        else:
            url += '?sub_id='
            data = self.id
        url += f'{data}&s={Subscription.secret(data)}'
        return url

