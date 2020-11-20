import logging
import os

import sentry_sdk
from flask import Flask, make_response, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration

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
    __tablename__ = "voters_and_statuses"

    id = db.Column("Voter Registration #", db.BigInteger, primary_key=True)
    first = db.Column("First Name", db.String())
    last = db.Column("Last Name", db.String())
    middle = db.Column("Middle Name", db.String())
    city = db.Column("City", db.String())
    county = db.Column("County", db.String())

    general_app_status = db.Column("Old App Status", db.String())
    general_ballot_status = db.Column("Old Ballot Status", db.String())
    general_status_reason = db.Column("Old Status Reason", db.String())
    general_app_date = db.Column("Old App Date", db.String())
    general_issue_date = db.Column("Old Issued Date", db.String())
    general_return_date = db.Column("Old Return Date", db.String())
    general_ballot_style = db.Column("Old Ballot Style", db.String())

    special_app_status = db.Column("New App Status", db.String())
    special_ballot_status = db.Column("New Ballot Status", db.String())
    special_status_reason = db.Column("New Status Reason", db.String())
    special_app_date = db.Column("New App Date", db.String())
    special_issued_date = db.Column("New Issued Date", db.String())
    special_return_date = db.Column("New Return Date", db.String())
    special_ballot_style = db.Column("New Ballot Style", db.String())

    def friendly_date(self):
        # return date.fromisoformat(self.day).strftime("%B %d")
        return ""

    def friendly_voting_method(self):
        # return self.ballot_style.lower()
        return ""

    def friendly_first(self):
        return self.first.capitalize()

    def friendly_ballot_status(self, specialElection):
        if specialElection:
            app_status = self.special_app_status
            ballot_status = self.special_ballot_status
            status_reason = self.special_status_reason
            return_date = self.special_return_date
            result = 'For the January special election, '
        else:
            app_status = self.general_app_status
            ballot_status = self.general_ballot_status
            status_reason = self.general_status_reason
            return_date = self.general_return_date
            result = 'In November\'s general election, '
        
        if ballot_status == 'A':
            result += (self.friendly_first() +
                '\'s ballot was successfully received back at the office on ' +
                return_date.strftime("%B %d") + '.')
        elif ballot_status:
            result += ('there may have been a problem with their ballot. ' +
                'Here\'s the explanation we are seeing: "' + status_reason + '".')
        elif app_status == 'A':
            result += (self.friendly_first() +
                ' applied to vote by mail, but their ballot ')
            if specialElection:
                result += 'has not yet made '
            else:
                result += 'did not make '
            result += 'its way back to be counted.'
        else:
            if specialElection:
                result += 'they are not yet listed in the absentee database. Please encourage them to apply for a mail-in ballot or to vote in person!'
            else:
                result += 'their ballot status is unknown. This could mean that they voted in person, or that they did not vote.'

        return result



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

    if request.values.get("first") and request.values.get("last"):
        statsd.increment("ga.lookup.name")
        logging.info("Handling request by first/last")
        first = request.values["first"].strip().upper().replace(",", "")
        last = request.values["last"].strip().upper().replace(",", "")

        records = (
            VoteRecord.query.filter(VoteRecord.first.like(f"{first}%"))
            .filter(VoteRecord.last == last)
            .order_by(VoteRecord.last, VoteRecord.first)
            .limit(26)
            .all()
        )

        if len(records) == 0:
            statsd.increment("ga.lookup.no_results")
            logging.info("Voter ID query by first/last returned no results")
            return render_template_nocache(
                "no-res-name.html",
                first=first,
                last=last,
            )
        else:
            statsd.increment("ga.lookup.success")
            logging.info("Voter ID query by first/last returned results")
            return render_template_nocache(
                "res-name.html",
                first=first,
                last=last,
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
