from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from app.routes import role_required
from app import dbtools
from app.dbtools import BACKUP_DIR, is_valid_backup, list_backups

backup_bp = Blueprint("backup_bp", __name__, url_prefix="/backup")


@backup_bp.route("/")
@role_required("admin")
def backup_list():
    return render_template("backup.html", backups=list_backups())


@backup_bp.route("/create", methods=["POST"])
@role_required("admin")
def create():
    name = dbtools.create_backup()
    flash(f"Backup ban gaya: {name}")
    return redirect(url_for("backup_bp.backup_list"))


@backup_bp.route("/download/<name>")
@role_required("admin")
def download(name):
    if not is_valid_backup(name):
        flash("Backup file nahi mili.")
        return redirect(url_for("backup_bp.backup_list"))
    return send_from_directory(BACKUP_DIR, name, as_attachment=True)


@backup_bp.route("/restore/<name>", methods=["POST"])
@role_required("admin")
def restore(name):
    if not is_valid_backup(name):
        flash("Backup file nahi mili.")
        return redirect(url_for("backup_bp.backup_list"))

    if request.form.get("confirm") != "RESTORE":
        flash("Restore ke liye box mein RESTORE likhna zaroori hai.")
        return redirect(url_for("backup_bp.backup_list"))

    safety = dbtools.restore_backup(name)
    flash(f"Restore ho gaya: {name}. Pehle ka data safety file mein hai: {safety}")
    return redirect(url_for("backup_bp.backup_list"))