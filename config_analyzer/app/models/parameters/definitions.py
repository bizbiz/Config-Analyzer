# app/models/parameters/definitions.py

from app.extensions import db

from sqlalchemy import ForeignKey, CheckConstraint, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.enums import EntityType
from sqlalchemy.orm import declared_attr

class ParameterDefinition(db.Model):
    """Classe de base abstraite pour les définitions de paramètres"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    is_active = db.Column(db.Boolean, default=True)
    target_entity = db.Column(db.Enum(EntityType))  # Entité(s) cible(s)

    @declared_attr
    def values(cls):
        return db.relationship(
            "ParameterValue", 
            back_populates="definition",
            cascade="all, delete-orphan"
        )

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
    
    id = db.Column(db.Integer, db.ForeignKey('parameter_definitions.id'), primary_key=True)
    default_value = db.Column(db.Float)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    unit = db.Column(db.String(50))
    
    __mapper_args__ = {'polymorphic_identity': 'float'}

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
    
    id = db.Column(db.Integer, db.ForeignKey('parameter_definitions.id'), primary_key=True)
    default_value = db.Column(db.String(255))
    regex_pattern = db.Column(db.String(255))
    max_length = db.Column(db.Integer)
    
    __mapper_args__ = {'polymorphic_identity': 'string'}

    @hybrid_property
    def definition_info(self):
        return {
            "default": self.default_value,
            "regex": self.regex_pattern,
            "max_length": self.max_length
        }

class EnumParameterDefinition(ParameterDefinition):
    __tablename__ = 'enum_parameter_definitions'
    
    id = db.Column(db.Integer, db.ForeignKey('parameter_definitions.id'), primary_key=True)
    enum_values = db.Column(db.JSON)  # Stocke les choix possibles
    allow_multiple = db.Column(db.Boolean, default=False)
    
    __mapper_args__ = {'polymorphic_identity': 'enum'}

    @hybrid_property
    def definition_info(self):
        return {
            "choices": self.enum_values,
            "multiple": self.allow_multiple
        }
