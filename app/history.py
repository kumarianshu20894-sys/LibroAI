from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Member
from app.recommend import member_read_books, recommend_books

history_bp = Blueprint("history_bp", __name__, url_prefix="/history")


@history_bp.route("/")
@login_required
def history_page():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash("Sirf members ka reading history hota hai.")
        return redirect(url_for("auth.dashboard"))

    past = member_read_books(member.id)
    suggestions = recommend_books(member.id)
    return render_template("history.html", past=past, suggestions=suggestions)