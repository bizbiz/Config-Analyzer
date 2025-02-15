from flask import Flask
from flask_migrate import Migrate
from app.extensions import db

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    migrate.init_app(app, db)

    # Import des modèles APRÈS initialisation de db
    from app.models import Client, PostalCode, RobotModel, Software
    
    # Création du contexte d'application
    with app.app_context():
        db.create_all()  # Optionnel pour développement

    # Enregistrement des blueprints
    from app.routes.clients import clients_bp
    app.register_blueprint(clients_bp)

    from app.routes.robot_models import robot_models_bp
    app.register_blueprint(robot_models_bp)

    from app.routes.software import software_bp
    app.register_blueprint(software_bp)

    from app.routes.home import home_bp
    app.register_blueprint(home_bp)

    from app.routes.software_versions import software_versions_bp
    app.register_blueprint(software_versions_bp)

    return app