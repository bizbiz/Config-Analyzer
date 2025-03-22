# /app/app/models.py

# Imports de la bibliothèque standard Python
import enum
from sqlalchemy import Enum as SQLAlchemyEnum
import re
import unicodedata
from datetime import datetime
from typing import List, Optional

# Imports de bibliothèques tierces
from flask_login import UserMixin
from sqlalchemy import (
    Enum, 
    ForeignKey, 
    Index, 
    Text, 
    UniqueConstraint, 
    func, 
    select, 
    event, 
    inspect,
    Column,
    Boolean,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.ext.hybrid import hybrid_property

# Imports de modules locaux
from app.extensions import db

def slugify(text, max_length=None):
    """
    Convertit un texte en slug URL-friendly.
    
    Args:
        text: Le texte à convertir
        max_length: Longueur maximale du slug (optionnel)
    
    Returns:
        str: Un slug
    """
    if not text:
        return ""
    
    # Normaliser le texte (enlever les accents)
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    # Convertir en minuscules et supprimer les caractères non autorisés
    text = re.sub(r'[^\w\s-]', '', text.lower())
    # Remplacer les espaces et caractères de séparation par un tiret
    text = re.sub(r'[-\s]+', '-', text).strip('-_')
    
    # Tronquer si une longueur maximale est spécifiée
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text

def generate_model_slug(model_class, instance, text_field, max_length=25, custom_field=None, custom_value=None):
    """
    Génère un slug unique pour n'importe quel modèle, en respectant strictement max_length.
    Permet également d'essayer un slug personnalisé avec un champ supplémentaire avant d'ajouter un compteur.
    
    Args:
        model_class: La classe du modèle (User, UserGroup, etc.)
        instance: L'instance du modèle (pour exclure lors de la vérification d'unicité)
        text_field: Le texte à convertir en slug (username, name, etc.)
        max_length: Longueur maximale du slug
        custom_field: Champ supplémentaire à utiliser pour générer un slug alternatif (optionnel)
        custom_value: Valeur du champ supplémentaire (optionnel)
    
    Returns:
        str: Un slug unique de longueur <= max_length
    """
    # Réserver de l'espace pour le suffixe potentiel "-999"
    suffix_length = 4  
    safe_length = max_length - suffix_length
    
    # Générer le slug de base avec une longueur réduite pour accommoder un éventuel suffixe
    base_slug = slugify(text_field, safe_length)
    slug = base_slug
    
    # Création de la requête avec exclusion de l'instance actuelle si elle a un ID
    query = model_class.query.filter(model_class.slug == slug)
    if hasattr(instance, 'id') and instance.id is not None:
        query = query.filter(model_class.id != instance.id)
    
    # Vérifier si le slug existe déjà
    if query.first():
        # Si un champ personnalisé est fourni, essayer un slug avec ce champ
        if custom_field and custom_value:
            # Calculer l'espace disponible pour chaque partie du slug composé
            combined_safe_length = max_length - suffix_length - 1  # -1 pour le tiret de séparation
            part1_length = int(combined_safe_length * 0.7)  # 70% pour le texte principal
            part2_length = combined_safe_length - part1_length  # Le reste pour le champ personnalisé
            
            # Générer le slug composé
            custom_slug = f"{slugify(text_field, part1_length)}-{slugify(custom_value, part2_length)}"
            
            # Vérifier si ce slug composé existe déjà
            custom_query = model_class.query.filter(model_class.slug == custom_slug)
            if hasattr(instance, 'id') and instance.id is not None:
                custom_query = custom_query.filter(model_class.id != instance.id)
            
            if not custom_query.first():
                return custom_slug
    
        # Si le slug existe ou si le slug composé existe aussi, ajouter un compteur
        counter = 1
        while query.first():
            # Si le compteur atteint 1000, réduire davantage la base pour un suffixe plus long
            if counter == 1000:
                suffix_length += 1
                base_slug = slugify(text_field, max_length - suffix_length)
            
            slug = f"{base_slug}-{counter}"
            counter += 1
            query = model_class.query.filter(model_class.slug == slug)
            if hasattr(instance, 'id') and instance.id is not None:
                query = query.filter(model_class.id != instance.id)
    
    return slug

#Listes prédéfinies pour éviter qu'on puisse ajouter des choses innatendue dans les champs
class ParameterType(str, enum.Enum):
    TEXT = "text"
    NUMERIC = "numeric"
    ENUM = "enum"

class EntityType(enum.Enum):
    CLIENT = "client"
    ROBOT_MODEL = "robot_model"
    SOFTWARE = "software"

#Models
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

@event.listens_for(Client, 'before_insert')
def generate_client_slug_on_insert(mapper, connection, target):
    """Génère automatiquement un slug lors de l'insertion d'un client."""
    if not target.slug:
        custom_value = target.postal_code_relation.code if target.postal_code_relation else None
        target.slug = generate_model_slug(Client, target, target.name, max_length=25, 
                                        custom_field='postal_code', custom_value=custom_value)

@event.listens_for(Client, 'before_update')
def generate_client_slug_on_update(mapper, connection, target):
    """Génère automatiquement un slug lors de la mise à jour d'un client si le nom change."""
    # Vérifier si le nom a été modifié en accédant à l'historique des attributs
    if inspect(target).attrs.name.history.has_changes():
        custom_value = target.postal_code_relation.code if target.postal_code_relation else None
        target.slug = generate_model_slug(Client, target, target.name, max_length=25, 
                                        custom_field='postal_code', custom_value=custom_value)

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

@event.listens_for(RobotModel, 'before_insert')
def set_robot_model_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion."""
    if not target.slug:
        target.slug = generate_model_slug(RobotModel, target, target.name, max_length=25, 
                                         custom_field='company', custom_value=target.company)

@event.listens_for(RobotModel, 'before_update')
def update_robot_model_slug_on_name_change(mapper, connection, target):
    """Met à jour le slug si le nom a changé."""
    state = db.inspect(target)
    if state.attrs.name.history.has_changes():
        target.slug = generate_model_slug(RobotModel, target, target.name, max_length=25,
                                         custom_field='company', custom_value=target.company)

class Software(db.Model):
    __tablename__ = 'software'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    slug = db.Column(db.String(255), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    versions = db.relationship("SoftwareVersion", back_populates="software")
    robot_modeles = db.relationship("RobotModelSoftware", back_populates="software")

@event.listens_for(Software, 'before_insert')
def generate_software_slug_on_insert(mapper, connection, target):
    """Génère automatiquement un slug lors de l'insertion d'un logiciel."""
    if not target.slug:
        # Trouver un robot_model associé pour utiliser comme champ secondaire si disponible
        custom_value = None
        if target.robot_modeles and len(target.robot_modeles) > 0:
            custom_value = target.robot_modeles[0].robot_modele.name
        
        target.slug = generate_model_slug(Software, target, target.name, max_length=255, 
                                         custom_field='robot_model', custom_value=custom_value)

@event.listens_for(Software, 'before_update')
def generate_software_slug_on_update(mapper, connection, target):
    """Génère automatiquement un slug lors de la mise à jour d'un logiciel si le nom change."""
    # Vérifier si le nom a été modifié
    if inspect(target).attrs.name.history.has_changes():
        # Trouver un robot_model associé pour utiliser comme champ secondaire si disponible
        custom_value = None
        if target.robot_modeles and len(target.robot_modeles) > 0:
            custom_value = target.robot_modeles[0].robot_modele.name
        
        target.slug = generate_model_slug(Software, target, target.name, max_length=255, 
                                         custom_field='robot_model', custom_value=custom_value)

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
    slug = db.Column(db.String(50), nullable=False, unique=True, index=True)  # Ajout de la colonne slug
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    __table_args__ = (db.UniqueConstraint('software_id', 'version', name='unique_version_per_software'),)
    
    software = db.relationship("Software", back_populates="versions")
    base_configurations = db.relationship("SoftwareBaseConfigurationFile", back_populates="software_version")
    robots = db.relationship("RobotClientSoftwareVersion", back_populates="software_version")

@event.listens_for(SoftwareVersion, 'before_insert')
def set_software_version_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion d'une version de logiciel."""
    if not target.slug:
        # Utiliser le nom du logiciel comme champ secondaire
        custom_value = target.software.name if target.software else None
        # Créer un slug qui combine la version et le nom du logiciel
        target.slug = generate_model_slug(
            SoftwareVersion, 
            target, 
            target.version, 
            max_length=25, 
            custom_field='software_name', 
            custom_value=custom_value
        )

@event.listens_for(SoftwareVersion, 'before_update')
def update_software_version_slug_on_change(mapper, connection, target):
    """Met à jour le slug si la version a changé."""
    state = db.inspect(target)
    if state.attrs.version.history.has_changes() or state.attrs.software_id.history.has_changes():
        # Utiliser le nom du logiciel comme champ secondaire
        custom_value = target.software.name if target.software else None
        # Créer un slug qui combine la version et le nom du logiciel
        target.slug = generate_model_slug(
            SoftwareVersion, 
            target, 
            target.version, 
            max_length=25, 
            custom_field='software_name', 
            custom_value=custom_value
        )


class SoftwareBaseConfigurationFile(db.Model):
    __tablename__ = 'software_base_configuration_files'
    id = db.Column(db.Integer, primary_key=True)
    software_version_id = db.Column(db.Integer, db.ForeignKey('software_versions.id'), nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(50), nullable=False, unique=True, index=True)  # Ajout de la colonne slug
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

@event.listens_for(SoftwareBaseConfigurationFile, 'before_insert')
def set_base_config_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion d'un fichier de configuration de base."""
    if not target.slug:
        # Utiliser le nom de la version du logiciel comme champ secondaire
        custom_value = None
        if target.software_version and target.software_version.software:
            custom_value = f"{target.software_version.software.name}-{target.software_version.version}"
        
        target.slug = generate_model_slug(
            SoftwareBaseConfigurationFile, 
            target, 
            target.file_name, 
            max_length=25, 
            custom_field='software_version', 
            custom_value=custom_value
        )

@event.listens_for(SoftwareBaseConfigurationFile, 'before_update')
def update_base_config_slug_on_change(mapper, connection, target):
    """Met à jour le slug si le nom du fichier ou la version du logiciel a changé."""
    state = db.inspect(target)
    if state.attrs.file_name.history.has_changes() or state.attrs.software_version_id.history.has_changes():
        # Utiliser le nom de la version du logiciel comme champ secondaire
        custom_value = None
        if target.software_version and target.software_version.software:
            custom_value = f"{target.software_version.software.name}-{target.software_version.version}"
        
        target.slug = generate_model_slug(
            SoftwareBaseConfigurationFile, 
            target, 
            target.file_name, 
            max_length=25, 
            custom_field='software_version', 
            custom_value=custom_value
        )


class RobotClient(db.Model):
    __tablename__ = 'robots_clients'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    robot_modele_id = db.Column(db.Integer, db.ForeignKey('robots_modeles.id'), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(50), nullable=False, unique=True, index=True)  # Ajout de la colonne slug
    length = db.Column(db.Float)
    height = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
 
    client = db.relationship("Client", back_populates="robots")
    robot_modele = db.relationship("RobotModel", back_populates="clients")
    software_versions = db.relationship("RobotClientSoftwareVersion", back_populates="robot_client")

@event.listens_for(RobotClient, 'before_insert')
def set_robot_client_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion d'un robot client."""
    if not target.slug:
        # Utiliser le nom du client et du modèle de robot comme champ secondaire
        custom_value = None
        if target.client and target.robot_modele:
            custom_value = f"{target.client.name}-{target.robot_modele.name}"
        
        target.slug = generate_model_slug(
            RobotClient, 
            target, 
            target.serial_number, 
            max_length=25, 
            custom_field='client_robot', 
            custom_value=custom_value
        )

@event.listens_for(RobotClient, 'before_update')
def update_robot_client_slug_on_change(mapper, connection, target):
    """Met à jour le slug si le numéro de série, le client ou le modèle a changé."""
    state = db.inspect(target)
    if (state.attrs.serial_number.history.has_changes() or 
            state.attrs.client_id.history.has_changes() or 
            state.attrs.robot_modele_id.history.has_changes()):
        
        # Utiliser le nom du client et du modèle de robot comme champ secondaire
        custom_value = None
        if target.client and target.robot_modele:
            custom_value = f"{target.client.name}-{target.robot_modele.name}"
        
        target.slug = generate_model_slug(
            RobotClient, 
            target, 
            target.serial_number, 
            max_length=25, 
            custom_field='client_robot', 
            custom_value=custom_value
        )

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
    slug = db.Column(db.String(50), nullable=False, unique=True, index=True)  # Ajout de la colonne slug
    snapshot_date = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        db.Index('ix_client_software_base_config', 'client_id', 'software_base_configuration_id'),
        db.Index('ix_snapshot_date', 'snapshot_date'),
    )
    
    software_base_configuration = db.relationship("SoftwareBaseConfigurationFile", back_populates="client_configurations")
    client = db.relationship("Client", back_populates="configurations")

