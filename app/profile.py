from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db

profile = Blueprint("profile", __name__, url_prefix="/profile")


@profile.route("/", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Naam khaali nahi ho sakta.")
            return redirect(url_for("profile.edit_profile"))

        current_user.name = name
        db.session.commit()
        flash("Profile update ho gayi.")
        return redirect(url_for("profile.edit_profile"))

    return render_template("profile.html")


@profile.route("/password", methods=["POST"])
@login_required
def change_password():
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(old_password):
        flash("Purana password galat hai.")
    elif len(new_password) < 6:
        flash("Naya password kam se kam 6 characters ka hona chahiye.")
    elif new_password != confirm_password:
        flash("Naya password aur confirm password match nahi karte.")
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Password badal gaya.")

    return redirect(url_for("profile.edit_profile"))