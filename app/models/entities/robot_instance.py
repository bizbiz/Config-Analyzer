# app/models/entities/robot_instance.py
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import validates, relationship, declared_attr
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation

@configure_slug_generation
class RobotInstance(SpecificEntity):
    """Instance concrète d'un robot chez un client"""
    __mapper_args__ = {'polymorphic_identity': EntityType.ROBOT_INSTANCE}

    __tablename__ = 'robotinstance'
    
    slug_source_field = 'client_robot'
    CUSTOM_SLUG_FIELD = 'serial_number'

    # Colonnes spécifiques
    serial_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    
    # Clés étrangères
    client_id = db.Column(
        db.Integer, 
        db.ForeignKey('client.id', ondelete='CASCADE'),  # Référence à la table enfant
        nullable=False, 
        index=True
    )
    robot_model_id = db.Column(db.Integer, ForeignKey('robotmodel.id', ondelete='RESTRICT'), nullable=False, index=True)

    # Relations
    client = db.relationship(
        "Client", 
        foreign_keys=[client_id],
        back_populates="robots",
        primaryjoin="Client.id == RobotInstance.client_id"  # Jointure explicite
    )
    model = db.relationship(
        "RobotModel", 
        back_populates="instances",
        foreign_keys=[robot_model_id]  # Déclaration explicite
    )
    software_versions = db.relationship(
        "RobotInstanceSoftwareVersion",
        back_populates="robot_instance",
        cascade="all, delete-orphan",
        order_by="RobotInstanceSoftwareVersion.installation_date.desc()"
    )

    __table_args__ = (
        Index('ix_robot_serial_client', 'serial_number', 'client_id'),
    )

    @property
    def client_robot(self):
        """Propriété calculée pour le slug"""
        if self.client and self.model:
            return f"{self.client.name}-{self.model.name}"
        return None

    @validates('serial_number')
    def validate_serial_number(self, key, serial):
        if len(serial) < 5:
            raise ValueError("Le numéro de série doit contenir au moins 5 caractères")
        return serial.upper()

    def __repr__(self):
        return f'<RobotInstance {self.serial_number} ({self.slug})>'
