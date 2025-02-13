from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_u_config_analyzer:password_ca@config_analyzer_db:5432/config_analyzer_db'
    db.init_app(app)
    migrate.init_app(app, db)

    # Import blueprints AFTER app creation
    with app.app_context():
        from .routes.clients import clients_bp
        from .routes.robots import robots_bp
        from .routes.machine_clients import machine_clients_bp
        from .routes.softwares import softwares_bp
        from .routes.robot_softwares import robot_softwares_bp
        from .routes.parametres import parametres_bp

        # Register blueprints
        app.register_blueprint(clients_bp)
        app.register_blueprint(robots_bp)
        app.register_blueprint(machine_clients_bp)
        app.register_blueprint(softwares_bp)
        app.register_blueprint(robot_softwares_bp)
        app.register_blueprint(parametres_bp)

    return app