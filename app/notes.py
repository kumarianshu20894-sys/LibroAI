from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Book, Member, ReadingNote

notes_bp = Blueprint("notes_bp", __name__, url_prefix="/notes")


def _current_member():
    return Member.query.filter_by(user_id=current_user.id).first()


@notes_bp.route("/")
@login_required
def notes_list():
    member = _current_member()
    if not member:
        flash("Sirf members notes likh sakte hain.")
        return redirect(url_for("auth.dashboard"))

    notes = (
        ReadingNote.query.filter_by(member_id=member.id)
        .order_by(ReadingNote.created_at.desc())
        .all()
    )
    books = Book.query.order_by(Book.title).all()
    return render_template("notes.html", notes=notes, books=books)


@notes_bp.route("/add", methods=["POST"])
@login_required
def add_note():
    member = _current_member()
    if not member:
        flash("Sirf members notes likh sakte hain.")
        return redirect(url_for("auth.dashboard"))

    book_id = request.form.get("book_id", type=int)
    note_type = request.form.get("note_type", "note")
    content = request.form.get("content", "").strip()

    if note_type not in ("note", "quote"):
        note_type = "note"
    if not content:
        flash("Note khaali nahi ho sakta.")
        return redirect(url_for("notes_bp.notes_list"))
    if not db.session.get(Book, book_id):
        flash("Book nahi mili.")
        return redirect(url_for("notes_bp.notes_list"))

    db.session.add(ReadingNote(
        member_id=member.id, book_id=book_id, note_type=note_type, content=content
    ))
    db.session.commit()
    flash("Note save ho gaya.")
    return redirect(url_for("notes_bp.notes_list"))


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    note = db.get_or_404(ReadingNote, note_id)
    member = _current_member()
    if not member or note.member_id != member.id:
        flash("Ye note aapka nahi hai.")
        return redirect(url_for("notes_bp.notes_list"))

    db.session.delete(note)
    db.session.commit()
    flash("Note delete ho gaya.")
    return redirect(url_for("notes_bp.notes_list"))