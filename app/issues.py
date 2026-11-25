from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Member, Copy, Issue, Fine, Reservation
from app.routes import role_required

issues = Blueprint("issues", __name__, url_prefix="/issues")

LOAN_DAYS = 14
STUDENT_LOAN_DAYS = 21
FINE_PER_DAY = 2
FINE_CAP = 100
MAX_BOOKS = {"student": 3, "staff": 5, "general": 2}
RENEW_DAYS = 7
MAX_RENEWALS = 1


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

        if copy.is_reference:
            flash("Reference books cannot be borrowed; they are for reading in the library only.")
            return redirect(url_for("issues.new_issue"))

        active_count = Issue.query.filter_by(member_id=member.id, return_date=None).count()
        limit = MAX_BOOKS.get(member.membership_type, 2)
        if active_count >= limit:
            flash(f"This member's limit is {limit} books, and they have already borrowed {active_count}.")
            return redirect(url_for("issues.new_issue"))

        loan_days = STUDENT_LOAN_DAYS if member.membership_type == "student" else LOAN_DAYS
        issue = Issue(
            copy_id=copy.id,
            member_id=member.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=loan_days),
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

    condition = request.form.get("condition", "ok")
    book = issue.copy.book

    if condition == "damaged" and book.price is None:
        flash("Is book ka price set nahi hai. Pehle book edit karke price daalein.")
        return redirect(url_for("issues.issue_list"))

    issue.return_date = date.today()
    copy = issue.copy
    messages = []

    late_days = (issue.return_date - issue.due_date).days
    if late_days > 0:
        amount = min(late_days * FINE_PER_DAY, FINE_CAP)
        db.session.add(Fine(issue_id=issue.id, amount=amount, reason="late"))
        messages.append(f"{late_days} din late, late fine Rs {amount}.")

    if condition == "damaged":
        damage_amount = book.price * 2
        db.session.add(Fine(issue_id=issue.id, amount=damage_amount, reason="damage"))
        copy.status = "damaged"
        messages.append(f"Damage charge Rs {damage_amount}.")
    else:
        copy.status = "available"
        waiting = (
            Reservation.query.filter_by(book_id=book.id, status="waiting")
            .order_by(Reservation.created_at)
            .first()
        )
        if waiting:
            waiting.status = "ready"
            copy.status = "reserved"
            messages.append(f"Ye book {waiting.member.user.name} ke liye reserved ho gayi hai.")

    db.session.commit()
    flash("Book returned. " + (" ".join(messages) if messages else "Koi fine nahi."))
    return redirect(url_for("issues.issue_list"))


@issues.route("/<int:issue_id>/lost", methods=["POST"])
@role_required("admin", "librarian")
def mark_lost(issue_id):
    issue = db.get_or_404(Issue, issue_id)

    if issue.return_date:
        flash("Ye book pehle hi return ho chuki hai.")
        return redirect(url_for("issues.issue_list"))

    book = issue.copy.book
    if book.price is None:
        flash("Is book ka price set nahi hai. Pehle book edit karke price daalein.")
        return redirect(url_for("issues.issue_list"))

    lost_amount = book.price * 2
    issue.return_date = date.today()
    issue.copy.status = "lost"
    db.session.add(Fine(issue_id=issue.id, amount=lost_amount, reason="lost"))
    db.session.commit()

    flash(f"Book lost mark ho gayi. Charge Rs {lost_amount}.")
    return redirect(url_for("issues.issue_list"))


@issues.route("/<int:issue_id>/renew", methods=["POST"])
@role_required("admin", "librarian")
def renew_issue(issue_id):
    issue = db.get_or_404(Issue, issue_id)

    if issue.return_date:
        flash("Ye book pehle hi return ho chuki hai.")
        return redirect(url_for("issues.issue_list"))

    if issue.renew_count >= MAX_RENEWALS:
        flash("Is book ki renewal limit (1 baar) khatam ho chuki hai.")
        return redirect(url_for("issues.issue_list"))

    has_waiting = Reservation.query.filter_by(book_id=issue.copy.book_id, status="waiting").first()
    if has_waiting:
        flash("Is book ki koi reservation hai, isliye renew nahi ho sakti.")
        return redirect(url_for("issues.issue_list"))

    issue.due_date = issue.due_date + timedelta(days=RENEW_DAYS)
    issue.renew_count += 1
    db.session.commit()

    flash(f"Renewal ho gayi. Nayi due date: {issue.due_date}")
    return redirect(url_for("issues.issue_list"))