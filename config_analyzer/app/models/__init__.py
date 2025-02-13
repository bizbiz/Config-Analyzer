from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .client import Client
from .robot import Robot
from .machine_client import MachineClient
from .software import Software
from .configuration_file import ConfigurationFile
from .parametre_logiciel import ParametreLogiciel