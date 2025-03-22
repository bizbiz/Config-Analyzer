# /app/utils/param_helpers.py
from sqlalchemy import or_, and_
from app.models import AdditionalParametersConfig, EntityType

def get_entity_params(entity_type, entity_id):
    """Récupère les paramètres configurés pour une entité"""
    return AdditionalParameter.query.join(AdditionalParametersConfig).filter(
        AdditionalParametersConfig.target_entity == EntityType[entity_type.upper()],
        AdditionalParameter.entity_id == entity_id
    ).all()


def get_applicable_params_configs(entity_type, entity_id=None):
    """
    Récupère toutes les configurations applicables à une entité
    Args:
        entity_type (str): 'client', 'software' ou 'robot_model'
        entity_id (int): ID de l'entité spécifique (optionnel)
    """
    entity_type_enum = {
        'client': EntityType.CLIENT,
        'software': EntityType.SOFTWARE,
        'robot_model': EntityType.ROBOT_MODEL
    }.get(entity_type)

    # Conditions de base
    base_conditions = or_(
        AdditionalParametersConfig.target_entity.is_(None),
        and_(
            AdditionalParametersConfig.target_entity == entity_type_enum,
            AdditionalParametersConfig.applicable_ids == []
        )
    )

    # Si entité spécifique
    if entity_id:
        specific_condition = and_(
            AdditionalParametersConfig.target_entity == entity_type_enum,
            AdditionalParametersConfig.applicable_ids.contains([entity_id])
        )
        base_conditions = or_(base_conditions, specific_condition)

    return AdditionalParametersConfig.query.filter(base_conditions).all()

def get_unconfigured_params(client_id, applicable_configs):
    """
    Récupère les paramètres applicables mais non configurés
    Args:
        client_id (int): ID du client
        applicable_configs (list): Liste des AdditionalParametersConfig applicables
    """
    configured_ids = [c.id for c in applicable_configs if c.additional_parameters]
    return [c for c in applicable_configs if c.id not in configured_ids]
