from datetime import datetime, timedelta, timezone

def GetFilterTimestamps():
    now = datetime.now(tz=timezone.utc)
    today = datetime(now.year, now.month, now.day)
    week = today - timedelta(days=today.weekday())
    month = datetime(now.year, now.month, 1)
    recently = today - timedelta(days=42)
    quarter = datetime(now.year, 3 * ((now.month - 1) // 3) + 1, 1)
    year = datetime(now.year, 1, 1)
    dates = {
        'daily': int(today.timestamp()),
        'weekly': int(week.timestamp()),
        'monthly': int(month.timestamp()),
        'recently': int(recently.timestamp()),
        'quarterly': int(quarter.timestamp()),
        'annually': int(year.timestamp())
    }
    return dates