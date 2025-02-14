from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, UniqueConstraint, Index, CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PostalCode(Base):
    __tablename__ = 'postal_codes'
    code = Column(String(10), primary_key=True)
    city = Column(String(255), nullable=False)
    country_code = Column(CHAR(2), nullable=False)


class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    postal_code = Column(String(10), ForeignKey('postal_codes.code'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    postal_code_relation = relationship("PostalCode", back_populates="clients")


class RobotModel(Base):
    __tablename__ = 'robots_modeles'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    company = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Software(Base):
    __tablename__ = 'software'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RobotModelSoftware(Base):
    __tablename__ = 'robots_modeles_software'
    robot_modele_id = Column(Integer, ForeignKey('robots_modeles.id'), primary_key=True)
    software_id = Column(Integer, ForeignKey('software.id'), primary_key=True)

    robot_modele = relationship("RobotModel", back_populates="software")
    software = relationship("Software", back_populates="robot_modeles")


class SoftwareVersion(Base):
    __tablename__ = 'software_versions'
    id = Column(Integer, primary_key=True)
    software_id = Column(Integer, ForeignKey('software.id'), nullable=False)
    version = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('software_id', 'version', name='unique_version_per_software'),)

    software = relationship("Software", back_populates="versions")


class SoftwareBaseConfigurationFile(Base):
    __tablename__ = 'software_base_configuration_files'
    id = Column(Integer, primary_key=True)
    software_version_id = Column(Integer, ForeignKey('software_versions.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('software_version_id', name='unique_base_config_per_version'),)

    software_version = relationship("SoftwareVersion", back_populates="base_configurations")


class RobotClient(Base):
    __tablename__ = 'robots_clients'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    robot_modele_id = Column(Integer, ForeignKey('robots_modeles.id'), nullable=False)
    serial_number = Column(String(50), nullable=False, unique=True)
    length = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index('ix_client_robot', 'client_id', 'robot_modele_id'),)

    client = relationship("Client", back_populates="robots")
    robot_modele = relationship("RobotModel", back_populates="clients")


class RobotClientSoftwareVersion(Base):
    __tablename__ = 'robots_clients_software_versions'
    robot_client_id = Column(Integer, ForeignKey('robots_clients.id'), primary_key=True)
    software_version_id = Column(Integer, ForeignKey('software_versions.id'), primary_key=True)
    active_configuration_id = Column(Integer, ForeignKey('client_configuration_files.id'))

    robot_client = relationship("RobotClient", back_populates="software_versions")
    software_version = relationship("SoftwareVersion", back_populates="robots")


class ClientConfigurationFile(Base):
    __tablename__ = 'client_configuration_files'
    id = Column(Integer, primary_key=True)
    software_base_configuration_id = Column(Integer, ForeignKey('software_base_configuration_files.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    content = Column(Text, nullable=False)
    snapshot_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_client_software_base_config', 'client_id', 'software_base_configuration_id'),
        Index('ix_snapshot_date', 'snapshot_date'),
    )

    software_base_configuration = relationship("SoftwareBaseConfigurationFile", back_populates="client_configurations")
    client = relationship("Client", back_populates="configurations")

# Establish relationships
PostalCode.clients = relationship("Client", order_by=Client.id, back_populates="postal_code_relation")
Client.robots = relationship("RobotClient", order_by=RobotClient.id, back_populates="client")
Client.configurations = relationship("ClientConfigurationFile", order_by=ClientConfigurationFile.id, back_populates="client")
RobotModel.software = relationship("RobotModelSoftware", order_by=RobotModelSoftware.robot_modele_id, back_populates="robot_modele")
RobotModel.clients = relationship("RobotClient", order_by=RobotClient.id, back_populates="robot_modele")
Software.versions = relationship("SoftwareVersion", order_by=SoftwareVersion.id, back_populates="software")
Software.robot_modeles = relationship("RobotModelSoftware", order_by=RobotModelSoftware.software_id, back_populates="software")
SoftwareVersion.base_configurations = relationship("SoftwareBaseConfigurationFile", order_by=SoftwareBaseConfigurationFile.id, back_populates="software_version")
SoftwareVersion.robots = relationship("RobotClientSoftwareVersion", order_by=RobotClientSoftwareVersion.software_version_id, back_populates="software_version")
SoftwareBaseConfigurationFile.client_configurations = relationship("ClientConfigurationFile", order_by=ClientConfigurationFile.id, back_populates="software_base_configuration")
RobotClient.software_versions = relationship("RobotClientSoftwareVersion", order_by=RobotClientSoftwareVersion.robot_client_id, back_populates="robot_client")