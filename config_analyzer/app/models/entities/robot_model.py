# app/models/entities/robot_model.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation
from app.models.associations.robot_model_software import RobotModelSoftware

@configure_slug_generation
class RobotModel(SpecificEntity):
    """Modèle de robot avec gestion polymorphique étendue"""
    __mapper_args__ = {'polymorphic_identity': EntityType.ROBOT_MODEL}
    
    # Configuration personnalisée du slug
    slug_source_field = 'name'
    CUSTOM_SLUG_FIELD = 'company'

    # Colonnes spécifiques
    company = Column(String(255), index=True, comment="Fabricant du robot")
    
    # Relations
    software = association_proxy(
        'robot_model_software', 
        'software',
        creator=lambda s: RobotModelSoftware(software=s)
    )
    
    instances = relationship(
        "RobotInstance", 
        back_populates="model",
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    robot_model_software = relationship(
        "RobotModelSoftware",
        back_populates="robot_model",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<RobotModel {self.name} ({self.company})>'
