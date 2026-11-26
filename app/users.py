from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.models import User
from app.routes import role_required
from app.audit import log_action

users = Blueprint("users", __name__, url_prefix="/users")

VALID_ROLES = ["admin", "librarian", "member"]


@users.route("/")
@role_required("admin")
def user_list():
    all_users = User.query.order_by(User.name).all()
    return render_template("user_list.html", users=all_users)


@users.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "librarian")

        if not name or not email or not password:
            flash("Naam, email aur password zaroori hain.")
            return render_template("user_form.html")
        if role not in VALID_ROLES:
            flash("Galat role.")
            return render_template("user_form.html")
        if User.query.filter_by(email=email).first():
            flash("Is email se user pehle se maujood hai.")
            return render_template("user_form.html")

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        log_action("user_add", f"{email} as {role}")
        db.session.commit()
        flash("User add ho gaya.")
        return redirect(url_for("users.user_list"))

    return render_template("user_form.html")


@users.route("/<int:user_id>/role", methods=["POST"])
@role_required("admin")
def change_role(user_id):
    user = db.get_or_404(User, user_id)
    new_role = request.form.get("role")

    if user.id == current_user.id:
        flash("Apna role khud nahi badal sakte.")
    elif new_role not in VALID_ROLES:
        flash("Galat role.")
    else:
        old_role = user.role
        user.role = new_role
        log_action("role_change", f"{user.email}: {old_role} -> {new_role}")
        db.session.commit()
        flash("Role badal diya gaya.")

    return redirect(url_for("users.user_list"))


@users.route("/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)

    if user.id == current_user.id:
        flash("Apne aap ko disable nahi kar sakte.")
    else:
        user.is_active_user = not user.is_active_user
        state = "active" if user.is_active_user else "disabled"
        log_action("user_toggle", f"{user.email} -> {state}")
        db.session.commit()
        flash(f"User {state} ho gaya.")

    return redirect(url_for("users.user_list"))