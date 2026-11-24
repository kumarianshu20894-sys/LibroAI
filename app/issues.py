from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Member, Copy, Issue, Fine
from app.routes import role_required

issues = Blueprint("issues", __name__, url_prefix="/issues")

LOAN_DAYS = 14
FINE_PER_DAY = 2
FINE_CAP = 100
MAX_BOOKS = {"student": 3, "staff": 5, "general": 2}


@issues.route("/")
@role_required("admin", "librarian")
def issue_list():
    active = Issue.query.filter_by(return_date=None).order_by(Issue.due_date).all()
    return render_template("issue_list.html", issues=active, today=date.today())


@issues.route("/new", methods=["GET", "POST"])
@role_required("admin", "librarian")
def new_issue():
    if request.method == "POST":
        member_id = request.form.get("member_id", type=int)
        copy_id = request.form.get("copy_id", type=int)

        member = db.session.get(Member, member_id)
        copy = db.session.get(Copy, copy_id)

        if not member or not copy:
            flash("Member or book copy not found.")
            return redirect(url_for("issues.new_issue"))

        unpaid = (
            Fine.query.join(Issue, Fine.issue_id == Issue.id)
            .filter(Issue.member_id == member.id, Fine.paid == False)
            .count()
        )

        if unpaid > 0:
            flash("This member has an unpaid fine. Please clear the fine first.")
            return redirect(url_for("issues.new_issue"))

        if member.status != "active":
            flash("This member is not active (blocked or expired).")
            return redirect(url_for("issues.new_issue"))

        if copy.status != "available":
            flash("This copy is currently unavailable.")
            return redirect(url_for("issues.new_issue"))

        active_count = Issue.query.filter_by(member_id=member.id, return_date=None).count()
        limit = MAX_BOOKS.get(member.membership_type, 2)
        if active_count >= limit:
            flash(f"This member's limit is {limit} books, and they have already borrowed {active_count}.")
            return redirect(url_for("issues.new_issue"))

        issue = Issue(
            copy_id=copy.id,
            member_id=member.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=LOAN_DAYS),
        )
        copy.status = "issued"
        db.session.add(issue)
        db.session.commit()

        flash(f"Book issued successfully. Due date: {issue.due_date}")
        return redirect(url_for("issues.issue_list"))

    members_list = Member.query.all()
    available_copies = Copy.query.filter_by(status="available").all()
    return render_template("issue_form.html", members=members_list, copies=available_copies)


@issues.route("/<int:issue_id>/return", methods=["POST"])
@role_required("admin", "librarian")
def return_issue(issue_id):
    issue = db.get_or_404(Issue, issue_id)

    if issue.return_date:
        flash("This book has already been returned.")
        return redirect(url_for("issues.issue_list"))

    issue.return_date = date.today()
    issue.copy.status = "available"

    late_days = (issue.return_date - issue.due_date).days
    if late_days > 0:
        amount = min(late_days * FINE_PER_DAY, FINE_CAP)
        db.session.add(Fine(issue_id=issue.id, amount=amount, reason="late"))
        flash(f"Book returned successfully. {late_days} days late, fine: Rs {amount}.")
    else:
        flash("Book returned successfully. No fine.")

    db.session.commit()
    return redirect(url_for("issues.issue_list"))