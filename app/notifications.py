from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notifications = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications.route("/")
@login_required
def notification_list():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template("notifications.html", items=items)


@notifications.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("Sab notifications read mark ho gayi.")
    return redirect(url_for("notifications.notification_list"))