# app/models/configuration.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, event
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import Entity
from app.models.parameters import ParameterValue, ParameterDefinition, FloatParameterDefinition
from app.models.associations.configuration_entity_link import ConfigurationEntityLink

class ConfigurationInstance(db.Model):
    """Fichier de configuration brut + paramètres associés"""
    __tablename__ = 'configuration_instances'
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False)
    entity_type = Column(db.Enum(EntityType), nullable=False)
    file_hash = Column(String(64), unique=True)
    file_name = Column(String(100), nullable=False)
    file_path = Column(String(255))
    raw_content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    parameters = relationship("ParameterValue", back_populates="configuration_instance", cascade="all, delete-orphan")
    entity_links = relationship(
        'ConfigurationEntityLink',
        back_populates='configuration',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    schema = relationship("ConfigSchema", back_populates="configuration_instances")

    __table_args__ = (
        Index('idx_entity_config', 'entity_id', 'entity_type'),
    )

    @property
    def client_configurations(self):
        return [pv for pv in self.parameters if pv.definition.target_entity == EntityType.CLIENT]

    @property
    def active_parameters(self):
        return [pv for pv in self.parameters if pv.is_active]

    @property
    def last_modified(self):
        param_dates = [pv.updated_at for pv in self.parameters if pv.updated_at]
        return max(param_dates) if param_dates else self.updated_at

    def extract_parameters(self):
        parser = ConfigFileParser(self)
        for name, value in parser.parse():
            definition = ParameterDefinition.query.filter_by(name=name).first()
            if not definition:
                definition = self._create_definition(name, value)
            
            ParameterValue.create(
                definition=definition,
                value=value,
                config_instance=self
            )
    
    def _create_definition(self, name, value):
        if value.isdigit():
            return FloatParameterDefinition(name=name)
        # Ajouter d'autres types si nécessaire

    def validate(self):
        for pv in self.parameters:
            if not pv.definition.validate(pv.value):
                raise InvalidParameterError(f"Valeur invalide pour {pv.definition.name}")

    @hybrid_property
    def linked_entities(self):
        """Retourne toutes les entités liées de manière polymorphique"""
        return [link.resolve_entity() for link in self.entity_links]

    def link_entity(self, entity):
        """Ajoute une liaison à une entité"""
        if any(l.entity_id == entity.id and l.entity_type == entity.entity_type.value for l in self.entity_links):
            raise ValueError("Entité déjà liée")
        self.entity_links.append(
            ConfigurationEntityLink(
                entity_type=entity.entity_type.value,
                entity_id=entity.id
            )
        )

    def unlink_entity(self, entity):
        """Retire une liaison à une entité"""
        link = next(
            (l for l in self.entity_links 
             if l.entity_type == entity.entity_type.value and l.entity_id == entity.id),
            None
        )
        if link:
            self.entity_links.remove(link)

class ConfigFileParser:
    def __init__(self, config_instance):
        self.raw_content = config_instance.raw_content
        
    def parse(self):
        for line in self.raw_content.split('\n'):
            if '=' in line:
                name, value = line.split('=', 1)
                yield name.strip(), value.strip()

class ConfigSchema(db.Model):
    __tablename__ = 'config_schemas'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    file_pattern = Column(String(100), nullable=False)
    parser_class = Column(String(100), nullable=False)
    
    configuration_instances = relationship("ConfigurationInstance", back_populates="schema")

@event.listens_for(ConfigurationEntityLink, 'before_insert')
@event.listens_for(ConfigurationEntityLink, 'before_update')
def validate_entity_ref(mapper, connection, target):
    entity_class = Entity.get_polymorphic_class(EntityType(target.entity_type))
    if not entity_class.query.get(target.entity_id):
        raise ValueError(f"Entité {target.entity_type}:{target.entity_id} introuvable")
