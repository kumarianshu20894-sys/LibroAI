from flask import Blueprint, redirect, render_template, flash, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Book, Member, Reservation
from app.routes import role_required
from app.audit import log_action
from app.notify import notify

reservations = Blueprint("reservations", __name__, url_prefix="/reservations")


@reservations.route("/")
@role_required("admin", "librarian")
def reservation_list():
    items = (
        Reservation.query.filter(Reservation.status.in_(["waiting", "ready"]))
        .order_by(Reservation.created_at)
        .all()
    )
    return render_template("reservation_list.html", reservations=items)


@reservations.route("/book/<int:book_id>", methods=["POST"])
@login_required
def reserve_book(book_id):
    book = db.get_or_404(Book, book_id)
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash("Only members can reserve books.")
        return redirect(url_for("books.book_detail", book_id=book.id))

    available = any(c.status == "available" for c in book.copies)
    if available:
        flash("This book is currently available. Please issue it directly.")
        return redirect(url_for("books.book_detail", book_id=book.id))

    existing = Reservation.query.filter_by(book_id=book.id, member_id=member.id, status="waiting").first()
    if existing:
        flash("You have already reserved this book.")
        return redirect(url_for("books.book_detail", book_id=book.id))

    db.session.add(Reservation(book_id=book.id, member_id=member.id))
    db.session.commit()
    flash("Book reserved successfully. You will be notified when it becomes available.")
    return redirect(url_for("books.book_detail", book_id=book.id))

@reservations.route("/<int:reservation_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(reservation_id):
    reservation = db.get_or_404(Reservation, reservation_id)
    member = Member.query.filter_by(user_id=current_user.id).first()
    is_staff = current_user.role in ("admin", "librarian")

    if not is_staff and (not member or reservation.member_id != member.id):
        flash("Ye reservation aapki nahi hai.")
        return redirect(url_for("auth.dashboard"))

    if reservation.status not in ("waiting", "ready"):
        flash("Ye reservation cancel nahi ho sakti.")
        return redirect(url_for("auth.dashboard"))

    was_ready = reservation.status == "ready"
    reservation.status = "cancelled"
    book = reservation.book

    if was_ready:
        reserved_copy = next((c for c in book.copies if c.status == "reserved"), None)
        if reserved_copy:
            next_waiting = (
                Reservation.query.filter_by(book_id=book.id, status="waiting")
                .order_by(Reservation.created_at)
                .first()
            )
            if next_waiting:
                next_waiting.status = "ready"
            else:
                reserved_copy.status = "available"

    log_action("reservation_cancel", f"Reservation {reservation.id}, book: {book.title}")
    db.session.commit()
    flash("Reservation cancel ho gayi.")
    return redirect(url_for("auth.dashboard"))