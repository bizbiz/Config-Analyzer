from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from app.models import AdditionalParametersConfig, AdditionalParameter, RobotModel, ParameterType, Client, Software, EntityType
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from flask_login import current_user
from sqlalchemy.dialects.postgresql import ARRAY

additional_params_config_bp = Blueprint('additional_params_config', __name__, url_prefix='/additional-params-config')

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

@additional_params_config_bp.route('/add/<string:entity_type>/', defaults={'entity_slug': None}, methods=['GET', 'POST'])
@additional_params_config_bp.route('/add/<string:entity_type>/<string:entity_slug>', methods=['GET', 'POST'])
def add(entity_type, entity_slug):
    """Ajoute une configuration de paramètres pour une entité ou un type d'entité"""
    target_entity = None
    entity_id = None
    
    referer_url = request.referrer
    
    if entity_type == 'robot_model':
        target_entity = EntityType.ROBOT_MODEL
    elif entity_type == 'client':
        target_entity = EntityType.CLIENT
    elif entity_type == 'software':
        target_entity = EntityType.SOFTWARE
    else:
        flash(f"Type d'entité non reconnu: {entity_type}", "error")
        return redirect(url_for('home.index'))
    
    if entity_slug:
        entity = None
        if target_entity == EntityType.ROBOT_MODEL:
            entity = RobotModel.query.filter_by(slug=entity_slug).first_or_404()
        elif target_entity == EntityType.CLIENT:
            entity = Client.query.filter_by(slug=entity_slug).first_or_404()
        elif target_entity == EntityType.SOFTWARE:
            entity = Software.query.filter_by(slug=entity_slug).first_or_404()
        
        entity_id = entity.id if entity else None
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        param_type = request.form.get('type')
        
        form_referer = request.form.get('referer_url')
        if form_referer:
            referer_url = form_referer
        
        if not name or not param_type:
            flash("Le nom et le type sont obligatoires", "error")
            return redirect(request.url)
        
        try:
            enum_type = ParameterType(param_type)
            configuration_values = []
            
            if enum_type == ParameterType.ENUM:
                multiple_choice = "1" if request.form.get('multiple_choice') else "0"
                enum_values = [v for v in request.form.getlist('enum_values[]') if v.strip()]
                configuration_values = [name, multiple_choice] + enum_values
            elif enum_type == ParameterType.NUMERIC:
                value = request.form.get('value')
                min_value = request.form.get('min_value')
                max_value = request.form.get('max_value')
                
                configuration_values = [value] if value else ['']
                if min_value:
                    configuration_values.append(min_value)
                elif max_value:
                    configuration_values.append('')
                if max_value:
                    if len(configuration_values) < 2:
                        configuration_values.append('')
                    configuration_values.append(max_value)
            else:
                value = request.form.get('value')
                if value:
                    configuration_values = [value]
            
            new_config = AdditionalParametersConfig(
                target_entity=target_entity,
                applicable_ids=[entity_id] if entity_id else [],
                type=enum_type,
                name=name,
                configuration_values=configuration_values,
                created_by_user_id=current_user.id if current_user.is_authenticated else None
            )

            new_config.description = description
            
            db.session.add(new_config)
            db.session.commit()
            
            flash(f"Configuration de paramètre '{name}' ajoutée avec succès", "success")
            
            if referer_url and referer_url != request.url:
                return redirect(referer_url)
            elif entity_slug:
                return redirect(url_for(f"{entity_type}s.view", slug=entity_slug))
            else:
                return redirect(url_for(f"{entity_type}s.list"))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de la configuration : {str(e)}", "error")
    
    return render_template(
        'add/additional_params_config.html',
        entity_type=entity_type,
        entity_slug=entity_slug,
        referer_url=referer_url
    )


