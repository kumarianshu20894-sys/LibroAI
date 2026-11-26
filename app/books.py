from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Book, Copy, Issue, Reservation
from app.routes import role_required
from app.audit import log_action

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
        price = request.form.get("price", type=float)

        if not title:
            flash("Title zaroori hai.")
            return render_template("book_form.html", book=None)

        if price is None or price < 0:
            flash("Price zaroori hai aur 0 se kam nahi ho sakta.")
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
            price=price,
        )
        db.session.add(book)
        db.session.flush()

        copies_count = request.form.get("copies", 1, type=int) or 1
        shelf = request.form.get("shelf", "").strip()
        is_reference = bool(request.form.get("is_reference"))
        for n in range(1, copies_count + 1):
            db.session.add(Copy(
                book=book,
                copy_number=n,
                shelf=shelf,
                status="available",
                is_reference=is_reference,
            ))

        log_action("book_add", f"Book: {title}")
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
        price = request.form.get("price", type=float)

        if not title:
            flash("Title zaroori hai.")
            return render_template("book_form.html", book=book)

        if price is None or price < 0:
            flash("Price zaroori hai aur 0 se kam nahi ho sakta.")
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
        book.price = price
        log_action("book_edit", f"Book id {book.id}: {book.title}")
        db.session.commit()

        flash("Book update ho gayi.")
        return redirect(url_for("books.book_list"))

    return render_template("book_form.html", book=book)


@books.route("/<int:book_id>/delete", methods=["POST"])
@role_required("admin")
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    copy_ids = [c.id for c in book.copies]

    # 1. Koi bhi issue record (active ya purana) ho to delete nahi
    has_issue_history = bool(copy_ids) and Issue.query.filter(
        Issue.copy_id.in_(copy_ids)
    ).first() is not None

    # 2. Koi bhi reservation record (kisi bhi status ka) ho to delete nahi
    has_reservation_history = Reservation.query.filter_by(book_id=book.id).first() is not None

    if has_issue_history or has_reservation_history:
        flash("Is book ka issue ya reservation record hai, isliye delete nahi ho sakti.")
        return redirect(url_for("books.book_list"))

    # 3. Koi copy available nahi hai (issued, reserved, damaged) to delete nahi
    if any(c.status != "available" for c in book.copies):
        flash("Is book ki kuch copies available nahi hain, isliye delete nahi ho sakti.")
        return redirect(url_for("books.book_list"))

    log_action("book_delete", f"Book id {book.id}: {book.title}")

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


@books.route("/<int:book_id>/copies", methods=["GET", "POST"])
@role_required("admin", "librarian")
def manage_copies(book_id):
    book = db.get_or_404(Book, book_id)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            count = request.form.get("count", 1, type=int) or 1
            shelf = request.form.get("shelf", "").strip()
            last_number = max([c.copy_number for c in book.copies], default=0)
            for n in range(1, count + 1):
                db.session.add(Copy(
                    book=book,
                    copy_number=last_number + n,
                    shelf=shelf,
                    status="available",
                ))
            log_action("copies_add", f"Book id {book.id}: {count} copies, shelf {shelf}")
            db.session.commit()
            flash(f"{count} nayi copies add ho gayi.")

        elif action == "status":
            copy = db.get_or_404(Copy, request.form.get("copy_id", type=int))
            new_status = request.form.get("new_status")

            if copy.book_id != book.id:
                flash("Ye copy is book ki nahi hai.")
            elif copy.status in ("issued", "reserved"):
                flash("Ye copy abhi issued ya reserved hai. Pehle return karwayein.")
            elif new_status not in ("available", "damaged", "lost", "removed"):
                flash("Wrong status!")
            else:
                copy.status = new_status
                log_action("copy_status", f"Copy {copy.id} of book {book.id}: {new_status}")
                db.session.commit()
                flash(f"Copy {copy.copy_number} ka status {new_status} ho gaya.")

        return redirect(url_for("books.manage_copies", book_id=book.id))

    return render_template("manage_copies.html", book=book)