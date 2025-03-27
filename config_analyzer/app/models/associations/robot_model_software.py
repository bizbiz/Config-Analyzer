# models/associations/robot_model_software.py
from sqlalchemy import ForeignKey, CheckConstraint
from app.extensions import db

class RobotModelSoftware(db.Model):
    """Table d'association entre RobotModel et Software"""
    __tablename__ = 'robot_model_software'
    
    robot_model_id = db.Column(
        db.Integer, 
        ForeignKey('robotmodel.id'), 
        primary_key=True,
        comment="Référence au modèle de robot"
    )
    
    software_id = db.Column(
        db.Integer, 
        ForeignKey('software.id'), 
        primary_key=True,
        comment="Référence au logiciel associé"
    )

    # Relations avec cascade et chargement optimisé
    robot_model = db.relationship(
        "RobotModel", 
        back_populates="software",
        lazy='joined'
    )
    
    software = db.relationship(
        "Software", 
        back_populates="robot_models",
        lazy='selectin'
    )
