from app.models import Book, Issue


def member_read_books(member_id):
    """Member ki returned books (Issue objects), latest pehle."""
    return (
        Issue.query.filter(Issue.member_id == member_id, Issue.return_date.isnot(None))
        .order_by(Issue.return_date.desc())
        .all()
    )


def recommend_books(member_id, limit=10):
    """Member ke padhe hue authors ki doosri books, jo member ne nahi padhi."""
    history = member_read_books(member_id)
    read_book_ids = {i.copy.book_id for i in history}
    read_authors = {i.copy.book.author for i in history if i.copy.book.author}

    if not read_authors:
        return []

    candidates = (
        Book.query.filter(Book.author.in_(read_authors), ~Book.id.in_(read_book_ids))
        .order_by(Book.title)
        .limit(limit)
        .all()
    )
    return candidates