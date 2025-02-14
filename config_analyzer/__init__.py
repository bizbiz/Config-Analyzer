from flask import Flask
from .models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object('config_analyzer.config.Config')
    
    db.init_app(app)
    
    from .app.routes.clients import clients_bp
    app.register_blueprint(clients_bp)

    return app