@event.listens_for(ClientConfigurationFile, 'before_insert')
def set_client_config_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion d'un fichier de configuration client."""
    if not target.slug:
        # Générer un texte de base pour le slug
        base_text = f"config"
        if target.client:
            base_text = f"{target.client.name}-config"
        
        # Utiliser le nom du client et la date comme valeur secondaire
        custom_value = None
        if target.client and target.software_base_configuration:
            date_str = target.snapshot_date.strftime("%Y%m%d")
            file_name = target.software_base_configuration.file_name if hasattr(target.software_base_configuration, 'file_name') else "config"
            custom_value = f"{file_name}-{date_str}"
        
        target.slug = generate_model_slug(
            ClientConfigurationFile, 
            target, 
            base_text, 
            max_length=25, 
            custom_field='file_date', 
            custom_value=custom_value
        )

@event.listens_for(ClientConfigurationFile, 'before_update')
def update_client_config_slug_on_change(mapper, connection, target):
    """Met à jour le slug si le client, la configuration de base ou la date a changé."""
    state = db.inspect(target)
    if (state.attrs.client_id.history.has_changes() or 
            state.attrs.software_base_configuration_id.history.has_changes() or 
            state.attrs.snapshot_date.history.has_changes()):
        
        # Générer un texte de base pour le slug
        base_text = f"config"
        if target.client:
            base_text = f"{target.client.name}-config"
        
        # Utiliser le nom du client et la date comme valeur secondaire
        custom_value = None
        if target.client and target.software_base_configuration:
            date_str = target.snapshot_date.strftime("%Y%m%d")
            file_name = target.software_base_configuration.file_name if hasattr(target.software_base_configuration, 'file_name') else "config"
            custom_value = f"{file_name}-{date_str}"
        
        target.slug = generate_model_slug(
            ClientConfigurationFile, 
            target, 
            base_text, 
            max_length=25, 
            custom_field='file_date', 
            custom_value=custom_value
        )


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
    target_entity = db.Column(SQLAlchemyEnum(EntityType), nullable=True)
    applicable_ids = db.Column(ARRAY(db.Integer), default=[], nullable=False)
    type = db.Column(SQLAlchemyEnum(ParameterType), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    configuration_values = db.Column(db.ARRAY(db.String(255)), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint(
            "(target_entity IS NULL AND applicable_ids = '{}') OR "
            "(target_entity IS NOT NULL AND applicable_ids = '{}') OR "
            "(target_entity IS NOT NULL AND applicable_ids != '{}')",
            name='check_application_scope'
        ),
        db.Index('idx_target_entity', 'target_entity')
    )

    # Relations et timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    dependencies = db.relationship("BaseConfigDependence", back_populates="additional_parameters_config")
    additional_parameters = db.relationship("AdditionalParameter", back_populates="additional_parameters_config")

    @property
    def value(self):
        if not self.configuration_values:
            return None
        if self.type == ParameterType.ENUM:
            return ','.join(self.configuration_values)
        return self.configuration_values[0] if self.configuration_values else None

    @property
    def type_display(self):
        if self.type == ParameterType.TEXT:
            return "Texte"
        elif self.type == ParameterType.NUMERIC:
            return "Nombre"
        elif self.type == ParameterType.ENUM:
            return "Énumération"
        return str(self.type)

    def get_known_min_max(self):
        if self.type != ParameterType.NUMERIC:
            return None, None
            
        numeric_values = []
        for param in self.additional_parameters:
            try:
                numeric_values.append(float(param.value))
            except (ValueError, TypeError):
                pass
                
        return (min(numeric_values), max(numeric_values)) if numeric_values else (None, None)


class AdditionalParameter(db.Model):
    __tablename__ = 'additional_parameters'
    id = db.Column(db.Integer, primary_key=True)
    additional_parameters_config_id = db.Column(db.Integer, db.ForeignKey('additional_parameters_config.id'))
    value = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)  # Nouveau champ booléen
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    additional_parameters_config = db.relationship("AdditionalParametersConfig", back_populates="additional_parameters")

