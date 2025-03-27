# app/models/entities/client.py
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import Entity, configure_slug_generation
from app.models.basic.postal_code import PostalCode

@configure_slug_generation
class Client(Entity):
    """Modèle Client héritant de la base polymorphique Entity"""
    __mapper_args__ = {'polymorphic_identity': EntityType.CLIENT}
    
    # Configuration du slug
    slug_source_field = 'name'
    CUSTOM_SLUG_FIELD = 'postal_code_relation.code'

    # Colonnes spécifiques
    postal_code_id = db.Column(
        db.Integer, 
        ForeignKey('postal_codes.id', ondelete='RESTRICT'), 
        nullable=False,
        index=True,
        comment="Clé étrangère vers la table des codes postaux"
    )
    
    # Relations optimisées
    postal_code_relation = db.relationship(
        PostalCode,
        back_populates='clients',
        lazy='joined',
        innerjoin=True
    )
    
    robots = db.relationship(
        "RobotInstance",
        back_populates="client",
        cascade='all, delete-orphan',
        order_by='RobotInstance.created_at.desc()',
        lazy='dynamic',
        passive_deletes=True
    )

    __table_args__ = (
        db.Index('idx_client_slug', 'slug', unique=True),
        db.Index('idx_client_postal', 'postal_code_id', 'name'),
    )
