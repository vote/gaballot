import json
import os
import logging
from datetime import date

from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from analytics import statsd

logging.getLogger().setLevel(logging.INFO)

sentry_sdk.init(
    "https://1c52ad490a08415fa8e4856e184976f2@o335887.ingest.sentry.io/5522281",
    integrations=[FlaskIntegration()],
)

app = Flask(__name__)
if "APP_SETTINGS" in os.environ:
    app.config.from_object(os.environ["APP_SETTINGS"])
else:
    app.config.from_object("config.DevelopmentConfig")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app, session_options={"autoflush": False})

"""
class VoteRecord(db.Model):
    __tablename__ = "vote_records"

    __table_args__ = (
        db.Index(
            "first_trgm_idx",
            "first",
            postgresql_ops={"first": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        db.Index(
            "last_trgm_idx",
            "last",
            postgresql_ops={"last": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    first = db.Column(db.String(), index=True)
    last = db.Column(db.String(), index=True)
    middle = db.Column(db.String(), index=True)
    city = db.Column(db.String(), index=True)
    county = db.Column(db.String(), index=True)
    day = db.Column(db.String(), index=True)
    voting_method = db.Column("VOTING_METHOD", db.String())

    def __init__(self, id, name, county, precinct, day):
        self.id = id
        self.name = name
        self.first = name.split(",")[1].strip()
        self.last = name.split(",")[0].strip()
        self.county = county
        self.precinct = precinct
        self.day = day

    def friendly_date(self):
        return date.fromisoformat(self.day).strftime("%B %d")

    def friendly_voting_method(self):
        return self.voting_method.lower()


db.create_all()
db.session.commit()
"""

def render_template_nocache(template_name, **args):
    resp = make_response(render_template(template_name, **args))
    resp.headers.set("Cache-Control", "private,no-store")
    return resp


@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    resp.headers.set("Cache-Control", "public, max-age=7200")

    return resp

@app.route("/faq")
def faq():
    resp = make_response(render_template("contact.html"))
    resp.headers.set("Cache-Control", "public, max-age=7200")

    return resp


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method != "POST":
        return redirect("/")

    if request.values.get("voteid"):
        statsd.increment("ga.lookup.voter_id")
        logging.info("Handling request by Voter ID")

        try:
            voteid = int(request.values["voteid"])
        except ValueError:
            logging.info(f"Invalid voteid: {request.values['voteid']}")
            return render_template_nocache(
                "error.html",
                msg="Invalid voter ID. Please make sure you enter a 10-digit number.",
            )

        try:
            record = VoteRecord.query.filter_by(id=int(request.values["voteid"])).one()
            statsd.increment("ga.lookup.success")
            logging.info("Voter ID query returned a result")
            return render_template_nocache(
                "res-id.html", record=record,
            )
        except NoResultFound:
            statsd.increment("ga.lookup.no_results")
            logging.info("Voter ID query returned no result")
            return render_template_nocache(
                "no-res-id.html", voter_id=request.values["voteid"]
            )
    elif (
        request.values.get("first")
        and request.values.get("last")
        and request.values.get("county")
    ):
        statsd.increment("ga.lookup.name_county")
        logging.info("Handling request by first/last/county")
        first = request.values["first"].strip().upper().replace(",", "")
        last = request.values["last"].strip().upper().replace(",", "")
        county = request.values["county"].upper()

        records = (
            VoteRecord.query.filter_by(county=county)
            .filter(VoteRecord.first.like(f"{first}%"))
            .filter(VoteRecord.last.like(f"{last}%"))
            .order_by(VoteRecord.last, VoteRecord.first)
            .limit(26)
            .all()
        )

        if len(records) == 0:
            statsd.increment("ga.lookup.no_results")
            logging.info("Voter ID query by first/last/county returned no results")
            return render_template_nocache(
                "no-res-name.html",
                first=first,
                last=last,
                county=county,
            )
        else:
            statsd.increment("ga.lookup.success")
            logging.info("Voter ID query by first/last/county returned results")
            return render_template_nocache(
                "res-name.html",
                first=first,
                last=last,
                county=county,
                results=records[:25],
                were_more_records=(len(records) > 25),
            )

    logging.info("Invalid request")
    statsd.increment("ga.lookup.invalid_request")
    return render_template_nocache(
        "error.html", msg="Please make sure to fill out all form fields.",
    )


# From: https://stackoverflow.com/a/22336061
@app.template_filter("pluralize")
def pluralize(number, singular="", plural="s"):
    if number == 1:
        return singular
    else:
        return plural


if __name__ == "__main__":
    app.run(debug=True)
