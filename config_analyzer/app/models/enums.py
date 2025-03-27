# app/models/enums.py
from enum import Enum

class EntityType(str, Enum):
    USER = "user"
    CLIENT = "client"
    ROBOT_MODEL = "robot_model"
    SOFTWARE = "software"
    GROUP = "group"
    ROLE = "role"
    ROBOT_INSTANCE = "robot_instance"
    SOFTWARE_VERSION = "software_version"
    ENTITY = "entity"
