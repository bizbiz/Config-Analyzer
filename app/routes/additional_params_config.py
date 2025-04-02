# /app/routes/additional_params_config.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, session
from urllib.parse import urlparse
from app.models.entities import RobotModel, Client, Software
from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from flask_login import current_user

additional_params_config_bp = Blueprint('additional_params_config', __name__, url_prefix='/additional-params-config')

def get_redirect_url(entity_type=None, entity_slug=None):
    """Détermine l'URL de redirection selon le contexte"""
    if not entity_type:
        return url_for('home.home')
    if not entity_slug:
        return url_for(f'{entity_type}s.list')
    return url_for(f'{entity_type}s.view', slug=entity_slug)

def get_entity_and_target(entity_type, entity_slug):
    entity = None
    target_entity = None
    
    if entity_type:
        try:
            target_entity = EntityType[entity_type.upper()]
            if entity_slug:
                EntityClass = Entity.get_polymorphic_class(target_entity)
                entity = EntityClass.query.filter_by(slug=entity_slug).first()
        except KeyError:
            abort(404, f"Type d'entité inconnu: {entity_type}")
    
    return entity, target_entity

def handle_config_form(definition, form_data):
    """Gère le traitement commun du formulaire"""
    definition.name = form_data.get('name')
    definition.description = form_data.get('description')
    definition.type = ParameterType(form_data.get('type'))
    
    if definition.type == ParameterType.ENUM:
        _handle_enum_type(definition, form_data)
    elif definition.type == ParameterType.NUMERIC:
        _handle_numeric_type(definition, form_data)
    else:
        _handle_text_type(definition, form_data)

def save_config(definition, is_new=False):
    """Sauvegarde commune pour add/edit"""
    try:
        if is_new:
            db.session.add(definition)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur base de données : {str(e)}", "error")
        return False

def _handle_text_type(definition, form_data):
    """Gère les paramètres texte avec regex"""
    definition.default_value = form_data.get('value', '')
    definition.regex_pattern = form_data.get('regex', '')
    
    if definition.regex_pattern:
        try:
            re.compile(definition.regex_pattern)
        except re.error as e:
            raise ValueError(f"Expression régulière invalide : {str(e)}")

def _handle_numeric_type(definition, form_data):
    """Gère les paramètres numériques"""
    definition.default_value = form_data.get('value', '')
    definition.min_value = form_data.get('min_value', '')
    definition.max_value = form_data.get('max_value', '')

def _handle_enum_type(definition, form_data):
    """Gère les énumérations"""
    definition.allow_multiple = bool(form_data.get('multiple_choice'))
    definition.enum_values = [v.strip() for v in form_data.getlist('enum_values[]') if v.strip()]



@additional_params_config_bp.route('/list')
def list():
    page = request.args.get('page', 1, type=int)
    items_per_page = 20
    search_query = request.args.get('q', '')
    
    query = ParameterDefinition.query
    
    if search_query:
        query = query.filter(ParameterDefinition.name.ilike(f'%{search_query}%'))
    
    total_items = query.count()
    
    paginated = query.paginate(page=page, per_page=items_per_page, error_out=False)
    
    for config in paginated.items:
        try:
            if config.target_entity == EntityType.ROBOT_MODEL:
                entity = RobotModel.query.filter(RobotModel.id == config.entity_id).first()
                config.entity_name = entity.name if entity else "Modèle inconnu"
            else:
                config.entity_name = f"{config.target_entity.value} {'(Global)' if not config.entity_id else ''}"
        except Exception:
            config.entity_name = "Entité inconnue"
    
    return render_template(
        'list/additional_params_config.html', 
        items=paginated.items,
        total_items=total_items,
        total_pages=paginated.pages,
        page=page,
        items_per_page=items_per_page,
        offset=(page - 1) * items_per_page
    )


@additional_params_config_bp.route('/add/', methods=['GET', 'POST'])
@additional_params_config_bp.route('/add/<string:entity_type>/', methods=['GET', 'POST'])
@additional_params_config_bp.route('/add/<string:entity_type>/<string:entity_slug>', methods=['GET', 'POST'])
def add(entity_type=None, entity_slug=None):
    entity, target_entity, entity_id = get_entity_and_target(entity_type, entity_slug)
    return_url = get_redirect_url(entity_type, entity_slug)

    if request.method == 'POST':
        new_definition = ParameterDefinition(
            name=request.form.get('name'),
            description=request.form.get('description'),
            target_entity=target_entity,
            entity_id=entity_id,
            type=request.form.get('type'),
            created_by_user_id=current_user.id if current_user.is_authenticated else None
        )
        
        handle_config_form(new_definition, request.form)
        
        try:
            db.session.add(new_definition)
            db.session.commit()
            flash("Nouvelle définition de paramètre ajoutée avec succès", "success")
            return redirect(return_url)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout : {str(e)}", "error")
            return redirect(request.url)

    return render_template('add/additional_params_config.html', 
                           entity_type=entity_type,
                           entity=entity,
                           return_url=return_url)


@additional_params_config_bp.route('/edit/<int:config_id>', methods=['GET', 'POST'])
def edit(config_id):
    definition = ParameterDefinition.query.get_or_404(config_id)
    entity_type = definition.target_entity.name.lower() if definition.target_entity else None
    entity_slug = None
    
    if definition.entity_id:
        entity = Entity.get_polymorphic_class(definition.target_entity).query.get(definition.entity_id)
        entity_slug = entity.slug if entity else None
    
    return_url = get_redirect_url(entity_type, entity_slug)

    if request.method == 'POST':
        handle_config_form(definition, request.form)
        
        if save_config(definition):
            flash("Configuration updated successfully", "success")
            return redirect(return_url)
        else:
            flash("Error updating configuration", "error")
            return redirect(request.url)

    return render_template('edit/additional_params_config.html',
                           config=definition,
                           entity_type=entity_type,
                           return_url=return_url)




@additional_params_config_bp.route('/delete/<int:config_id>', methods=['POST'])
def delete(config_id):
    """Supprime une définition de paramètre par son ID"""

    definition = ParameterDefinition.query.get_or_404(config_id)
    
    entity_type = definition.target_entity.name.lower() if definition.target_entity else None
    entity_slug = None
    
    if definition.entity_id:
        entity = Entity.get_polymorphic_class(definition.target_entity).query.get(definition.entity_id)
        entity_slug = entity.slug if entity else None
    
    try:
        # Suppression des valeurs de paramètres associées
        ParameterValue.query.filter_by(parameter_definition_id=definition.id).delete()
        
        # Suppression de la définition de paramètre
        db.session.delete(definition)
        db.session.commit()
        
        flash("Définition de paramètre et valeurs associées supprimées avec succès", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    return_url = request.form.get('return_to', url_for('additional_params_config.list'))
    return redirect(return_url)
