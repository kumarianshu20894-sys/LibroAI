from datetime import datetime ,date
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")  # admin, librarian, member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))
    isbn = db.Column(db.String(20), unique=True)
    publisher = db.Column(db.String(150))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(8, 2), nullable=True)

    copies = db.relationship("Copy", backref="book", lazy=True)


class Copy(db.Model):
    __tablename__ = "copies"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    copy_number = db.Column(db.Integer, nullable=False, default=1)
    shelf = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default="available")  # available, issued, damaged, lost
    condition = db.Column(db.String(100))
    is_reference = db.Column(db.Boolean, nullable=False, default=False)

class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    membership_type = db.Column(db.String(20), nullable=False, default="general")
    status = db.Column(db.String(20), nullable=False, default="active")
    expiry_date = db.Column(db.Date)

    user = db.relationship("User", backref=db.backref("member", uselist=False))
    issues = db.relationship("Issue", backref="member", lazy=True)


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    copy_id = db.Column(db.Integer, db.ForeignKey("copies.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    renew_count = db.Column(db.Integer, nullable=False, default=0)

    copy = db.relationship("Copy", backref="issues")
    fines = db.relationship("Fine", backref="issue", lazy=True)


class Fine(db.Model):
    __tablename__ = "fines"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    amount = db.Column(db.Numeric(8, 2), nullable=False)
    reason = db.Column(db.String(20), nullable=False, default="late")
    paid = db.Column(db.Boolean, nullable=False, default=False)
    paid_date = db.Column(db.Date)


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="waiting")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    book = db.relationship("Book", backref="reservations")
    member = db.relationship("Member", backref="reservations")