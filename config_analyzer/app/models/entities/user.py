# app/models/entities/user.py
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.enums import EntityType
from app.models.base import Entity, configure_slug_generation


@configure_slug_generation
class User(Entity):
    """Utilisateur du système avec gestion polymorphique étendue"""
    __mapper_args__ = {'polymorphic_identity': EntityType.USER}
    
    slug_source_field = 'username'
    CUSTOM_SLUG_FIELD = 'email'

    # Colonnes spécifiques
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128))
    access_level = Column(Integer, default=0)
    
    # Relations
    groups = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    owned_groups = relationship("Group", back_populates="owner", lazy='dynamic')
    
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

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'access_level': self.access_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
