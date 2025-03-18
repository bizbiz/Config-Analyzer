# Imports de la bibliothèque standard Python
import enum
import re
import unicodedata

# Imports de bibliothèques tierces
from flask_login import UserMixin
from sqlalchemy import Enum, ForeignKey, Index, Text, UniqueConstraint, func, select, event
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Imports de modules locaux
from app.extensions import db

# Fonction alternative à slugify si vous ne voulez pas installer la dépendance
def slugify(text, max_length=150):
    """
    Génère un slug à partir du texte donné.
    
    Args:
        text (str): Le texte à convertir en slug
        max_length (int): Longueur maximale du slug (défaut: 150)
        
    Returns:
        str: Le slug généré
    """
    # Convertir en minuscules
    text = str(text).lower()
    
    # Supprimer les accents
    text = ''.join([c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)])
    
    # Remplacer les espaces par des tirets
    text = re.sub(r'[^\w\s-]', '', text).strip()
    text = re.sub(r'[-\s]+', '-', text)
    
    # Limiter la longueur
    return text[:max_length]

class ParameterType(enum.Enum):
    TEXT = "text"
    NUMERIC = "numeric"
    ENUM = "enum"

class PostalCode(db.Model):
    __tablename__ = 'postal_codes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(5), nullable=False)

    clients = db.relationship('Client', back_populates='postal_code_relation', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('code', 'city', 'country_code', name='_postal_code_uc'),
    )

    def __repr__(self):
        return f'<PostalCode {self.code}, {self.city}, {self.country_code}>'

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(150), nullable=False, unique=True, index=True)
    postal_code_id = db.Column(db.Integer, db.ForeignKey('postal_codes.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    postal_code_relation = db.relationship('PostalCode', back_populates='clients')
    robots = db.relationship('RobotClient', back_populates='client')
    configurations = db.relationship('ClientConfigurationFile', back_populates='client')

    def __repr__(self):
        return f'<Client {self.name}>'
    
    def generate_slug(self):
        """Génère un slug unique pour le client."""
        # Essayer d'abord avec juste le nom
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà (exclure l'instance actuelle)
        while Client.query.filter(Client.slug == slug, Client.id != self.id).first():
            # Si le slug existe, essayer avec le nom + code postal
            if self.postal_code_relation:
                test_slug = f"{base_slug}-{slugify(self.postal_code_relation.code)}"
                
                # Vérifier si ce nouveau slug existe déjà
                if not Client.query.filter(Client.slug == test_slug, Client.id != self.id).first():
                    slug = test_slug
                    break
            
            # Si le slug avec code postal existe aussi ou s'il n'y a pas de code postal,
            # ajouter un compteur
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        self.slug = slug
        return slug

from sqlalchemy import event

class RobotModel(db.Model):
    __tablename__ = 'robots_modeles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    company = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    software = db.relationship("RobotModelSoftware", back_populates="robot_modele")
    clients = db.relationship("RobotClient", back_populates="robot_modele")

    def generate_unique_slug(self):
        """Génère un slug unique basé sur le nom."""
        base_slug = slugify(self.name)
        slug = base_slug
        
        # Vérifier si ce slug existe déjà (en excluant l'instance actuelle)
        counter = 1
        while RobotModel.query.filter(RobotModel.slug == slug, 
                                    RobotModel.id != self.id).first():
            # Si le slug existe, ajouter un compteur
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug

# Écouteurs d'événements pour gérer automatiquement les slugs
@event.listens_for(RobotModel, 'before_insert')
def set_robot_model_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion."""
    target.slug = target.generate_unique_slug()

@event.listens_for(RobotModel, 'before_update')
def update_robot_model_slug_on_name_change(mapper, connection, target):
    """Met à jour le slug si le nom a changé."""
    state = db.inspect(target)
    if state.attrs.name.history.has_changes():
        target.slug = target.generate_unique_slug()


class Software(db.Model):
    __tablename__ = 'software'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    versions = db.relationship("SoftwareVersion", back_populates="software")
    robot_modeles = db.relationship("RobotModelSoftware", back_populates="software")

class RobotModelSoftware(db.Model):
    __tablename__ = 'robots_modeles_software'
    robot_modele_id = db.Column(db.Integer, db.ForeignKey('robots_modeles.id'), primary_key=True)
    software_id = db.Column(db.Integer, db.ForeignKey('software.id'), primary_key=True)
    
    robot_modele = db.relationship("RobotModel", back_populates="software")
    software = db.relationship("Software", back_populates="robot_modeles")

class SoftwareVersion(db.Model):
    __tablename__ = 'software_versions'
    id = db.Column(db.Integer, primary_key=True)
    software_id = db.Column(db.Integer, db.ForeignKey('software.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    __table_args__ = (db.UniqueConstraint('software_id', 'version', name='unique_version_per_software'),)
    
    software = db.relationship("Software", back_populates="versions")
    base_configurations = db.relationship("SoftwareBaseConfigurationFile", back_populates="software_version")
    robots = db.relationship("RobotClientSoftwareVersion", back_populates="software_version")

class SoftwareBaseConfigurationFile(db.Model):
    __tablename__ = 'software_base_configuration_files'
    id = db.Column(db.Integer, primary_key=True)
    software_version_id = db.Column(db.Integer, db.ForeignKey('software_versions.id'), nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True))

    __table_args__ = (db.UniqueConstraint('software_version_id', 'file_name', name='unique_base_config_per_version'),)
    
    software_version = db.relationship("SoftwareVersion", back_populates="base_configurations")
    client_configurations = db.relationship("ClientConfigurationFile", back_populates="software_base_configuration")
    parameters = db.relationship("BaseConfigFileParameter", back_populates="base_config_file")

    @hybrid_property
    def safe_client_configurations(self):
        return self.client_configurations or []
    
    @hybrid_property
    def safe_parameters(self):
        return self.parameters.all() if self.parameters else []

    @property
    def last_modified(self):
        param_dates = [p.updated_at for p in self.parameters if p.updated_at]
        base_date = self.updated_at or self.created_at
        all_dates = param_dates + [base_date]
        return max(all_dates) if all_dates else None

class RobotClient(db.Model):
    __tablename__ = 'robots_clients'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    robot_modele_id = db.Column(db.Integer, db.ForeignKey('robots_modeles.id'), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    length = db.Column(db.Float)
    height = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
 
    client = db.relationship("Client", back_populates="robots")
    robot_modele = db.relationship("RobotModel", back_populates="clients")
    software_versions = db.relationship("RobotClientSoftwareVersion", back_populates="robot_client")

class RobotClientSoftwareVersion(db.Model):
    __tablename__ = 'robots_clients_software_versions'
    robot_client_id = db.Column(db.Integer, db.ForeignKey('robots_clients.id'), primary_key=True)
    software_version_id = db.Column(db.Integer, db.ForeignKey('software_versions.id'), primary_key=True)
    active_configuration_id = db.Column(db.Integer, db.ForeignKey('client_configuration_files.id'))
    
    robot_client = db.relationship("RobotClient", back_populates="software_versions")
    software_version = db.relationship("SoftwareVersion", back_populates="robots")

class ClientConfigurationFile(db.Model):
    __tablename__ = 'client_configuration_files'
    id = db.Column(db.Integer, primary_key=True)
    software_base_configuration_id = db.Column(db.Integer, db.ForeignKey('software_base_configuration_files.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    snapshot_date = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        db.Index('ix_client_software_base_config', 'client_id', 'software_base_configuration_id'),
        db.Index('ix_snapshot_date', 'snapshot_date'),
    )
    
    software_base_configuration = db.relationship("SoftwareBaseConfigurationFile", back_populates="client_configurations")
    client = db.relationship("Client", back_populates="configurations")

class BaseConfigFileParameter(db.Model):
    __tablename__ = 'base_config_file_parameters'
    id = db.Column(db.Integer, primary_key=True)
    in_use = db.Column(db.Boolean, default=True, nullable=False)
    base_config_file_id = db.Column(db.Integer, db.ForeignKey('software_base_configuration_files.id'), nullable=False)
    name = db.Column(db.String(100))
    value = db.Column(db.String(100))
    type = db.Column(db.String(100))
    numeric_rule = db.Column(db.String(10))
    min_value = db.Column(db.Float)
    default_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    regex_rule = db.Column(db.String)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    view_access_level = db.Column(db.Integer, nullable=False, default=0)
    edit_access_level = db.Column(db.Integer, nullable=False, default=0)
    created_by_user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True)
    parameter_group_id = db.Column(db.String(100))
    version = db.Column(db.Integer, default=1)
    
    base_config_file = db.relationship("SoftwareBaseConfigurationFile", back_populates="parameters")
    dependencies = db.relationship("BaseConfigDependence", back_populates="base_config_file_parameter")

class BaseConfigDependence(db.Model):
    __tablename__ = 'base_config_dependances'
    id = db.Column(db.Integer, primary_key=True)
    base_config_file_parameters_id = db.Column(db.Integer, db.ForeignKey('base_config_file_parameters.id'))
    additional_parameters_config_id = db.Column(db.Integer, db.ForeignKey('additional_parameters_config.id'))
    depend_rules_type = db.Column(db.String(100))
    depend_rules = db.Column(db.Text)

    base_config_file_parameter = db.relationship("BaseConfigFileParameter", back_populates="dependencies")
    additional_parameters_config = db.relationship("AdditionalParametersConfig", back_populates="dependencies")

class AdditionalParametersConfig(db.Model):
    __tablename__ = 'additional_parameters_config'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(30)) 
    table_id = db.Column(db.Integer)
    type = db.Column(Enum(ParameterType), nullable=False)
    name = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=True)
    values = db.Column(ARRAY(db.String(255)))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    dependencies = db.relationship("BaseConfigDependence", back_populates="additional_parameters_config")
    additional_parameters = db.relationship("AdditionalParameter", back_populates="additional_parameters_config")
    
    @property
    def value(self):
        if not self.values:
            return None
        if self.type == ParameterType.ENUM:
            return ','.join(self.values)
        return self.values[0] if self.values else None

    @property
    def type_display(self):
        if self.type == ParameterType.TEXT:
            return "Texte"
        elif self.type == ParameterType.NUMERIC:
            return "Nombre"
        elif self.type == ParameterType.ENUM:
            return "Énumération"
        return str(self.type)

    # Méthode pour obtenir les valeurs min/max connues des paramètres existants
    def get_known_min_max(self):
        if self.type != ParameterType.NUMERIC:
            return None, None
            
        numeric_values = []
        for param in self.additional_parameters:
            try:
                numeric_values.append(float(param.value))
            except (ValueError, TypeError):
                pass
                
        if not numeric_values:
            return None, None
            
        return min(numeric_values), max(numeric_values)

class AdditionalParameter(db.Model):
    __tablename__ = 'additional_parameters'
    id = db.Column(db.Integer, primary_key=True)
    additional_parameters_config_id = db.Column(db.Integer, db.ForeignKey('additional_parameters_config.id'))
    name = db.Column(db.String(100))
    value = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    additional_parameters_config = db.relationship("AdditionalParametersConfig", back_populates="additional_parameters")

# Modèle de groupe d'utilisateurs
class UserGroup(db.Model):
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(64), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(128), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    users = db.relationship('User', back_populates='group')
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'

# Modèle utilisateur amélioré
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    access_level = db.Column(db.Integer, default=0)  # 0: minimum, 1: normal, 2: group manager, 3: super admin
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    # Relation avec le groupe
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'))
    group = db.relationship('UserGroup', back_populates='users')
    
    # Relations existantes
    created_parameters = db.relationship("BaseConfigFileParameter", 
                                    foreign_keys="BaseConfigFileParameter.created_by_user_id",
                                    backref="created_by_user")
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_group_manager(self):
        return self.access_level >= 2
    
    def is_super_admin(self):
        return self.access_level >= 3
    
    def __repr__(self):
        return f'<User {self.username}>'
