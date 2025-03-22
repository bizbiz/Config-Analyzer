# /app/routes/additional_params_config.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, session
from urllib.parse import urlparse
from app.models import AdditionalParametersConfig, AdditionalParameter, RobotModel, ParameterType, Client, Software, EntityType
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from flask_login import current_user
from sqlalchemy.dialects.postgresql import ARRAY

additional_params_config_bp = Blueprint('additional_params_config', __name__, url_prefix='/additional-params-config')

def get_redirect_url(entity_type=None, entity_slug=None):
    """Détermine l'URL de redirection selon le contexte"""
    # Cas superglobal
    if not entity_type:
        return url_for('home.index')
    
    # Cas global
    if not entity_slug:
        return url_for(f'{entity_type}s.list')
    
    # Cas ciblé
    return url_for(f'{entity_type}s.view', slug=entity_slug)

def get_entity_and_target(entity_type, entity_slug):
    entity = None
    target_entity = None
    applicable_ids = []

    if entity_type:
        if entity_type == 'robot_model':
            target_entity = EntityType.ROBOT_MODEL
            if entity_slug:
                entity = RobotModel.query.filter_by(slug=entity_slug).first()
        elif entity_type == 'client':
            target_entity = EntityType.CLIENT
            if entity_slug:
                entity = Client.query.filter_by(slug=entity_slug).first()
        elif entity_type == 'software':
            target_entity = EntityType.SOFTWARE
            if entity_slug:
                entity = Software.query.filter_by(slug=entity_slug).first()
        
        if entity:
            applicable_ids = [entity.id]

    return entity, target_entity, applicable_ids


def handle_config_form(config, form_data):
    """Gère le traitement commun du formulaire"""
    config.name = form_data.get('name')
    config.description = form_data.get('description')
    config.type = ParameterType(form_data.get('type'))
    
    if config.type == ParameterType.ENUM:
        _handle_enum_type(config, form_data)
    elif config.type == ParameterType.NUMERIC:
        _handle_numeric_type(config, form_data)
    else:
        _handle_text_type(config, form_data)

def save_config(config, is_new=False):
    """Sauvegarde commune pour add/edit"""
    try:
        if is_new:
            db.session.add(config)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur base de données : {str(e)}", "error")
        return False

def _handle_text_type(config, form_data):
    """Gère les paramètres texte avec regex"""
    value = form_data.get('value', '')
    regex = form_data.get('regex', '')
    
    # Structure: [valeur, regex]
    config.configuration_values = []
    if value:
        config.configuration_values.append(value)
        config.configuration_values.append(regex)
    
    # Validation optionnelle du regex
    if regex:
        try:
            re.compile(regex)
        except re.error as e:
            raise ValueError(f"Expression régulière invalide : {str(e)}")

def _handle_numeric_type(config, form_data):
    """Gère les paramètres numériques"""
    value = form_data.get('value', '')
    min_val = form_data.get('min_value', '')
    max_val = form_data.get('max_value', '')
    
    config.configuration_values = [value]
    if min_val.strip():
        config.configuration_values.append(min_val)
    if max_val.strip():
        config.configuration_values.append(max_val)

def _handle_enum_type(config, form_data):
    """Gère les énumérations"""
    multiple_choice = "1" if form_data.get('multiple_choice') else "0"
    enum_values = [v.strip() for v in form_data.getlist('enum_values[]') if v.strip()]
    config.configuration_values = [config.name, multiple_choice] + enum_values



@additional_params_config_bp.route('/list')
def list():
    """Liste toutes les configurations de paramètres avec pagination"""
    page = request.args.get('page', 1, type=int)
    items_per_page = 20
    search_query = request.args.get('q', '')
    
    # Requête de base
    query = AdditionalParametersConfig.query
    
    # Ajouter la recherche si un terme est fourni
    if search_query:
        query = query.filter(
            AdditionalParametersConfig.name.ilike(f'%{search_query}%')
        )
    
    # Compter le total d'éléments
    total_items = query.count()
    
    # Récupérer la page courante
    paginated = query.paginate(
        page=page, 
        per_page=items_per_page, 
        error_out=False
    )
    
    # Enrichir les données
    for config in paginated.items:
        try:
            if config.target_entity == EntityType.ROBOT_MODEL:
                entity = RobotModel.query.filter(RobotModel.id.in_(config.applicable_ids)).first()
                config.entity_name = entity.name if entity else "Modèle inconnu"
            else:
                config.entity_name = f"{config.target_entity.value} {'(Global)' if not config.applicable_ids else ''}"
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
    entity, target_entity, applicable_ids = get_entity_and_target(entity_type, entity_slug)
    return_url = get_redirect_url(entity_type, entity_slug)

    if request.method == 'POST':
        new_config = AdditionalParametersConfig(
            target_entity=target_entity,
            applicable_ids=applicable_ids,
            created_by_user_id=current_user.id if current_user.is_authenticated else None
        )
        
        handle_config_form(new_config, request.form)
        
        if save_config(new_config, is_new=True):
            return redirect(return_url)
        else:
            return redirect(request.url)

    return render_template('add/additional_params_config.html', 
                         entity_type=entity_type,
                         entity=entity,
                         return_url=return_url)

@additional_params_config_bp.route('/edit/<int:config_id>', methods=['GET', 'POST'])
def edit(config_id):
    config = AdditionalParametersConfig.query.get_or_404(config_id)
    entity_type = config.target_entity.name.lower() if config.target_entity else None
    entity_slug = None
    
    if config.applicable_ids:
        entity = (Client if config.target_entity == EntityType.CLIENT else 
                 Software if config.target_entity == EntityType.SOFTWARE else 
                 RobotModel).query.get(config.applicable_ids[0])
        entity_slug = entity.slug if entity else None
    
    return_url = get_redirect_url(entity_type, entity_slug)

    if request.method == 'POST':
        handle_config_form(config, request.form)
        
        if save_config(config):
            return redirect(return_url)
        else:
            return redirect(request.url)

    return render_template('edit/additional_params_config.html',
                         config=config,
                         entity_type=entity_type,
                         return_url=return_url)



@additional_params_config_bp.route('/delete/<int:config_id>', methods=['POST'])
def delete(config_id):
    """Supprime une configuration de paramètres par son ID"""

    config = AdditionalParametersConfig.query.get_or_404(config_id)
    
    entity_type = None
    entity_slug = None
    
    # Déterminer le type d'entité et le slug si applicable
    if config.applicable_ids:
        if config.target_entity == EntityType.ROBOT_MODEL:
            entity = RobotModel.query.get(config.applicable_ids[0])
            entity_type = 'robot_model'
        elif config.target_entity == EntityType.CLIENT:
            entity = Client.query.get(config.applicable_ids[0])
            entity_type = 'client'
        elif config.target_entity == EntityType.SOFTWARE:
            entity = Software.query.get(config.applicable_ids[0])
            entity_type = 'software'
        
        entity_slug = entity.slug if entity else None
    
    try:
        # Suppression des paramètres associés
        AdditionalParameter.query.filter_by(additional_parameters_config_id=config.id).delete()
        
        # Suppression de la configuration
        db.session.delete(config)
        db.session.commit()
        
        flash("Configuration et paramètres associés supprimés avec succès", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    # Redirection vers la page d'origine
    return_url = request.form.get('return_to', url_for('additional_params_config.list'))
    return redirect(return_url)      
