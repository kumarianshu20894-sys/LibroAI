from datetime import datetime
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")  # admin, librarian, member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))
    isbn = db.Column(db.String(20), unique=True)
    publisher = db.Column(db.String(150))
    description = db.Column(db.Text)

    copies = db.relationship("Copy", backref="book", lazy=True)


class Copy(db.Model):
    __tablename__ = "copies"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    copy_number = db.Column(db.Integer, nullable=False, default=1)
    shelf = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default="available")  # available, issued, damaged, lost
    condition = db.Column(db.String(100))