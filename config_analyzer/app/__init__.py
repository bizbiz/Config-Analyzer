from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    db.init_app(app)
    migrate.init_app(app, db)

    # Import des modèles APRÈS création de l'app
    from app.models import Client  # Remplacer par vos modèles réels
    
    # Enregistrement des blueprints
    from app.routes.clients import clients_bp
    app.register_blueprint(clients_bp)

    return app