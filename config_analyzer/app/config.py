import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres_u_config_analyzer:password_ca@config_analyzer_db:5432/config_analyzer_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'clé_secrète_dev')
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')

class DevConfig(Config):
    pass