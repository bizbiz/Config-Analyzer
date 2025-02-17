from sqlalchemy import ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select, func
from app.extensions import db

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
    postal_code_id = db.Column(db.Integer, db.ForeignKey('postal_codes.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    postal_code_relation = db.relationship('PostalCode', back_populates='clients')
    robots = db.relationship('RobotClient', back_populates='client')
    configurations = db.relationship('ClientConfigurationFile', back_populates='client')

    def __repr__(self):
        return f'<Client {self.name}>'

class RobotModel(db.Model):
    __tablename__ = 'robots_modeles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    company = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    software = db.relationship("RobotModelSoftware", back_populates="robot_modele")
    clients = db.relationship("RobotClient", back_populates="robot_modele")

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
    in_use = db.Column(db.Boolean, nullable=False)
    base_config_file_id = db.Column(db.Integer, db.ForeignKey('software_base_configuration_files.id'), nullable=False)
    name = db.Column(db.String(100))
    value = db.Column(db.String(100))
    is_numeric_values = db.Column(db.Boolean)
    numeric_rule = db.Column(db.String(10))  # =, between, <, >, <=, >=, empty
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    is_text_value = db.Column(db.Boolean)
    regex_rule = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    base_config_file = db.relationship("SoftwareBaseConfigurationFile", back_populates="parameters")
    dependencies = db.relationship("BaseConfigDependence", back_populates="base_config_file_parameter")

class BaseConfigDependence(db.Model):
    __tablename__ = 'base_config_dependances'
    id = db.Column(db.Integer, primary_key=True)
    base_config_file_parameters_id = db.Column(db.Integer, db.ForeignKey('base_config_file_parameters.id'))
    additional_parameters_config_id = db.Column(db.Integer, db.ForeignKey('additional_parameters_config.id'))
    depend_rules_type = db.Column(db.String(100))  # numeric or regex
    depend_rules = db.Column(db.Text)

    base_config_file_parameter = db.relationship("BaseConfigFileParameter", back_populates="dependencies")
    additional_parameters_config = db.relationship("AdditionalParametersConfig", back_populates="dependencies")

class AdditionalParametersConfig(db.Model):
    __tablename__ = 'additional_parameters_config'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(30))  # clients, robot_clients, software_versions, robot_modeles
    table_id = db.Column(db.Integer)
    type = db.Column(db.String(20))  # numeric, text

    dependencies = db.relationship("BaseConfigDependence", back_populates="additional_parameters_config")
    additional_parameters = db.relationship("AdditionalParameter", back_populates="additional_parameters_config")

class AdditionalParameter(db.Model):
    __tablename__ = 'additional_parameters'
    id = db.Column(db.Integer, primary_key=True)
    additional_parameters_config_id = db.Column(db.Integer, db.ForeignKey('additional_parameters_config.id'))
    name = db.Column(db.String(100))
    value = db.Column(db.String(255))

    additional_parameters_config = db.relationship("AdditionalParametersConfig", back_populates="additional_parameters")