from flask import Blueprint, redirect, render_template, flash, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Book, Member, Reservation
from app.routes import role_required

reservations = Blueprint("reservations", __name__, url_prefix="/reservations")


@reservations.route("/")
@role_required("admin","librarian")
def reservation_list():
    items = Reservation.query.filter_by(status="waiting").order_by(Reservation.created_at).all()
    return render_template("reservation_list.html",reservations=items)

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