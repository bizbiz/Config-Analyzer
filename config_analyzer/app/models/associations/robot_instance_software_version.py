# app/models/associations/robot_instance_software_version.py

from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from app.extensions import db

class RobotInstanceSoftwareVersion(db.Model):
    """Association entre RobotInstance et SoftwareVersion"""
    __tablename__ = 'robot_instance_software_versions'
    
    robot_instance_id = db.Column(db.Integer, ForeignKey('robot_instances.id'), primary_key=True)
    software_version_id = db.Column(db.Integer, ForeignKey('softwareversion.id'), primary_key=True)
    installation_date = db.Column(db.DateTime, default=db.func.now())
    
    # Configurer l'index composite
    __table_args__ = (
        db.Index('idx_robot_software', 'robot_instance_id', 'software_version_id'),
    )

    # Relations optimisées
    robot_instance = relationship(
        "RobotInstance", 
        back_populates="software_versions",
        lazy='joined'
    )
    software_version = relationship(
        "SoftwareVersion", 
        lazy='selectin'
    )
