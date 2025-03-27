# app/models/associations/group_member.py
from datetime import date
from sqlalchemy import ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from app.extensions import db

class GroupMember(db.Model):
    """Association utilisateur-groupe avec rôle et période"""
    __tablename__ = 'group_members'
    
    user_id = db.Column(
        db.Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        primary_key=True,
        comment="ID de l'utilisateur"
    )
    group_id = db.Column(
        db.Integer, 
        ForeignKey('groups.id', ondelete='CASCADE'), 
        primary_key=True,
        comment="ID du groupe"
    )
    role_id = db.Column(
        db.Integer, 
        ForeignKey('roles.id', ondelete='SET NULL'),
        index=True,
        comment="ID du rôle"
    )
    start_date = db.Column(
        db.Date, 
        default=date.today,
        comment="Date de début d'appartenance"
    )
    end_date = db.Column(
        db.Date, 
        nullable=True,
        comment="Date de fin d'appartenance (si applicable)"
    )

    # Relations optimisées
    user = db.relationship(
        "User", 
        back_populates="group_memberships",
        lazy="select"
    )
    
    group = db.relationship(
        "Group", 
        back_populates="members",
        lazy="joined"
    )
    
    role = db.relationship(
        "Role", 
        back_populates="group_assignments",
        lazy="joined"
    )

    __table_args__ = (
        CheckConstraint(
            'end_date IS NULL OR end_date >= start_date',
            name='valid_dates'
        ),
        Index('ix_member_dates', 'start_date', 'end_date'),
    )
