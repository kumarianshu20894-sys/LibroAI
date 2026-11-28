import os
import re
import sqlite3
from datetime import datetime
from app import db

BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups"
)
NAME_RE = re.compile(r"^library_\d{8}_\d{6}\.db$")


def _db_path():
    return db.engine.url.database


def backup_path(name):
    return os.path.join(BACKUP_DIR, name)


def is_valid_backup(name):
    return bool(NAME_RE.match(name)) and os.path.isfile(backup_path(name))


def list_backups():
    if not os.path.isdir(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if NAME_RE.match(f)]
    return sorted(files, reverse=True)


def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = datetime.now().strftime("library_%Y%m%d_%H%M%S.db")
    src = sqlite3.connect(_db_path())
    dst = sqlite3.connect(backup_path(name))
    src.backup(dst)
    dst.close()
    src.close()
    return name


def restore_backup(name):
    # Restore se pehle current data ka safety backup banta hai
    safety = create_backup()

    db.session.remove()
    db.engine.dispose()

    src = sqlite3.connect(backup_path(name))
    dst = sqlite3.connect(_db_path())
    src.backup(dst)
    dst.close()
    src.close()
    return safety