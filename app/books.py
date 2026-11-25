from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Book, Copy
from app.routes import role_required

books = Blueprint("books", __name__, url_prefix="/books")


@books.route("/")
@login_required
def book_list():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like))
        )

    pagination = query.order_by(Book.title).paginate(page=page, per_page=10, error_out=False)
    return render_template("book_list.html", pagination=pagination, q=q)


@books.route("/add", methods=["GET", "POST"])
@role_required("admin", "librarian")
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        isbn = request.form.get("isbn", "").strip() or None

        if not title:
            flash("Title zaroori hai.")
            return render_template("book_form.html", book=None)

        if isbn and Book.query.filter_by(isbn=isbn).first():
            flash("Is ISBN wali book pehle se maujood hai.")
            return render_template("book_form.html", book=None)

        book = Book(
            title=title,
            author=request.form.get("author", "").strip(),
            isbn=isbn,
            publisher=request.form.get("publisher", "").strip(),
            description=request.form.get("description", "").strip(),
        )
        db.session.add(book)
        db.session.flush()  # book.id ke liye

        copies_count = request.form.get("copies", 1, type=int) or 1
        shelf = request.form.get("shelf", "").strip()
        for n in range(1, copies_count + 1):
            db.session.add(Copy(
                book=book,
                copy_number=n,
                shelf=shelf,
                status="available",
                is_reference=bool(request.form.get("is_reference"))))

        db.session.commit()
        flash("Book add ho gayi.")
        return redirect(url_for("books.book_list"))

    return render_template("book_form.html", book=None)


@books.route("/<int:book_id>/edit", methods=["GET", "POST"])
@role_required("admin", "librarian")
def edit_book(book_id):
    book = db.get_or_404(Book, book_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        isbn = request.form.get("isbn", "").strip() or None

        if not title:
            flash("Title zaroori hai.")
            return render_template("book_form.html", book=book)

        if isbn:
            other = Book.query.filter(Book.isbn == isbn, Book.id != book.id).first()
            if other:
                flash("Is ISBN wali doosri book pehle se maujood hai.")
                return render_template("book_form.html", book=book)

        book.title = title
        book.author = request.form.get("author", "").strip()
        book.isbn = isbn
        book.publisher = request.form.get("publisher", "").strip()
        book.description = request.form.get("description", "").strip()
        db.session.commit()

        flash("Book update ho gayi.")
        return redirect(url_for("books.book_list"))

    return render_template("book_form.html", book=book)


@books.route("/<int:book_id>/delete", methods=["POST"])
@role_required("admin")
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)

    if any(c.status == "issued" for c in book.copies):
        flash("Is book ki kuch copies issued hain, pehle unhe return karwayein.")
        return redirect(url_for("books.book_list"))

    for copy in book.copies:
        db.session.delete(copy)
    db.session.delete(book)
    db.session.commit()

    flash("Book delete ho gayi.")
    return redirect(url_for("books.book_list"))


@books.route("/<int:book_id>")
@login_required
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    return render_template("book_detail.html", book=book)