# app/models/parameters/values.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, event, and_, or_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declared_attr
from app.extensions import db
from app.models.enums import EntityType

class ParameterValue(db.Model):
    """Valeur polymorphique avec historisation"""
    __tablename__ = 'parameter_values'

    # Colonne discriminatrice EN PREMIER
    value_type = db.Column(String(50))

    __mapper_args__ = {
        'polymorphic_on': value_type,
        'polymorphic_identity': 'base'
    }
    
    id = db.Column(db.Integer, primary_key=True)
    parameter_definition_id = db.Column(
        db.Integer, 
        ForeignKey('parameter_definitions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    entity_id = db.Column(db.Integer)
    entity_type = db.Column(db.Enum(EntityType))
    config_instance_id = db.Column(
        db.Integer, 
        ForeignKey('configuration_instances.id', ondelete='SET NULL'),
        index=True
    )
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    is_active = db.Column(db.Boolean, default=True, index=True)
    notes = db.Column(db.Text)
    
    # Relations
    @declared_attr
    def definition(cls):
        return db.relationship(
            "ParameterDefinition",
            back_populates="values",
            foreign_keys="ParameterValue.parameter_definition_id"
        )

    @declared_attr
    def dependencies(cls):
        return db.relationship(
            "ParameterDependency",
            back_populates="source_value",
            foreign_keys="ParameterDependency.source_parameter_id"
        )


class FloatParameterValue(ParameterValue):
    __tablename__ = 'float_parameter_values'
    __mapper_args__ = {'polymorphic_identity': 'float', 'concrete': True}
    
    id = db.Column(db.Integer, ForeignKey('parameter_values.id'), primary_key=True)
    value = db.Column(db.Float)
    unit = db.Column(db.String(50))

class StringParameterValue(ParameterValue):
    __tablename__ = 'string_parameter_values'
    __mapper_args__ = {'polymorphic_identity': 'string', 'concrete': True}
    
    id = db.Column(db.Integer, ForeignKey('parameter_values.id'), primary_key=True)
    value = db.Column(db.String(255))
    max_length = db.Column(db.Integer)

class JSONParameterValue(ParameterValue):
    __tablename__ = 'json_parameter_values'
    __mapper_args__ = {'polymorphic_identity': 'json', 'concrete': True}
    
    id = db.Column(db.Integer, ForeignKey('parameter_values.id'), primary_key=True)
    value = db.Column(db.JSON)
