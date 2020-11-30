import logging, os, smtplib

import sentry_sdk
from flask import Flask, make_response, redirect, render_template, request
from flask_mail import Mail, Message
from sqlalchemy.sql import func
import jinja2
from sentry_sdk.integrations.flask import FlaskIntegration

from analytics import statsd

from models import db
from models.voters import VoteRecord
from models.subscriptions import Subscription

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
mail = Mail(app)

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

@app.route('/subscribe', methods=["POST"])
def subscribe():
    voter_reg_num = request.values.get("voter_reg_num")
    email = request.values.get("email")

    new_sub = Subscription(voter_reg_num=voter_reg_num,
                           email=email)
    db.session.add(new_sub)
    db.session.commit()

    return 'success'

@app.route('/unsubscribe')
def unsubscribe():
    sub_id = request.values.get("sub_id")
    secret = request.values.get("s")

    if secret != Subscription.secret(sub_id):
        return f"Invalid parameter: s={secret}, please make sure you clicked the correct link"

    sub = Subscription.query.get(sub_id)
    sub.active = False
    db.session.commit()

    return f"We will stop sending emails to {sub.email} about that voter."

@app.route('/unsubscribe_all')
def unsubscribe_all():
    email = request.values.get("email")
    secret = request.values.get("s")

    if secret != Subscription.secret(email):
        return f"Invalid parameter: s={s}, please make sure you clicked the correct link"

    (Subscription.query
                 .filter(Subscription.email == email)
                 .update({Subscription.active: False}))
    db.session.commit()

    return (f"We will stop sending any emails to {email}.")


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

DAYS_BETWEEN_EMAILS = 7

def generate_digest_email(address):
    subscriptions = (Subscription.query
        .filter(Subscription.active)
        .filter(Subscription.email == address))
    data = []
    unsub_all = ''
    for s in subscriptions:
        if s.voter_reg_num:
            voter = VoteRecord.query.get(s.voter_reg_num)
        else:
            # TODO: gather data about this search...
            pass
        data.append((voter, s.unsub_url(False)))

        s.last_emailed = func.now()
        db.session.add(s)
        # just for convenience, we generate it each time, but it will be shared
        # across all of them
        unsub_all = s.unsub_url(True) 
    return Message(
        recipients=[address],
        subject='Ballot update for your friends in Georgia',
        html=render_template('digest-email.html', email=address, data=data, unsub_all=unsub_all)
    )

@app.cli.command('send-emails')
def send_emails():
    result = db.engine.execute(f'''
        SELECT DISTINCT(email) FROM subscriptions
        WHERE active AND
            extract(epoch FROM
                (now() - greatest(last_emailed, subscribe_time))
            )/3600 > {24*DAYS_BETWEEN_EMAILS}
    ''')
    with mail.connect() as conn:
        for (email,) in result:
            message = generate_digest_email(email)
            try:
                conn.send(message)
                db.session.commit()
            except smtplib.SMTPException as e:
                logging.warning(f'Exception {e} while sending an email to "{email}"')
                db.session.rollback()

if __name__ == "__main__":
    app.run(debug=DEBUG)
