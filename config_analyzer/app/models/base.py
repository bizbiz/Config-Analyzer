# app/models/base.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, event, and_, or_
from sqlalchemy.orm import declared_attr, relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from app.extensions import db
from .enums import EntityType
import re

def camel_to_snake(name):
    """Convertit CamelCase en SCREAMING_SNAKE_CASE amélioré"""
    # Ajoute un underscore devant les groupes de majuscules suivis de minuscules
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Gère les acronymes (ex: HTTPAPI → HTTP_API)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.upper().replace("__", "_")  # Nettoie les doubles underscores

class EntityMixin:
    """Mixin de base pour toutes les entités polymorphiques"""
    
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True)
    
    @declared_attr
    def name(cls):
        return Column(String(255), nullable=False)
    
    @declared_attr
    def slug(cls):
        return Column(String(255), nullable=False, unique=True, index=True)
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now())
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @declared_attr
    def entity_type(cls):
        return Column(Enum(EntityType), nullable=False)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @declared_attr
    def __mapper_args__(cls):
        if cls.__name__ != 'Entity':
            # Conversion automatique du nom de classe
            enum_name = camel_to_snake(cls.__name__)
            
            return {
                'polymorphic_identity': EntityType[enum_name],
                'inherit_condition': (getattr(cls, 'id') == Entity.id)
            }
        return {}

class QueryMixin:
    """Mixin pour les requêtes polymorphes"""
    
    @classmethod
    def get_polymorphic_class(cls, entity_type):
        registry = {
            EntityType.ROBOT_MODEL: 'RobotModel',
            EntityType.SOFTWARE: 'Software',
            EntityType.CLIENT: 'Client'
        }
        return getattr(db.Model, registry.get(entity_type))

class Entity(db.Model, EntityMixin, QueryMixin):
    """Classe de base polymorphique abstraite"""
    __abstract__ = True

    @declared_attr
    def configurations(cls):
        enum_name = camel_to_snake(cls.__name__)  # Utiliser la fonction de conversion
        return relationship(
            'ConfigurationEntityLink',
            primaryjoin=(
                f"and_(ConfigurationEntityLink.entity_type == '{EntityType[enum_name].value}', "
                f"ConfigurationEntityLink.entity_id == {cls.__name__}.id)"
            ),
            backref=backref('entity', lazy='joined'),
            cascade='all, delete-orphan',
            passive_deletes=True
        )

def configure_slug_generation(cls):
    @event.listens_for(cls, 'before_insert')
    @event.listens_for(cls, 'before_update')
    def generate_slug(mapper, connection, target):
        from ..utils.slug_helpers import generate_model_slug  # Import local
        
        if not target.slug:
            base_text = getattr(target, 'name', '')
            custom_field = getattr(cls, 'CUSTOM_SLUG_FIELD', None)
            custom_value = getattr(target, custom_field, None) if custom_field else None

            target.slug = generate_model_slug(
                base_text=base_text,
                model_class=cls,
                custom_value=custom_value,
                max_length=25
            )
    return cls
