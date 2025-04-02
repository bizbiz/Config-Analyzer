# app/models/__init__.py
from app.extensions import db
from .base import Entity, SpecificEntity, configure_slug_generation
from .enums import EntityType
from .associations import (
    GroupMember, 
    ClientConfiguration, 
    RobotInstanceSoftwareVersion, 
    RobotModelSoftware,
    ConfigurationEntityLink
)
from .entities import (
    User, 
    Client, 
    RobotModel, 
    Software, 
    Group, 
    Role, 
    RobotInstance, 
    SoftwareVersion
)
from .basic import PostalCode
from .parameters import (
    ParameterDefinition,
    FloatParameterDefinition,
    StringParameterDefinition,
    EnumParameterDefinition,
    ParameterValue,
    FloatParameterValue,
    StringParameterValue,
    JSONParameterValue,
    ParameterDependency
)


__version__ = "1.0.0"
__author__ = "qbizouard@gmail.com"

__all__ = [
    
    # Associations
    'GroupMember', 


    # Core
    'Entity',
    'EntityType',
    'ParameterType',
    'configure_slug_generation',
    
    # Entities
    'User',
    'Client',
    'RobotModel',
    'Software',
    'Group',
    'Role',
    'RobotInstance', 
    'SoftwareVersion',
    
    # Basic models
    'PostalCode',
    
    # Parameters
    'ParameterDefinition',
    'FloatParameterDefinition',
    'StringParameterDefinition', 
    'EnumParameterDefinition'
    'ParameterValue',
    'FloatParameterValue',
    'StringParameterValue',
    'JSONParameterValue',
    'ParameterDependency',

]
