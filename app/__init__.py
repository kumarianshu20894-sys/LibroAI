import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///library.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    @app.context_processor
    def inject_unread_count():
        from flask_login import current_user
        from app.models import Notification
        if current_user.is_authenticated:
            count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return {"unread_count": count}
        return {"unread_count": 0}

    @app.route("/")
    def home():
        return "Library System chal raha hai!"

    from app.routes import auth
    app.register_blueprint(auth)

    from app.books import books
    app.register_blueprint(books)

    from app.members import members
    app.register_blueprint(members)

    from app.issues import issues
    app.register_blueprint(issues)

    from app.fines import fines
    app.register_blueprint(fines)

    from app.reservations import reservations
    app.register_blueprint(reservations)

    from app.profile import profile
    app.register_blueprint(profile)

    from app.users import users
    app.register_blueprint(users)

    from app.settings_routes import settings_bp
    app.register_blueprint(settings_bp)

    from app.notifications import notifications
    app.register_blueprint(notifications)

    from app.wishlist import wishlist
    app.register_blueprint(wishlist)

    from app.goals_routes import goals_bp
    app.register_blueprint(goals_bp)

    from app.history import history_bp
    app.register_blueprint(history_bp)

    return app