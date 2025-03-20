import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres_u_config_analyzer:password_ca@config_analyzer_db:5432/config_analyzer_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'clé_secrète_dev')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c statement_timeout=60000"
        }
    }

    @classmethod
    def init_app(cls, app):
        """Configuration commune à tous les environnements"""
        pass

class ProdConfig(Config):
    DEBUG = False

class DevConfig(Config):
    DEBUG = True

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        with app.app_context():
            # Ne pas créer les extensions ici (à faire manuellement en base)
            pass

config = {
    'development': DevConfig,
    'production': ProdConfig,
    'default': DevConfig
}
