from sqlalchemy.sql import text
from models import db


def statewide_by_day():
    sql = """
        SELECT * FROM cumulative_stats_by_day
        WHERE days_before < 45 AND days_before >= (select '2021-01-05' - max(date(file_update_time - interval '18 hours')) from updated_times);
    """

    results = {}
    for result in db.engine.execute(text(sql)):
        results[result["days_before"]] = {
            "total_general": int(result["total_returned_general"]),
            "total_special": int(result["total_returned_special"]),
        }

    return results

def statewide_by_party_day():
    sql = """
        SELECT * FROM cumulative_stats_by_party_day
        WHERE days_before < 45 AND days_before >= (select '2021-01-05' - max(date(file_update_time - interval '18 hours')) from updated_times);
    """

    results = {}
    results['combined'] = {}
    for result in db.engine.execute(text(sql)):
        results.setdefault(result['party'] or '', {})[result['days_before']] = {
            "total_general": int(result["total_returned_general"]),
            "total_special": int(result["total_returned_special"]),
        }
        results['combined'].setdefault(result['days_before'], {
            'total_general': 0, 'total_special': 0
        })
        results['combined'][result['days_before']]['total_general'] += int(result["total_returned_general"])
        results['combined'][result['days_before']]['total_special'] += int(result["total_returned_special"])

    return results