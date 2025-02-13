from . import db
from .client import Client
from .software import Software

class ParametreLogiciel(db.Model):
    __tablename__ = 'parametres_logiciels'
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False)
    
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    software_id = db.Column(db.Integer, db.ForeignKey('software.id'))
    
    client = db.relationship('Client', back_populates='parametres')
    software = db.relationship('Software', back_populates='parametres')