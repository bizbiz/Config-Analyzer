# app/models/associations/configuration_entity_link.py
from sqlalchemy import CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship, validates, declared_attr
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import Entity

class StringEnumType(db.TypeDecorator):
    """Convertit entre Enum et String pour le stockage"""
    impl = db.String(50)
    cache_ok = True

    def __init__(self, enum_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        if isinstance(value, self.enum_type):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.enum_type(value)
        return value

class ConfigurationEntityLink(db.Model):
    """Table de jointure polymorphique entre ConfigurationInstance et les entités"""
    __tablename__ = 'configuration_entity_link'
    
    config_id = db.Column(
        db.Integer, 
        db.ForeignKey('configuration_instances.id', ondelete='CASCADE'), 
        primary_key=True
    )
    entity_type = db.Column(
        db.String(50),  # Type final en VARCHAR
        primary_key=True
    )
    entity_id = db.Column(
        db.Integer,
        db.ForeignKey('entities.id'),
        primary_key=True,
        comment="ID de l'entité référencée"
    )

    # Relation avec ConfigurationInstance
    configuration = db.relationship("ConfigurationInstance", back_populates="entity_links")

    @validates('entity_type')
    def validate_entity_type(self, key, value):
        if isinstance(value, EntityType):
            return value.value  # Conversion ENUM -> str
        return value

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
