from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models import Fine, Issue
from app.audit import log_action
from app.routes import role_required

fines = Blueprint("fines", __name__, url_prefix="/fines")


@fines.route("/")
@role_required("admin", "librarian")
def fine_list():
    unpaid = Fine.query.filter_by(paid=False).order_by(Fine.id).all()
    return render_template("fine_list.html", fines=unpaid)


@fines.route("/<int:fine_id>/pay", methods=["POST"])
@role_required("admin", "librarian")
def pay_fine(fine_id):
    fine = db.get_or_404(Fine, fine_id)
    if fine.paid:
        flash("This fine has already been paid.")
        return redirect(url_for("fines.fine_list"))

    fine.paid = True
    fine.paid_date = date.today()
    log_action("fine_paid", f"Fine {fine.id}, Rs {fine.amount}")
    db.session.commit()
    flash(f"Fine of Rs {fine.amount} has been marked as paid.")
    return redirect(url_for("fines.fine_list"))