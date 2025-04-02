# app/models/entities/software.py
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.ext.associationproxy import association_proxy
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation
from app.models.associations.robot_model_software import RobotModelSoftware

@configure_slug_generation
class Software(SpecificEntity):
    """Logiciel avec gestion polymorphique"""
    __mapper_args__ = {'polymorphic_identity': EntityType.SOFTWARE}
    
    slug_source_field = 'name'
    CUSTOM_SLUG_FIELD = 'robot_model'

    description = Column(String(500), comment="Description détaillée du logiciel")

    # Relations
    versions = db.relationship(
        'SoftwareVersion', 
        foreign_keys='SoftwareVersion.software_id',  # Ajout explicite
        back_populates='software',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    robot_model_associations = db.relationship(
        "RobotModelSoftware",
        back_populates="software",
        cascade="all, delete-orphan"
    )

    robot_models = association_proxy(
        'robot_model_associations', 
        'robot_model',
        creator=lambda rm: RobotModelSoftware(robot_model=rm)
    )

    def __repr__(self):
        return f'<Software {self.name}>'

    @property
    def latest_version(self):
        return self.versions.order_by(SoftwareVersion.version.desc()).first()

    @property
    def robot_model(self):
        """Retourne le nom du premier robot_model associé pour la génération du slug"""
        first_model = self.robot_models[0] if self.robot_models else None
        return first_model.robot_model.name if first_model else None
