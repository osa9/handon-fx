import datetime
import pytz


def jst_same_month(utc_date: datetime.datetime, utc_now: datetime.datetime = None):
    jst = pytz.timezone("Asia/Tokyo")
    if utc_now is None:
        jst_now = datetime.datetime.now(jst)
    else:
        jst_now = utc_now.astimezone(jst)

    jst_date = utc_date.astimezone(jst)
    return jst_date.month == jst_now.month


def jst_delta_days(utc_date: datetime.datetime, utc_now: datetime.datetime = None):
    jst = pytz.timezone("Asia/Tokyo")
    if utc_now is None:
        jst_now = datetime.datetime.now(jst)
    else:
        jst_now = utc_now.astimezone(jst)

    jst_utc_date = utc_date.astimezone(jst)
    if jst_utc_date > jst_now:
        return 0
    return (jst_now - jst_utc_date).days
