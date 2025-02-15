from sqlalchemy import ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.sql import func
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

    __table_args__ = (db.UniqueConstraint('software_version_id', 'file_name', name='unique_base_config_per_version'),)

    software_version = db.relationship("SoftwareVersion", back_populates="base_configurations")
    client_configurations = db.relationship("ClientConfigurationFile", back_populates="software_base_configuration")

class RobotClient(db.Model):
    __tablename__ = 'robots_clients'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    robot_modele_id = db.Column(db.Integer, db.ForeignKey('robots_modeles.id'), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    length = db.Column(db.Integer)
    height = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (db.Index('ix_client_robot', 'client_id', 'robot_modele_id'),)
    
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