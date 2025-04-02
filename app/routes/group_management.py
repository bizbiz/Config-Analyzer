# app/routes/group_management.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.entities.group import Group
from app.models.entities.user import User
from app.models.associations.group_member import GroupMember
from app.auth import super_admin_required, group_admin_required

# Création du Blueprint pour les groupes
group_management_bp = Blueprint('group_management', __name__, url_prefix='/admin/groups')

@group_management_bp.route('/list')
@login_required
@group_admin_required
def list_groups():
    """Liste des groupes (tous pour super admin, uniquement le sien pour admin)"""
    if current_user.is_super_admin():  # Super admin
        groups = Group.query.all()
    else:  # Group admin
        groups = [gm.group for gm in current_user.groups]
    
    return render_template('group_management/group_list.html', groups=groups)

@group_management_bp.route('/view/<slug>')
@login_required
@group_admin_required
def view_group(slug):
    """Afficher les détails d'un groupe"""
    group = Group.query.filter_by(slug=slug).first_or_404()
    
    # Vérifier que l'utilisateur courant a le droit de voir ce groupe
    if not current_user.is_super_admin() and not any(gm.group_id == group.id for gm in current_user.groups):
        abort(403)  # Forbidden
    
    group_members = GroupMember.query.filter_by(group_id=group.id).all()
    
    return render_template('group_management/group_view.html', group=group, members=group_members)

@group_management_bp.route('/add', methods=['GET', 'POST'])
@login_required
@super_admin_required
def add_group():
    """Ajouter un nouveau groupe (réservé aux super admins)"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        try:
            group = Group(
                name=name,
                description=description,
                owner_id=current_user.id
            )
            
            db.session.add(group)
            db.session.commit()
            
            # Ajouter automatiquement le créateur comme membre du groupe
            member = GroupMember(
                user_id=current_user.id,
                group_id=group.id,
                is_admin=True
            )
            db.session.add(member)
            db.session.commit()
            
            flash("Groupe créé avec succès.", "success")
            return redirect(url_for('group_management.list_groups'))
            
        except IntegrityError:
            db.session.rollback()
            flash("Un groupe avec ce nom existe déjà.", "error")
    
    return render_template('group_management/group_add.html')

@group_management_bp.route('/edit/<slug>', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_group(slug):
    """Modifier un groupe existant (réservé aux super admins)"""
    group = Group.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.description = request.form.get('description', '')
        
        try:
            db.session.commit()
            flash("Groupe mis à jour avec succès.", "success")
            return redirect(url_for('group_management.list_groups'))
        except IntegrityError:
            db.session.rollback()
            flash("Un groupe avec ce nom existe déjà.", "error")
    
    return render_template('group_management/group_edit.html', group=group)

@group_management_bp.route('/delete/<slug>', methods=['POST'])
@login_required
@super_admin_required
def delete_group(slug):
    """Supprimer un groupe (réservé aux super admins)"""
    group = Group.query.filter_by(slug=slug).first_or_404()
    
    # Vérifier si le groupe a des membres
    if GroupMember.query.filter_by(group_id=group.id).count() > 0:
        flash("Ce groupe contient des utilisateurs et ne peut pas être supprimé.", "error")
        return redirect(url_for('group_management.list_groups'))
    
    try:
        db.session.delete(group)
        db.session.commit()
        flash("Groupe supprimé avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    return redirect(url_for('group_management.list_groups'))
