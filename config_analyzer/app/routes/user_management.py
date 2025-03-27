# app/routes/user_management.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.entities.user import User
from app.models.entities.group import Group
from app.models.entities.role import Role
from app.models.associations.group_member import GroupMember
from app.auth import super_admin_required, group_admin_required, group_manager_required

user_management_bp = Blueprint('user_management', __name__, url_prefix='/admin/users')

@user_management_bp.route('/list')
@login_required
@group_manager_required
def list_users():
    if current_user.is_super_admin():
        users = User.query.all()
    elif current_user.is_group_manager():
        user_groups = [gm.group for gm in current_user.groups if gm.is_admin]
        users = User.query.join(GroupMember).filter(GroupMember.group_id.in_([g.id for g in user_groups])).all()
    
    return render_template('user_management/user_list.html', users=users)

@user_management_bp.route('/view/<slug>')
@login_required
@group_manager_required
def view_user(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    
    if not current_user.is_super_admin() and not any(gm.group_id == user.group_id for gm in current_user.groups):
        abort(403)
    
    return render_template('user_management/user_view.html', user=user)

@user_management_bp.route('/add', methods=['GET', 'POST'])
@login_required
@group_manager_required
def add_user():
    groups = Group.query.all() if current_user.is_super_admin() else [gm.group for gm in current_user.groups if gm.is_admin]
    roles = Role.query.all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        group_id = request.form.get('group_id', type=int)
        access_level = request.form.get('access_level', type=int, default=1)
        
        # Validations
        form_data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'group_id': group_id,
            'access_level': access_level
        }
        
        # Valider que le niveau d'accès est inférieur à celui de l'utilisateur courant
        if access_level >= current_user.access_level and current_user.access_level < 4:
            flash("Vous ne pouvez pas créer un utilisateur avec un niveau d'accès supérieur ou égal au vôtre.", "error")
            return render_template('user_management/user_add.html', form_data=form_data, groups=groups, roles=roles)
        
        # Valider que le groupe est celui de l'utilisateur courant (pour les managers/admins)
        if current_user.access_level < 4 and group_id != current_user.group_id:
            flash("Vous ne pouvez pas ajouter un utilisateur à un autre groupe.", "error")
            return render_template('user_management/user_add.html', form_data=form_data, groups=groups, roles=roles)
        
        try:
            new_user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                password=request.form.get('password'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name')
            )
            db.session.add(new_user)
            db.session.flush()
            
            group_member = GroupMember(
                user_id=new_user.id,
                group_id=request.form.get('group_id', type=int),
                role_id=request.form.get('role_id', type=int)
            )
            db.session.add(group_member)
            db.session.commit()
            
            flash("Utilisateur créé avec succès.", "success")
            return redirect(url_for('user_management.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash("Un utilisateur avec ce nom d'utilisateur ou cet email existe déjà.", "error")
    
    return render_template('user_management/user_add.html', groups=groups, roles=roles)

@user_management_bp.route('/edit/<slug>', methods=['GET', 'POST'])
@login_required
@group_manager_required
def edit_user(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    
    # Vérifications de sécurité
    if current_user.access_level < 4 and user.group_id != current_user.group_id:
        abort(403)
    
    if current_user.access_level == 2 and user.access_level >= current_user.access_level:
        abort(403)
    
    groups = Group.query.all() if current_user.is_super_admin() else [gm.group for gm in current_user.groups if gm.is_admin]
    roles = Role.query.all()
    
    if request.method == 'POST':
        # Super admin peut tout modifier, sinon on limite
        if current_user.access_level >= 4:
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.group_id = request.form.get('group_id', type=int)
            user.access_level = request.form.get('access_level', type=int)
        else:
            # Autres utilisateurs ont des restrictions
            new_access_level = request.form.get('access_level', type=int)
            if new_access_level >= current_user.access_level:
                flash("Vous ne pouvez pas donner un niveau d'accès supérieur ou égal au vôtre.", "error")
                return render_template('user_management/user_edit.html', user=user, groups=groups, roles=roles)
            
            user.access_level = new_access_level
        
        # Champs communs à tous les niveaux
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        
        # Mise à jour du mot de passe si fourni
        password = request.form.get('password')
        if password and password.strip():
            user.password = password
        
        try:
            db.session.commit()
            flash("Utilisateur mis à jour avec succès.", "success")
            return redirect(url_for('user_management.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash("Un utilisateur avec ce nom d'utilisateur ou cet email existe déjà.", "error")
    
    return render_template('user_management/user_edit.html', user=user, groups=groups, roles=roles)

@user_management_bp.route('/delete/<slug>', methods=['POST'])
@login_required
@group_admin_required
def delete_user(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    
    # Vérifications de sécurité
    if current_user.access_level < 4 and user.group_id != current_user.group_id:
        abort(403)
    
    if current_user.access_level < 4 and user.access_level >= 4:
        abort(403)
    
    if user.id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "error")
        return redirect(url_for('user_management.list_users'))
    
    try:
        GroupMember.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash("Utilisateur supprimé avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    return redirect(url_for('user_management.list_users'))