# app/models/basic/postal_code.py
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.extensions import db

class PostalCode(db.Model):
    """Modèle pour la gestion des codes postaux internationaux"""
    __tablename__ = 'postal_codes'
    
    id = db.Column(
        db.Integer, 
        primary_key=True,
        comment="Identifiant unique auto-incrémenté"
    )
    code = db.Column(
        db.String(20), 
        nullable=False,
        index=True,
        comment="Code postal (format variable selon pays)"
    )
    city = db.Column(
        db.String(100), 
        nullable=False,
        index=True,
        comment="Nom de la ville officiel"
    )
    country_code = db.Column(
        db.String(3),  # ISO 3166-1 alpha-3
        nullable=False,
        index=True,
        comment="Code pays ISO 3 lettres"
    )

    # Relation avec les clients
    clients = db.relationship(
        'Client', 
        back_populates='postal_code_relation',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        # Contrainte d'unicité combinée
        db.UniqueConstraint(
            'code', 
            'city', 
            'country_code', 
            name='uq_postal_code_full'
        ),
        # Validation des données
        CheckConstraint(
            'LENGTH(code) BETWEEN 3 AND 10', 
            name='ck_postal_code_length'
        ),
        CheckConstraint(
            'LENGTH(country_code) = 3', 
            name='ck_country_code_length'
        ),
        Index('idx_country_city', 'country_code', 'city'),
        {'comment': 'Table de référence des codes postaux internationaux'}
    )

    def __repr__(self):
        return f'<PostalCode {self.code} {self.city} [{self.country_code}]>'

    @property
    def formatted_address(self):
        """Retourne l'adresse formatée selon les standards postaux"""
        return f"{self.code} {self.city}, {self.country_code}"

    def to_dict(self):
        """Sérialisation pour les API"""
        return {
            'id': self.id,
            'code': self.code,
            'city': self.city,
            'country_code': self.country_code
        }