# app/models/entities/software_version.py
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation

@configure_slug_generation
class SoftwareVersion(SpecificEntity):
    """Version spécifique d'un logiciel"""
    __mapper_args__ = {'polymorphic_identity': EntityType.SOFTWARE_VERSION}

    slug_source_field = 'version'
    CUSTOM_SLUG_FIELD = 'software'

    version = Column(String(20), nullable=False, index=True)
    software_id = Column(Integer, ForeignKey('software.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relations
    software = relationship("Software", back_populates="versions")
    base_configurations = relationship(
        "ConfigurationTemplate",
        back_populates="software_version",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('software_id', 'version', name='uq_software_version'),
    )

    def __repr__(self):
        return f'<SoftwareVersion {self.software.name} {self.version}>'

    @property
    def full_version(self):
        return f"{self.software.name} {self.version}"
