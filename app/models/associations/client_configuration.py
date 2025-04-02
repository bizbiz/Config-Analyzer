# app/models/associations/client_configuration.py
from sqlalchemy.orm import relationship, declared_attr
from app.extensions import db

class ClientConfiguration(db.Model):
    __tablename__ = 'client_configuration'
    
    # Ajout d'une clé primaire
    id = db.Column(db.Integer, primary_key=True)
    
    # Ajouter d'autres colonnes nécessaires
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    config_id = db.Column(db.Integer, db.ForeignKey('configuration_instances.id'))
    
    # Relations
    client = db.relationship("Client", back_populates="configurations")
    configuration = db.relationship("ConfigurationInstance", back_populates="client_links")
