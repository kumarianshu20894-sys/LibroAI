from flask_login import current_user
from app import db
from app.models import AuditLog


def log_action(action, details=""):
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else "system"
    db.session.add(AuditLog(user_id=user_id, user_name=user_name, action=action, details=details))