# app/__init__.py

from flask import Flask, session
from flask_migrate import Migrate
from flask_login import LoginManager
from app.models.entities.user import User
from app.extensions import db
from app.config import config
from datetime import datetime
import jinja2

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Fonction attribute à ajouter à l'environnement Jinja2
def jinja2_attribute(obj, attribute_name):
    """
    Fonction utilitaire pour accéder aux attributs d'un objet dans Jinja2.
    Équivalent à la fonction `attribute` native de Jinja2.
    """
    if obj is None:
        return None
    try:
        return getattr(obj, attribute_name)
    except AttributeError:
        return None

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configuration globale
    app.config.from_object(config[config_name])
    
    # Configuration spécifique aux sessions
    app.config.update(
        SESSION_COOKIE_NAME='config_analyzer_session',
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=3600  # 1 heure
    )

    # Activer les extensions Jinja2
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')  # Pour break et continue
    
    # Ajouter hasattr comme fonction globale
    app.jinja_env.globals['hasattr'] = hasattr
    
    # Ajouter la fonction attribute (très important pour notre cas)
    app.jinja_env.globals['attribute'] = jinja2_attribute

    # Extensions supplémentaires
    app.jinja_env.add_extension('jinja2.ext.do')
    app.jinja_env.add_extension('jinja2.ext.debug')
    
    # Autres fonctions utiles
    app.jinja_env.globals['isinstance'] = isinstance
    app.jinja_env.globals['str'] = str
    app.jinja_env.globals['int'] = int
    app.jinja_env.globals['float'] = float
    app.jinja_env.globals['len'] = len
    app.jinja_env.globals['dict'] = dict
    app.jinja_env.globals['list'] = list
    
    # Filtres utiles
    app.jinja_env.filters['items'] = lambda d: d.items()
    app.jinja_env.filters['keys'] = lambda d: d.keys()
    app.jinja_env.filters['values'] = lambda d: d.values()    
    
    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y'):
        """Filtre personnalisé pour formater les dates"""
        if value is None:
            return ""
        return value.strftime(format)

    # Middleware pour sessions
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # Enregistrement des blueprints
    register_blueprints(app)

    return app

def register_blueprints(app):
    from app.routes.clients import clients_bp
    from app.routes.robot_models import robot_models_bp
    from app.routes.softwares import softwares_bp
    from app.routes.home import home_bp
    from app.routes.software_versions import software_versions_bp
    from app.routes.configurations import configurations_bp
    from app.routes.robot_instances import robot_instances_bp
    from app.routes.parsed_files import parsed_files_bp
    from app.routes.additional_params import additional_params_bp
    from app.routes.additional_params_config import additional_params_config_bp
    from app.routes.group_management import group_management_bp
    from app.routes.user_management import user_management_bp

    app.register_blueprint(clients_bp)
    app.register_blueprint(robot_models_bp)
    app.register_blueprint(softwares_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(software_versions_bp)
    app.register_blueprint(configurations_bp)
    app.register_blueprint(robot_instances_bp)
    app.register_blueprint(parsed_files_bp)
    app.register_blueprint(additional_params_bp)
    app.register_blueprint(additional_params_config_bp)
    app.register_blueprint(group_management_bp)
    app.register_blueprint(user_management_bp)