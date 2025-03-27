# app/models/entities/group.py
from sqlalchemy import event
from sqlalchemy.orm import validates
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation

@configure_slug_generation
class Group(SpecificEntity):
    """Groupe d'utilisateurs avec capacités polymorphiques"""
    __tablename__ = 'groups'
    __mapper_args__ = {'polymorphic_identity': EntityType.GROUP}
    
    # Configuration du slug double
    slug_source_field = 'name'
    CUSTOM_SLUG_FIELD = 'owner.username'  # Fallback sur le nom du propriétaire

    # Colonnes spécifiques
    name = db.Column(
        db.String(100), 
        nullable=False,
        index=True,
        comment="Nom unique du groupe"
    )
    description = db.Column(
        db.Text,
        comment="Description détaillée du groupe"
    )
    
    # Relations
    owner_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        index=True
    )
    owner = db.relationship(
        "User", 
        back_populates="owned_groups",
        lazy='joined'
    )
    members = db.relationship(
        "GroupMember", 
        back_populates="group",
        cascade='all, delete-orphan',
        order_by='GroupMember.start_date.desc()',
        lazy='dynamic'
    )

    @validates('name')
    def validate_name(self, key, name):
        """Valide le nom avant sauvegarde"""
        if len(name) < 3:
            raise ValueError("Le nom du groupe doit contenir au moins 3 caractères")
        return name

    def generate_slug(self):
        """Génère un slug combinant nom et propriétaire"""
