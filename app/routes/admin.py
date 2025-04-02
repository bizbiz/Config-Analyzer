@auth_bp.route('/admin-dashboard')
@super_admin_required
def admin_dashboard():
    """Page accessible uniquement aux super administrateurs"""
    users = User.query.all()
    groups = UserGroup.query.all()
    return render_template('admin/dashboard.html', users=users, groups=groups)

@auth_bp.route('/group-manager')
@group_manager_required
def group_manager():
    """Page accessible aux gestionnaires de groupe et super admins"""
    group = current_user.group
    users = User.query.filter_by(group_id=group.id).all()
    return render_template('admin/group_manager.html', group=group, users=users)
