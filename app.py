import logging
import os
from datetime import datetime
import math

import sentry_sdk
from flask import Flask, make_response, render_template, request
from sentry_sdk.integrations.flask import FlaskIntegration
import pytz

# from analytics import statsd
from models import db
from models.voters import VoteRecord
from data import statewide_by_party_day

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
db.init_app(app)

COUNTY_ALERTS = {
    # 'FULTON': 'https://example.com',
}


@app.template_filter("commafy")
def commafy_filter(v):
    return "{:,}".format(v)


def render_template_nocache(template_name, **args):
    resp = make_response(render_template(template_name, **args))
    resp.headers.set("Cache-Control", "private,no-store")
    return resp


@app.route("/")
def index():
    election = datetime(2021, 1, 5, tzinfo=pytz.timezone("US/Eastern"))
    days_until_election = math.ceil(
        (election - datetime.now(tz=pytz.timezone("US/Eastern"))).total_seconds()
        / (60 * 60 * 24)
    )

    data = statewide_by_party_day()
    current_data = data['combined'][min(data['combined'].keys())]

    resp = make_response(
        render_template(
            "index.html",
            days_until_election=days_until_election,
            data=data,
            current_data=current_data,
        )
    )
    resp.headers.set("Cache-Control", "public, max-age=900")

    return resp


@app.route("/faq")
def faq():
    resp = make_response(render_template("contact.html"))
    resp.headers.set("Cache-Control", "public, max-age=900")

    return resp


@app.route("/search", methods=["GET"])
def search():
    if request.values.get("first") and request.values.get("last"):
        # statsd.increment("ga.lookup.name")
        logging.info("Handling request by first/last")
        first = request.values["first"].strip().upper().replace(",", "")
        last = request.values["last"].strip().upper().replace(",", "")
        middle = request.values["middle"].strip().upper().replace(",", "")
        county = request.values["county"].strip().upper().replace(",", "")
        city = request.values["city"].strip().upper().replace(",", "")

        records = VoteRecord.lookup(last, first, middle, city, county, 26)

        if len(records) == 0:
            # statsd.increment("ga.lookup.no_results")
            logging.info("Voter ID query by first/last returned no results")
            return render_template_nocache(
                "no-res-name.html",
                first=first,
                middle=middle,
                last=last,
                county=county,
                city=city,
            )
        else:
            # statsd.increment("ga.lookup.success")
            logging.info("Voter ID query by first/last returned results")
            return render_template_nocache(
                "res-name.html",
                first=first,
                middle=middle,
                last=last,
                county=county,
                city=city,
                results=records[:25],
                were_more_records=(len(records) > 25),
                county_alerts=COUNTY_ALERTS,
            )

    logging.info("Invalid request")
    # statsd.increment("ga.lookup.invalid_request")
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
    app.run(debug=DEBUG, host="0.0.0.0")
