from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Book, Member, Wishlist

wishlist = Blueprint("wishlist", __name__, url_prefix="/wishlist")


@wishlist.route("/")
@login_required
def wishlist_list():
    member = Member.query.filter_by(user_id=current_user.id).first()
    items = []
    if member:
        items = Wishlist.query.filter_by(member_id=member.id).order_by(Wishlist.created_at.desc()).all()
    return render_template("wishlist.html", items=items)


@wishlist.route("/add/<int:book_id>", methods=["POST"])
@login_required
def add_to_wishlist(book_id):
    book = db.get_or_404(Book, book_id)
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash("Sirf members wishlist mein book add kar sakte hain.")
        return redirect(url_for("books.book_detail", book_id=book.id))

    exists = Wishlist.query.filter_by(member_id=member.id, book_id=book.id).first()
    if exists:
        flash("Ye book pehle se wishlist mein hai.")
    else:
        db.session.add(Wishlist(member_id=member.id, book_id=book.id))
        db.session.commit()
        flash("Wishlist mein add ho gayi.")
    return redirect(url_for("books.book_detail", book_id=book.id))


@wishlist.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_wishlist(item_id):
    item = db.get_or_404(Wishlist, item_id)
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member or item.member_id != member.id:
        flash("Ye item aapki wishlist mein nahi hai.")
        return redirect(url_for("wishlist.wishlist_list"))

    db.session.delete(item)
    db.session.commit()
    flash("Wishlist se hata di gayi.")
    return redirect(url_for("wishlist.wishlist_list"))