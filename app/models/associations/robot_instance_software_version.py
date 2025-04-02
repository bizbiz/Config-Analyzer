# app/models/associations/robot_instance_software_version.py

from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declared_attr
from app.extensions import db

class RobotInstanceSoftwareVersion(db.Model):
    """Association entre RobotInstance et SoftwareVersion"""
    __tablename__ = 'robot_instance_software_versions'
    
    robot_instance_id = db.Column(
        db.Integer, 
        db.ForeignKey('robotinstance.id'),  # Modifié 'robot_instances.id' → 'robotinstance.id'
        primary_key=True
    )
    software_version_id = db.Column(
        db.Integer, 
        db.ForeignKey('softwareversion.id'), 
        primary_key=True
    )

    installation_date = db.Column(db.DateTime, default=db.func.now())
    
    # Configurer l'index composite
    __table_args__ = (
        db.Index('idx_robot_software', 'robot_instance_id', 'software_version_id'),
    )

    robot_instance = relationship(
        "RobotInstance", 
        back_populates="software_versions",
        foreign_keys=[robot_instance_id]  # Ajout explicite
    )

    software_version = relationship(
        "SoftwareVersion", 
        back_populates="robot_instances",  # À vérifier dans SoftwareVersion
        foreign_keys=[software_version_id]
    )
