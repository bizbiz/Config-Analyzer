from . import db
from .software import Software

class ConfigurationFile(db.Model):
    __tablename__ = 'configuration_files'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('softwares.id'))  # ForeignKey corrigée
    
    software = db.relationship('Software', back_populates='configuration_files')
