from app.models import Issue


def finished_books(member_id, year, month):
    """Us mahine mein return ki hui books (Issue objects)."""
    issues = Issue.query.filter(
        Issue.member_id == member_id,
        Issue.return_date.isnot(None),
    ).all()
    return [i for i in issues if i.return_date.year == year and i.return_date.month == month]


def books_finished_in_month(member_id, year, month):
    return len(finished_books(member_id, year, month))


def current_streak(member_id, goal_map):
    """Aaj ke mahine se peeche, consecutive mahine jahan goal poora hua."""
    from datetime import date
    today = date.today()
    year, month = today.year, today.month
    streak = 0
    while True:
        target = goal_map.get((year, month))
        if target is None:
            break
        if books_finished_in_month(member_id, year, month) < target:
            break
        streak += 1
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return streak