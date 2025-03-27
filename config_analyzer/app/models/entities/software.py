# app/models/entities/software.py
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation

@configure_slug_generation
class Software(SpecificEntity):
    """Logiciel avec gestion polymorphique"""
    __mapper_args__ = {'polymorphic_identity': EntityType.SOFTWARE}
    
    slug_source_field = 'name'
    CUSTOM_SLUG_FIELD = 'robot_model'  # Utilise le premier robot_model associé

    description = Column(String(500), comment="Description détaillée du logiciel")

    # Relations
    versions = relationship(
        'SoftwareVersion', 
        back_populates='software',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    robot_models = relationship(
        'RobotModelSoftware',
        back_populates='software',
        cascade='all, delete-orphan'
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
