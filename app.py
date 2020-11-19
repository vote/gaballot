import logging
import os
from datetime import date

import sentry_sdk
from flask import Flask, make_response, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration
from sqlalchemy.orm.exc import NoResultFound

from analytics import statsd

logging.getLogger().setLevel(logging.INFO)

DEBUG = "APP_SETTINGS" not in os.environ

if not DEBUG:
    sentry_sdk.init(
        "https://1c52ad490a08415fa8e4856e184976f2@o335887.ingest.sentry.io/5522281",
        integrations=[FlaskIntegration()],
    )

app = Flask(__name__)
if DEBUG:
    app.config.from_object("config.DevelopmentConfig")
else:
    app.config.from_object(os.environ["APP_SETTINGS"])

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app, session_options={"autoflush": False})


class VoteRecord(db.Model):
    __tablename__ = "voters_35209_current"

    id = db.Column("Voter Registration #", db.BigInteger, primary_key=True)
    first = db.Column("First Name", db.String())
    last = db.Column("Last Name", db.String())
    middle = db.Column("Middle", db.String())
    city = db.Column("City", db.String())
    county = db.Column("County", db.String())
    application_status = db.Column("Application Status", db.String())
    ballot_status = db.Column("Ballot Status", db.String())
    ballot_style = db.Column("Status Reason", db.String())
    app_date = db.Column("Application Date", db.String())
    issued_date = db.Column("Ballot Issued Date", db.String())
    return_date = db.Column("Ballot Return Date", db.String())

    def friendly_date(self):
        return date.fromisoformat(self.day).strftime("%B %d")

    def friendly_voting_method(self):
        return self.voting_method.lower()


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
            int(request.values["voteid"])
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
                "res-id.html",
                record=record,
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
            VoteRecord.query.filter(VoteRecord.first.like(f"{first}%"))
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
        "error.html",
        msg="Please make sure to fill out all form fields.",
    )


# From: https://stackoverflow.com/a/22336061
@app.template_filter("pluralize")
def pluralize(number, singular="", plural="s"):
    if number == 1:
        return singular
    else:
        return plural


if __name__ == "__main__":
    app.run(debug=DEBUG)
