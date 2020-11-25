import logging
import os

import sentry_sdk
from flask import Flask, make_response, redirect, render_template, request
import jinja2
from sentry_sdk.integrations.flask import FlaskIntegration

from analytics import statsd

from models import db
from models.voters import VoteRecord

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

@app.template_filter('commafy')
def commafy_filter(v):
    return "{:,}".format(v)

def render_template_nocache(template_name, **args):
    resp = make_response(render_template(template_name, **args))
    resp.headers.set("Cache-Control", "private,no-store")
    return resp


@app.route("/")
def index():
    sql = '''
select
    (select count from voter_status_counters_35209
     where "Application Status" = 'A' and "Ballot Status" = 'A')
        as returned_general,
    (select count from voter_status_counters_35211
     where "Application Status" = 'A' and "Ballot Status" = 'A') 
        as returned_special,
    (select count from voter_status_counters_35211
     where "Application Status" = 'A' and "Ballot Status" = 'total') 
        as applied_special,
    (select file_update_time from updated_times
     where election = '35211' order by job_time desc limit 1) 
        as update_time'''
    stats = db.engine.execute(sql).first()

    resp = make_response(render_template("index.html", stats = stats))
    resp.headers.set("Cache-Control", "public, max-age=7200")

    return resp

@app.route("/faq")
def faq():
    resp = make_response(render_template("contact.html"))
    resp.headers.set("Cache-Control", "public, max-age=7200")

    return resp


@app.route("/search", methods=["GET"])
def search():
    if request.values.get("first") and request.values.get("last"):
        statsd.increment("ga.lookup.name")
        logging.info("Handling request by first/last")
        first = request.values["first"].strip().upper().replace(",", "")
        last = request.values["last"].strip().upper().replace(",", "")
        middle = request.values["middle"].strip().upper().replace(",", "")
        county = request.values["county"].strip().upper().replace(",", "")
        city = request.values["city"].strip().upper().replace(",", "")

        records = VoteRecord.lookup(last, first, middle, city, county, 26)

        if len(records) == 0:
            statsd.increment("ga.lookup.no_results")
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
            statsd.increment("ga.lookup.success")
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
