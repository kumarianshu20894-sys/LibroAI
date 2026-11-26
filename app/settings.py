from app import db
from app.models import Setting

DEFAULTS = {
    "loan_days": "14",
    "student_loan_days": "21",
    "renew_days": "7",
    "fine_per_day": "2",
    "fine_cap": "100",
    "max_general": "2",
    "max_student": "3",
    "max_staff": "5",
}


def get_setting(key):
    row = db.session.get(Setting, key)
    if row:
        return row.value
    return DEFAULTS[key]


def get_int(key):
    return int(get_setting(key))


def set_setting(key, value):
    row = db.session.get(Setting, key)
    if row:
        row.value = str(value)
    else:
        db.session.add(Setting(key=key, value=str(value)))