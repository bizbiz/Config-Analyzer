from . import db
from .robot import Robot
from .parametre_logiciel import ParametreLogiciel

class MachineClient(db.Model):
    __tablename__ = 'machine_clients'
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False, unique=True)
    
    robot_id = db.Column(db.Integer, db.ForeignKey('robots.id'))
    parametre_id = db.Column(db.Integer, db.ForeignKey('parametres_logiciels.id'))
    
    # Relation corrigée
    robot = db.relationship('Robot', back_populates='machines')
    parametre = db.relationship('ParametreLogiciel', back_populates='machines')

