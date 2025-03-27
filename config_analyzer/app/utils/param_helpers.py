from sqlalchemy import or_, and_
from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType

def get_entity_params(entity_type, entity_id):
    """Récupère les paramètres configurés pour une entité"""
    return ParameterValue.query.join(ParameterDefinition).filter(
        ParameterDefinition.target_entity == EntityType[entity_type.upper()],
        ParameterValue.entity_id == entity_id
    ).all()

def get_applicable_params_configs(entity_type, entity_id=None):
    """
    Récupère toutes les configurations applicables à une entité
    """
    entity_type_enum = EntityType[entity_type.upper()]

    base_conditions = or_(
        ParameterDefinition.target_entity.is_(None),
        and_(
            ParameterDefinition.target_entity == entity_type_enum,
            ParameterDefinition.values == []
        )
    )

    if entity_id:
        specific_condition = and_(
            ParameterDefinition.target_entity == entity_type_enum,
            ParameterDefinition.values.any(entity_id=entity_id)
        )
        base_conditions = or_(base_conditions, specific_condition)

    return ParameterDefinition.query.filter(base_conditions).all()

def get_unconfigured_params(entity_id, applicable_configs):
    """
    Récupère les paramètres applicables mais non configurés
    """
    configured_ids = [c.id for c in applicable_configs if c.values.filter_by(entity_id=entity_id).first()]
    return [c for c in applicable_configs if c.id not in configured_ids]
