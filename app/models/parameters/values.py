# app/models/parameters/values.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, event, and_, or_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declared_attr, validates
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.enums import EntityType
from app.models.parameters.definitions import EnumParameterDefinition

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

    configuration_instance = db.relationship(
        "ConfigurationInstance",
        back_populates="parameters",
        foreign_keys=[config_instance_id]
    )
    
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
            foreign_keys="ParameterDependency.source_value_id"
        )

    @hybrid_property
    def typed_value(self):
        """Retourne la valeur typée selon le type de paramètre"""
        if self.value_type == 'float' and isinstance(self, FloatParameterValue):
            return self.value
        elif self.value_type == 'string' and isinstance(self, StringParameterValue):
            return self.value
        elif self.value_type == 'json' and isinstance(self, JSONParameterValue):
            return self.value
        elif self.value_type == 'enum' and isinstance(self, EnumParameterValue):
            return self.value
        return None

    @typed_value.setter
    def typed_value(self, value):
        """Définit la valeur et le type automatiquement"""
        if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
            if not isinstance(self, FloatParameterValue):
                raise TypeError("Cette instance ne peut pas stocker de valeur numérique")
            self.value = float(value)
            self.value_type = 'float'
        elif isinstance(value, str):
            if isinstance(self, StringParameterValue):
                self.value = value
                self.value_type = 'string'
            elif isinstance(self, EnumParameterValue):
                self.value = value
                self.value_type = 'enum'
            else:
                raise TypeError("Cette instance ne peut pas stocker de chaîne de caractères")
        elif isinstance(value, dict):
            if not isinstance(self, JSONParameterValue):
                raise TypeError("Cette instance ne peut pas stocker de dictionnaire JSON")
            self.value = value
            self.value_type = 'json'
        elif isinstance(value, list):
            if isinstance(self, EnumParameterValue):
                self.value = value
                self.value_type = 'enum'
            elif isinstance(self, JSONParameterValue):
                self.value = value
                self.value_type = 'json'
            else:
                raise TypeError("Cette instance ne peut pas stocker de liste")
        else:
            raise TypeError(f"Type de valeur non supporté: {type(value)}")

    @classmethod
    def create_value(cls, definition, value, **kwargs):
        """
        Méthode factory pour créer une instance de valeur du type approprié
        en fonction de la définition et de la valeur fournie.
        """
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return FloatParameterValue(definition=definition, value=float(value), **kwargs)
        elif isinstance(value, str):
            # Vérifier si c'est une enum ou une string
            if isinstance(definition, EnumParameterDefinition):
                return EnumParameterValue(definition=definition, value=value, **kwargs)
            else:
                return StringParameterValue(definition=definition, value=value, **kwargs)
        elif isinstance(value, list):
            # Liste d'enum ou liste JSON
            if isinstance(definition, EnumParameterDefinition) and definition.allow_multiple:
                return EnumParameterValue(definition=definition, value=value, **kwargs)
            else:
                return JSONParameterValue(definition=definition, value=value, **kwargs)
        elif isinstance(value, dict):
            return JSONParameterValue(definition=definition, value=value, **kwargs)
        else:
            raise TypeError(f"Type de valeur non pris en charge: {type(value)}")


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

class EnumParameterValue(ParameterValue):
    __tablename__ = 'enum_parameter_values'
    __mapper_args__ = {
        'polymorphic_identity': 'enum', 
        'concrete': True
    }
    
    id = db.Column(db.Integer, db.ForeignKey('parameter_values.id'), primary_key=True)
    value = db.Column(db.JSON)  # Stocke les valeurs sélectionnées
    
    @validates('value')
    def validate_enum_value(self, key, value):
        """Valide que les valeurs correspondent aux choix de la définition"""
        definition = self.definition
        if isinstance(definition, EnumParameterDefinition):
            allowed_values = definition.enum_values
            if definition.allow_multiple:
                if not all(v in allowed_values for v in value):
                    raise ValueError("Certaines valeurs ne sont pas autorisées")
            else:
                if value not in allowed_values:
                    raise ValueError(f"Valeur {value} non autorisée")
        return value
