from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

def access_level_required(level):
    """Décorateur pour vérifier le niveau d'accès minimal requis"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.access_level < level:
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def group_manager_required(f):
    """Décorateur pour vérifier si l'utilisateur est gestionnaire de groupe"""
    return access_level_required(2)(f)

def super_admin_required(f):
    """Décorateur pour vérifier si l'utilisateur est super admin"""
    return access_level_required(3)(f)

# Ajoutez cette fonction qui semble être requise par group_management.py
def group_admin_required(f):
    """Décorateur pour vérifier si l'utilisateur est admin de groupe"""
    return access_level_required(2)(f)  # Niveau d'accès à ajuster selon vos besoins
