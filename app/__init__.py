import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import Engine
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

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

    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

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
    
    return app