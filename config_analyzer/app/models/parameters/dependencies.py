# app/models/parameters/dependencies.py
from sqlalchemy import ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.extensions import db
from .values import ParameterValue

class ParameterDependency(db.Model):
    __tablename__ = 'parameter_dependencies'
 
    __table_args__ = (
        CheckConstraint('source_parameter_id != target_parameter_id', 
                      name='ck_no_self_dependency'),
    )
        
    id = db.Column(db.Integer, primary_key=True)
    source_parameter_id = db.Column(
        Integer, 
        ForeignKey('parameter_values.id', ondelete='CASCADE'),
        index=True  # Ajout d'index pour les performances
    )
    target_parameter_id = db.Column(
        Integer, 
        ForeignKey('parameter_values.id', ondelete='CASCADE'),
        index=True
    )
    condition_type = db.Column(db.String(50))
    condition_value = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relations avec spécification explicite des clés étrangères
    source_value = db.relationship(
        "ParameterValue", 
        foreign_keys=[source_parameter_id],
        back_populates="dependencies",
        lazy="joined"  # Chargement automatique par défaut
    )
    
    target_value = db.relationship(
        "ParameterValue", 
        foreign_keys=[target_parameter_id],
        back_populates="dependent_dependencies",  # Relation inverse nécessaire
        lazy="select"
    )
