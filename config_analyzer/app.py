from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_u_config_analyzer:password_ca@config_analyzer_db:5432/config_analyzer_db'
    db.init_app(app)
    return app