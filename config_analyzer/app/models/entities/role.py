# app/models/entities/role.py
from sqlalchemy import Column, String, JSON
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import SpecificEntity, configure_slug_generation

@configure_slug_generation
class Role(SpecificEntity):
    """Rôle applicatif avec gestion polymorphique"""
    __mapper_args__ = {'polymorphic_identity': EntityType.ROLE}
    
    # Colonnes spécifiques
    name = Column(String(50), unique=True, nullable=False, index=True)
    permissions = Column(JSON, comment="Stockage flexible des droits")

    def __repr__(self):
        return f'<Role {self.name}>'

    @property
    def permission_list(self):
        """Retourne la liste des permissions sous forme de liste"""
        return self.permissions.keys() if self.permissions else []

    def has_permission(self, permission):
        """Vérifie si le rôle a une permission spécifique"""
        return permission in self.permission_list

    def add_permission(self, permission, value=True):
        """Ajoute une permission au rôle"""
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission] = value
        db.session.add(self)
        db.session.commit()

    def remove_permission(self, permission):
        """Supprime une permission du rôle"""
        if self.permissions and permission in self.permissions:
            del self.permissions[permission]
            db.session.add(self)
            db.session.commit()
