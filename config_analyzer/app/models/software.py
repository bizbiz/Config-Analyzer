# app/models/entities/software.py
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import Entity, EntityType, configure_slug_generation

@configure_slug_generation
class Software(Entity):
    __tablename__ = 'software'
    __mapper_args__ = {'polymorphic_identity': EntityType.SOFTWARE}
    
    description = Column(String(500), comment="Description détaillée du logiciel")

    versions = relationship(
        "SoftwareVersion", 
        back_populates="software",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="SoftwareVersion.version.desc()"
    )

    def __repr__(self):
        return f'<Software {self.name}>'

    @property
    def latest_version(self):
        return self.versions.first()

    def add_version(self, version):
        new_version = SoftwareVersion(version=version, software=self)
        db.session.add(new_version)
        return new_version
