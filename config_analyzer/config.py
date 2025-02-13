# config.py
import os

class Config:
    # Clé secrète obligatoire pour Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clé_secrète_dev')  # À changer en prod
    
    # Configuration base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres_u_config_analyzer:password_ca@config_analyzer_db:5432/config_analyzer_db')
    
    # Désactive le tracking des modifications SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FLASK_APP = 'main.py'  # Spécifie le point d'entrée pour Flask-Migrate
    
    # Mode debug (désactiver en production)
    DEBUG = True

# Configuration spécifique pour la production
class ProdConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

# Configuration développement
class DevConfig(Config):
    pass
