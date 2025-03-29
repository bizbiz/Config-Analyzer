# app/utils/param_helpers.py

from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType
from sqlalchemy import or_

def get_applicable_params_configs(entity_type_str, entity_id):
    """
    Récupère les définitions de paramètres applicables pour un type d'entité donné.
    
    Args:
        entity_type_str (str): Le type d'entité ('client', 'robot', etc.)
        entity_id (int): L'ID de l'entité
        
    Returns:
        list: Liste des définitions de paramètres applicables
    """
    # Convertir le type d'entité en format Enum
    entity_type = EntityType[entity_type_str.upper()]
    
    # Récupérer les définitions de paramètres pour ce type d'entité
    return ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == entity_type,
        ParameterDefinition.is_active == True
    ).all()

def get_unconfigured_params(entity_id, applicable_configs):
    """
    Identifie quels paramètres applicables ne sont pas encore configurés
    pour une entité donnée.
    
    Args:
        entity_id (int): L'ID de l'entité
        applicable_configs (list): Liste des ParameterDefinition applicables
        
    Returns:
        list: Liste des ParameterDefinition non configurées
    """
    # Récupérer les IDs des définitions déjà configurées pour cette entité
    configured_param_ids = [
        p.parameter_definition_id for p in ParameterValue.query.filter(
            ParameterValue.entity_id == entity_id,
            ParameterValue.is_active == True
        ).all()
    ]
    
    # Filtrer les définitions qui ne sont pas déjà configurées
    return [
        config for config in applicable_configs 
        if config.id not in configured_param_ids
    ]

def get_entity_params(entity_type, entity_id):
    """
    Récupère tous les paramètres configurés pour une entité donnée.
    
    Args:
        entity_type (EntityType): Le type d'entité
        entity_id (int): L'ID de l'entité
        
    Returns:
        list: Liste des valeurs de paramètres configurées
    """
    return ParameterValue.query.filter(
        ParameterValue.entity_type == entity_type,
        ParameterValue.entity_id == entity_id,
        ParameterValue.is_active == True
    ).all()