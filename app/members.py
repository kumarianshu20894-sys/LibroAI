from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User, Member
from app.routes import role_required
from app.audit import log_action

members = Blueprint("members", __name__, url_prefix="/members")


@members.route("/")
@role_required("admin", "librarian")
def member_list():
    all_members = Member.query.join(User).order_by(User.name).all()
    return render_template("member_list.html", members=all_members)


@members.route("/add", methods=["GET", "POST"])
@role_required("admin", "librarian")
def add_member():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        membership_type = request.form.get("membership_type", "general")

        if not name or not email or not password:
            flash("Name, email, and password are required.")
            return render_template("member_form.html")

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.")
            return render_template("member_form.html")

        user = User(name=name, email=email, role="member")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        member = Member(user_id=user.id, phone=phone, membership_type=membership_type)
        db.session.add(member)
        log_action("member_add", f"Member: {email}")
        db.session.commit()

        flash("Member added successfully.")
        return redirect(url_for("members.member_list"))

    return render_template("member_form.html")