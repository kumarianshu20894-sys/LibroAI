from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Book, Copy, Issue, Fine, Member
from app import db
from datetime import date

auth = Blueprint("auth", __name__)


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("auth.dashboard"))

        flash("Email ya password galat hai.")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/dashboard")
@login_required
def dashboard():
    if current_user.role in ["admin","librarian"]:
        stats = {
            "total_books": Book.query.count(),
            "total_copies": Copy.query.count(),
            "issued_copies": Copy.query.filter_by(status="issued").count(),
            "overdue": Issue.query.filter(Issue.return_date.is_(None), Issue.due_date < date.today()).count(),
            "unpaid_fines": Fine.query.filter_by(paid=False).count(),
            "total_members": Member.query.count(),
        }
        return render_template("dashboard_staff.html", stats=stats)

    member = Member.query.filter_by(user_id=current_user.id).first()
    my_issues = []
    if member:
        my_issues = Issue.query.filter_by(member_id=member.id, return_date=None).all()
    return render_template("dashboard_member.html", member=member, my_issues=my_issues)


@auth.route("/admin-only")
@role_required("admin")
def admin_only():
    return "Sirf admin dekh sakta hai"