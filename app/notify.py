from datetime import datetime, timedelta, date
from app import db
from app.models import Notification, Issue


def notify(user_id, message):
    db.session.add(Notification(user_id=user_id, message=message))


def generate_due_reminders(member):
    """Member ki active issues dekh kar due-soon ya overdue reminder banata hai.
    Ek hi message 24 ghante mein dobara nahi banega."""
    today = date.today()
    since = datetime.utcnow() - timedelta(hours=24)
    issues = Issue.query.filter_by(member_id=member.id, return_date=None).all()

    for issue in issues:
        days_left = (issue.due_date - today).days
        title = issue.copy.book.title

        if days_left < 0:
            msg = f"'{title}' ki due date {issue.due_date} thi, ab overdue hai. Jaldi return karein."
        elif days_left <= 2:
            msg = f"'{title}' ki due date {issue.due_date} hai ({days_left} din baki)."
        else:
            continue

        exists = Notification.query.filter(
            Notification.user_id == member.user_id,
            Notification.message == msg,
            Notification.created_at >= since,
        ).first()
        if not exists:
            notify(member.user_id, msg)

    db.session.commit()