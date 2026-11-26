from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.routes import role_required
from app.settings import DEFAULTS, get_setting, set_setting
from app.audit import log_action

settings_bp = Blueprint("settings_bp", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
@role_required("admin")
def settings_page():
    if request.method == "POST":
        for key in DEFAULTS:
            value = request.form.get(key, "").strip()
            if not value.isdigit():
                flash(f"{key} ke liye sirf number daalein.")
                return redirect(url_for("settings_bp.settings_page"))
            set_setting(key, value)
        log_action("settings_update", "Library settings badli gayi")
        db.session.commit()
        flash("Settings save ho gayi.")
        return redirect(url_for("settings_bp.settings_page"))

    values = {key: get_setting(key) for key in DEFAULTS}
    return render_template("settings.html", values=values)