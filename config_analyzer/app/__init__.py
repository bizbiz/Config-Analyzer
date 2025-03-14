from flask import Flask
from flask_migrate import Migrate
from app.extensions import db
from flask_login import LoginManager

login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User  # Import ici pour éviter les imports circulaires
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)  # Initialiser login_manager ici

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

    from app.routes.softwares import softwares_bp
    app.register_blueprint(softwares_bp)

    from app.routes.home import home_bp
    app.register_blueprint(home_bp)

    from app.routes.software_versions import software_versions_bp
    app.register_blueprint(software_versions_bp)

    from app.routes.software_base_configurations import software_base_configurations_bp
    app.register_blueprint(software_base_configurations_bp)

    from app.routes.robot_clients import robot_clients_bp
    app.register_blueprint(robot_clients_bp)

    from app.routes.parsed_files import parsed_files_bp
    app.register_blueprint(parsed_files_bp)

    return app