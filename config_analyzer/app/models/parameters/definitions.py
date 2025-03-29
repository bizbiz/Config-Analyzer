# app/models/parameters/definitions.py

from app.extensions import db

from sqlalchemy import ForeignKey, CheckConstraint, Enum, String, Column, Float, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.enums import EntityType
from sqlalchemy.orm import declared_attr, Mapped, mapped_column, relationship
from sqlalchemy.types import Text, DateTime

class ParameterDefinition(db.Model):
    """Classe de base concrète pour les définitions de paramètres"""
    __tablename__ = 'parameter_definitions'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(default=True)
    target_entity = mapped_column(Enum(EntityType))
    definition_type: Mapped[str] = mapped_column(String(50))  # Colonne discriminatrice

    __mapper_args__ = {
        'polymorphic_on': 'definition_type',
        'polymorphic_identity': 'base'
    }

    __table_args__ = (
        UniqueConstraint('name', 'target_entity', name='uix_name_target_entity'),
    )

    # Relation avec les valeurs
    values = db.relationship(
        "ParameterValue", 
        back_populates="definition",
        cascade="all, delete-orphan",
        foreign_keys="ParameterValue.parameter_definition_id"
    )

    dependencies_out = db.relationship(
        "ParameterDependency",
        foreign_keys="ParameterDependency.source_parameter_id",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    
    dependencies_in = db.relationship(
        "ParameterDependency",
        foreign_keys="ParameterDependency.target_parameter_id",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    
    @property
    def dependencies(self):
        """Liste des paramètres dépendants (lecture seule)"""
        return [dep.target for dep in self.dependencies_out]
    
    @property
    def dependents(self):
        """Liste des paramètres qui dépendent de ce paramètre (lecture seule)"""
        return [dep.source for dep in self.dependencies_in]

    @hybrid_property
    def definition_info(self):
        """Retourne les métadonnées spécifiques au type sous forme de dict"""
        raise NotImplementedError("Implémenté dans les sous-classes")

    def get_definition(self):
        """Version générique pour l'API"""
        return {
            "type": self.type_display,
            "description": self.description,
            **self.definition_info
        }

class FloatParameterDefinition(ParameterDefinition):
    __tablename__ = 'float_parameter_definitions'
    
    id: Mapped[int] = mapped_column(
        ForeignKey('parameter_definitions.id'), 
        primary_key=True
    )
    default_value: Mapped[float] = mapped_column(Float)
    min_value: Mapped[float] = mapped_column(Float)
    max_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'float',
        'inherit_condition': (id == ParameterDefinition.id)
    }

    @hybrid_property
    def definition_info(self):
        return {
            "default": self.default_value,
            "min": self.min_value,
            "max": self.max_value,
            "unit": self.unit
        }

class StringParameterDefinition(ParameterDefinition):
    __tablename__ = 'string_parameter_definitions'
    
    id = mapped_column(
        db.Integer, 
        ForeignKey('parameter_definitions.id'), 
        primary_key=True
    )
    default_value = mapped_column(db.String(255))
    regex_pattern = mapped_column(db.String(255))
    max_length = mapped_column(db.Integer)
    
    __mapper_args__ = {
        'polymorphic_identity': 'string',
        'inherit_condition': (id == ParameterDefinition.id)
    }

class EnumParameterDefinition(ParameterDefinition):
    __tablename__ = 'enum_parameter_definitions'
    
    id = mapped_column(
        db.Integer, 
        ForeignKey('parameter_definitions.id'), 
        primary_key=True
    )
    enum_values = mapped_column(db.JSON)
    allow_multiple = mapped_column(db.Boolean, default=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'enum',
        'inherit_condition': (id == ParameterDefinition.id)
    }