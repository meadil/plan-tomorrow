from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Fallback to local SQLite if DATABASE_URL isn't set yet
    db_url = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
    
    # Fix Neon/Postgres connection string if it starts with postgres:// (SQLAlchemy requires postgresql://)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev_secret_key_123")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    with app.app_context():
        db.create_all()

    return app