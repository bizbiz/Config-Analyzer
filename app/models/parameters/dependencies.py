# app/models/parameters/dependencies.py
from sqlalchemy import Column, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from app.extensions import db
from .definitions import ParameterDefinition

class ParameterDependency(db.Model):
    __tablename__ = 'parameter_dependencies'
    
    source_parameter_id = db.Column( 
        db.Integer, 
        db.ForeignKey('parameter_definitions.id', ondelete='CASCADE'), 
        primary_key=True,
        comment="Paramètre source de la dépendance"
    )
    target_parameter_id = db.Column( 
        db.Integer, 
        db.ForeignKey('parameter_definitions.id', ondelete='CASCADE'), 
        primary_key=True,
        comment="Paramètre cible de la dépendance"
    )

    condition_type = db.Column(db.String(50))
    condition_value = db.Column(db.JSON)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relations avec spécification explicite des clés étrangères
    source = relationship(
        "ParameterDefinition", 
        foreign_keys=[source_parameter_id],  # Nom corrigé
        back_populates="dependencies_out"
    )
    target = relationship(
        "ParameterDefinition", 
        foreign_keys=[target_parameter_id],  # Nom corrigé
        back_populates="dependencies_in"
    )

    source_value_id = db.Column(  # Nouvelle colonne
        db.Integer, 
        db.ForeignKey('parameter_values.id', ondelete='CASCADE'),
        primary_key=True,
        comment="Valeur source de la dépendance"
    )
    source_value = db.relationship(
        "ParameterValue",
        foreign_keys=[source_value_id],
        back_populates="dependencies"
    )