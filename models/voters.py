from models import db

import jinja2

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

    @staticmethod
    def lookup(last, first, middle, city, county, limit):
        return (VoteRecord.query.filter(VoteRecord.first.like(f"{first}%"))
            .filter(VoteRecord.last == last)
            .filter(VoteRecord.middle.like(f"{middle}%"))
            .filter(VoteRecord.county.like(f"{county}%"))
            .filter(VoteRecord.city.like(f"{city}%"))
            .order_by(VoteRecord.last, VoteRecord.first)
            .limit(limit)
            .all()
        )

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
            ballot_style = self.special_ballot_style
            return_date = self.special_return_date
            result = 'For the January special election, '
        else:
            app_status = self.general_app_status
            ballot_status = self.general_ballot_status
            status_reason = self.general_status_reason
            ballot_style = self.general_ballot_style
            return_date = self.general_return_date
            result = 'In November\'s general election, '
        
        if ballot_status == 'A':
            result += (self.friendly_first() +
                '\'s ' + ballot_style.lower() +
                ' ballot was successfully cast on ' + 
                return_date.strftime("%B %-d") + '.')
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
            if specialElection and self.special_issued_date:
                result += (' The ballot was mailed to them on ' +
                    self.special_issued_date.strftime("%B %-d") + '.')
        else:
            if specialElection:
                result += ('they are not yet listed in the absentee database. ' +
                    'Please encourage them to ' +
                    jinja2.Markup('<a href="https://ballotrequest.sos.ga.gov/" target="_blank" rel="noopener noreferrer">apply for a mail-in ballot</a>!'))
            else:
                result += 'their ballot status is unknown. This could mean that they voted in person, or that they did not vote.'

        return result
