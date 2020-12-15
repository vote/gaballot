from sqlalchemy.sql import text
from models import db


def statewide_by_day(current_days_before):
    sql = """
        SELECT * FROM cumulative_stats_by_day
        WHERE days_before < 45 AND days_before > :current_days_before;
    """

    results = {}
    for result in db.engine.execute(text(sql), current_days_before=current_days_before):
        results[result["days_before"]] = {
            "total_general": int(result["total_returned_general"]),
            "total_special": int(result["total_returned_special"]),
        }

    return results