# Modèle de groupe d'utilisateurs
class UserGroup(db.Model):
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    description = db.Column(db.Text)

    users = db.relationship('User', back_populates='group')
    
    def generate_slug(self):
        """Génère un slug unique basé sur le nom du groupe."""
        return generate_model_slug(UserGroup, self, self.name)

# Écouteurs d'événements pour UserGroup
@event.listens_for(UserGroup, 'before_insert')
def set_user_group_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion."""
    target.slug = target.generate_slug()

@event.listens_for(UserGroup, 'before_update')
def update_user_group_slug_on_name_change(mapper, connection, target):
    """Met à jour le slug si le nom du groupe a changé."""
    state = db.inspect(target)
    if state.attrs.name.history.has_changes():
        target.slug = target.generate_slug()


# Modèle utilisateur
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    access_level = db.Column(db.Integer, default=0)  # 0: minimum, 1: normal, 2: group manager, 3: group admin, 4: super admin
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Réduit à 50 caractères, cohérent avec max_length=25
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'))
    group = db.relationship('UserGroup', back_populates='users')
    
    # Relation avec les rôles pour une autorisation plus flexible
    roles = db.relationship('Role', secondary='user_roles')

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

# Écouteurs d'événements pour User
@event.listens_for(User, 'before_insert')
def set_user_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion d'un utilisateur."""
    if not target.slug:
        # Utiliser l'email comme champ secondaire
        target.slug = generate_model_slug(
            User, 
            target, 
            target.username, 
            max_length=25, 
            custom_field='email', 
            custom_value=target.email
        )

@event.listens_for(User, 'before_update')
def update_user_slug_on_username_change(mapper, connection, target):
    """Met à jour le slug si le nom d'utilisateur a changé."""
    state = db.inspect(target)
    if state.attrs.username.history.has_changes():
        target.slug = generate_model_slug(
            User, 
            target, 
            target.username, 
            max_length=25, 
            custom_field='email', 
            custom_value=target.email
        )

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Ajout de la colonne slug
    description = db.Column(db.String(255))
    
    users = db.relationship('User', secondary='user_roles')

# Écouteurs d'événements pour Role
@event.listens_for(Role, 'before_insert')
def set_role_slug_before_insert(mapper, connection, target):
    """Définit le slug avant l'insertion d'un rôle."""
    if not target.slug:
        target.slug = generate_model_slug(
            Role, 
            target, 
            target.name, 
            max_length=25
        )

@event.listens_for(Role, 'before_update')
def update_role_slug_on_name_change(mapper, connection, target):
    """Met à jour le slug si le nom du rôle a changé."""
    state = db.inspect(target)
    if state.attrs.name.history.has_changes():
        target.slug = generate_model_slug(
            Role, 
            target, 
            target.name, 
            max_length=25
        )


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
