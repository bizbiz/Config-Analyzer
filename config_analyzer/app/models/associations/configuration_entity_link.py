# app/models/associations/configuration_entity_link.py
from sqlalchemy import CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import Entity

class ConfigurationEntityLink(db.Model):
    """Table de jointure polymorphique entre ConfigurationInstance et les entités"""
    __tablename__ = 'configuration_entity_link'
    
    config_id = db.Column(
        db.Integer, 
        ForeignKey('configuration_instances.id', ondelete='CASCADE'), 
        primary_key=True
    )
    entity_type = db.Column(
        db.Enum(EntityType),
        primary_key=True,
        comment="Type d'entité (client, robot_model, etc)"
    )
    entity_id = db.Column(
        db.Integer, 
        primary_key=True,
        comment="ID de l'entité référencée"
    )

    # Relation avec ConfigurationInstance
    configuration = relationship("ConfigurationInstance", back_populates="entity_links")

    __table_args__ = (
        CheckConstraint(
            entity_type.in_([member.value for member in EntityType]),
            name='valid_entity_types'
        ),
        Index('ix_entity_ref', 'entity_type', 'entity_id'),
    )

    @property
    def entity(self):
        """Résout l'entité référencée de manière polymorphique"""
        return Entity.get_polymorphic_class(EntityType(self.entity_type)).query.get(self.entity_id)

    @entity.setter
    def entity(self, value):
        """Définit l'entité cible de manière contrôlée"""
        if not isinstance(value, Entity):
            raise TypeError("Seulement des sous-classes Entity autorisées")
        self.entity_type = value.entity_type
        self.entity_id = value.id