@additional_params_config_bp.route('/edit/<string:entity_type>/<string:entity_slug>/<int:config_id>', methods=['GET', 'POST'])
def edit(entity_type, entity_slug, config_id):
    """Édite une configuration de paramètres existante"""

    # Correction : Définir target_entity avant utilisation
    try:
        target_entity = EntityType(entity_type)
    except ValueError:
        abort(404)

    # Gestion des configurations globales
    is_global = (entity_slug == 'global')

    entity = None
    if not is_global:
        # Récupération de l'entité seulement si ce n'est pas une config globale
        if target_entity == EntityType.ROBOT_MODEL:
            entity = RobotModel.query.filter_by(slug=entity_slug).first_or_404()
        elif target_entity == EntityType.CLIENT:
            entity = Client.query.filter_by(slug=entity_slug).first_or_404()
        elif target_entity == EntityType.SOFTWARE:
            entity = Software.query.filter_by(slug=entity_slug).first_or_404()

    config = AdditionalParametersConfig.query.get_or_404(config_id)
    
    # Vérification de la cohérence de la configuration
    if not is_global:
        if config.target_entity != target_entity:
            abort(404)
        if entity.id not in config.applicable_ids:
            abort(404)
    else:
        if config.target_entity is not None or config.applicable_ids:
            abort(404)

    # Récupération des valeurs min/max existantes
    known_min, known_max = config.get_known_min_max()
    
    if request.method == 'POST':
        # Validation des données
        new_name = request.form.get('name')
        if not new_name:
            flash("Le nom du paramètre est obligatoire", "error")
            return redirect(request.url)
            
        try:
            new_type = ParameterType(request.form.get('type'))
        except ValueError:
            flash("Type de paramètre invalide", "error")
            return redirect(request.url)

        # Mise à jour des valeurs
        config.name = new_name
        config.description = request.form.get('description')
        config.type = new_type
        config.updated_by_user_id = current_user.id if current_user.is_authenticated else None

        # Gestion des valeurs selon le type
        if new_type == ParameterType.ENUM:
            multiple_choice = "1" if request.form.get('multiple_choice') else "0"
            enum_values = [v.strip() for v in request.form.getlist('enum_values[]') if v.strip()]
            if not enum_values:
                flash("Au moins une valeur d'énumération est requise", "error")
                return redirect(request.url)
            config.configuration_values = [new_name, multiple_choice] + enum_values
            
        elif new_type == ParameterType.NUMERIC:
            value = request.form.get('value', '')
            min_val = request.form.get('min_value', '')
            max_val = request.form.get('max_value', '')
            
            # Validation des valeurs numériques
            try:
                if value: float(value)
                if min_val: float(min_val)
                if max_val: float(max_val)
            except ValueError:
                flash("Valeur numérique invalide", "error")
                return redirect(request.url)
            
            config.configuration_values = [value]
            if min_val:
                config.configuration_values.append(min_val)
            if max_val:
                config.configuration_values.extend([''] * (2 - len(config.configuration_values)))
                config.configuration_values.append(max_val)
                
        else:  # Texte
            value = request.form.get('value', '')
            config.configuration_values = [value] if value else []

        # Sauvegarde
        try:
            db.session.commit()
            flash("Configuration mise à jour avec succès", "success")
            if is_global:
                return redirect(url_for('additional_params_config.list'))
            return redirect(url_for(f'{entity_type}s.view', slug=entity.slug))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour : {str(e)}", "error")

    return render_template(
        'edit/additional_params_config.html',
        entity=entity,
        entity_type=entity_type,
        config=config,
        is_global=is_global,
        known_min=known_min,
        known_max=known_max
    )



@additional_params_config_bp.route('/delete/<string:entity_type>/<string:entity_slug>/<int:config_id>', methods=['POST'])
def delete(entity_type, entity_slug, config_id):
    """Supprime une configuration de paramètres"""
    # Déterminer le type d'entité
    target_entity = None
    entity = None
    
    if entity_type == 'robot_model':
        target_entity = EntityType.ROBOT_MODEL
        entity = RobotModel.query.filter_by(slug=entity_slug).first_or_404()
    elif entity_type == 'client':
        target_entity = EntityType.CLIENT
        entity = Client.query.filter_by(slug=entity_slug).first_or_404()
    elif entity_type == 'software':
        target_entity = EntityType.SOFTWARE
        entity = Software.query.filter_by(slug=entity_slug).first_or_404()
    else:
        abort(404)
    
    config = AdditionalParametersConfig.query.get_or_404(config_id)
    
    # Vérifier que la configuration appartient bien à cette entité
    if (config.target_entity != target_entity) or (entity.id not in config.applicable_ids and config.applicable_ids):
        abort(404)
    
    try:
        # Supprimer d'abord tous les paramètres associés
        AdditionalParameter.query.filter_by(additional_parameters_config_id=config.id).delete()
        
        # Puis supprimer la configuration
        db.session.delete(config)
        db.session.commit()
        
        flash("Configuration et paramètres associés supprimés avec succès", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    return redirect(url_for(f'{entity_type}s.view', slug=entity.slug))
