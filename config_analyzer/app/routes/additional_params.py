from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from app.models import (AdditionalParametersConfig, AdditionalParameter, Client, RobotClient, RobotModel, Software, SoftwareVersion)
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
import uuid

additional_params_bp = Blueprint('additional_params', __name__)

# Fonction utilitaire améliorée pour récupérer l'entité associée et le nom de la table
def get_entity_by_table_name(table_name, table_id=None, entity_name=None):
    # Normaliser le nom de la table (enlever le 's' final si présent)
    normalized_table_name = table_name.rstrip('s')
    
    # Dictionnaire de correspondance entre le nom normalisé et le nom réel de la table
    table_mappings = {
        'client': 'clients',
        'robot_client': 'robot_clients',
        'robot_model': 'robot_models',
        'software': 'software',
        'software_version': 'software_versions'
    }
    
    # Vérifier si le nom normalisé existe dans notre dictionnaire
    if normalized_table_name not in table_mappings:
        abort(404, f"Type d'entité inconnu: {table_name}")
    
    # Récupérer le vrai nom de la table
    actual_table_name = table_mappings[normalized_table_name]
    
    # Récupérer l'entité selon le type
    entity = None
    if normalized_table_name == 'client':
        if entity_name:
            entity = Client.query.filter_by(name=entity_name).first_or_404()
        else:
            entity = Client.query.get_or_404(table_id)
    elif normalized_table_name == 'robot_client':
        if entity_name:
            entity = RobotClient.query.filter_by(serial_number=entity_name).first_or_404()
        else:
            entity = RobotClient.query.get_or_404(table_id)
    elif normalized_table_name == 'robot_model':
        if entity_name:
            entity = RobotModel.query.filter_by(name=entity_name).first_or_404()
        else:
            entity = RobotModel.query.get_or_404(table_id)
    elif normalized_table_name == 'software':
        if entity_name:
            entity = Software.query.filter_by(name=entity_name).first_or_404()
        else:
            entity = Software.query.get_or_404(table_id)
    elif normalized_table_name == 'software_version':
        if entity_name:
            entity = SoftwareVersion.query.filter_by(version=entity_name).first_or_404()
        else:
            entity = SoftwareVersion.query.get_or_404(table_id)
    
    # Retourner à la fois l'entité et le nom réel de la table
    return entity, actual_table_name

# Fonction utilitaire pour obtenir le nom d'affichage de l'entité
def get_entity_display_name(entity, table_name):
    if table_name == 'clients':
        return entity.name
    elif table_name == 'robot_clients':
        return f"Robot {entity.serial_number} - {entity.client.name}"
    elif table_name == 'robot_models':
        return entity.name
    elif table_name == 'software':
        return entity.name
    elif table_name == 'software_versions':
        return f"{entity.software.name} v{entity.version}"
    else:
        return f"Entité #{entity.id}"

# ======== ROUTES D'AFFICHAGE ========

@additional_params_bp.route('/additional_params/view/<table_name>/<int:table_id>')
def view_additional_params(table_name, table_id):
    """Affiche les paramètres additionnels d'une entité"""
    entity, actual_table_name = get_entity_by_table_name(table_name, table_id=table_id)
    entity_name = get_entity_display_name(entity, actual_table_name)
    
    # Récupérer la configuration des paramètres additionnels
    config = AdditionalParametersConfig.query.filter_by(
        table_name=actual_table_name,
        table_id=table_id
    ).first()
    
    additional_params = []
    
    if config:
        additional_params = AdditionalParameter.query.filter_by(
            additional_parameters_config_id=config.id
        ).all()
    
    return render_template(
        'view/additional_params.html',
        entity=entity,
        entity_name=entity_name,
        table_name=actual_table_name,
        table_id=table_id,
        additional_params=additional_params,
        config=config
    )

@additional_params_bp.route('/additional_params/list')
def list_additional_params():
    """Liste toutes les configurations de paramètres additionnels"""
    configs = AdditionalParametersConfig.query.all()
    
    # Enrichir les configurations avec des informations supplémentaires
    for config in configs:
        config.param_count = AdditionalParameter.query.filter_by(
            additional_parameters_config_id=config.id
        ).count()
        
        try:
            entity, actual_table_name = get_entity_by_table_name(config.table_name, table_id=config.table_id)
            config.entity_name = get_entity_display_name(entity, actual_table_name)
        except:
            config.entity_name = f"Entité inconnue ({config.table_name} #{config.table_id})"
    
    return render_template(
        'list/additional_params.html',
        configs=configs
    )

# ======== ROUTES D'ÉDITION ========

@additional_params_bp.route('/additional_params/edit/<table_name>/<int:table_id>', methods=['GET', 'POST'])
def edit_additional_params(table_name, table_id):
    """Édite les paramètres additionnels d'une entité"""
    entity, actual_table_name = get_entity_by_table_name(table_name, table_id=table_id)
    entity_name = get_entity_display_name(entity, actual_table_name)
    
    # Récupérer ou créer la configuration
    config = AdditionalParametersConfig.query.filter_by(
        table_name=actual_table_name,
        table_id=table_id
    ).first()
    
    if not config and request.method == 'GET':
        # Rediriger vers la page d'ajout si la configuration n'existe pas
        return redirect(url_for('additional_params.add_additional_params', table_name=table_name, table_id=table_id))
    
    additional_params = []
    if config:
        additional_params = AdditionalParameter.query.filter_by(
            additional_parameters_config_id=config.id
        ).all()
    
    if request.method == 'POST':
        try:
            # Si la configuration n'existe pas encore, la créer
            if not config:
                config = AdditionalParametersConfig(
                    table_name=actual_table_name,
                    table_id=table_id,
                    type='text'  # Type par défaut
                )
                db.session.add(config)
                db.session.flush()
            
            # Récupérer les paramètres existants
            existing_params = {
                p.id: p for p in AdditionalParameter.query.filter_by(
                    additional_parameters_config_id=config.id
                ).all()
            }
            
            # Traiter les paramètres soumis
            param_ids = request.form.getlist('param_id')
            param_names = request.form.getlist('param_name')
            param_values = request.form.getlist('param_value')
            
            processed_ids = set()
            
            for i in range(len(param_names)):
                if not param_names[i].strip():
                    continue
                
                param_id = param_ids[i] if i < len(param_ids) else None
                
                if param_id and param_id.isdigit() and int(param_id) in existing_params:
                    # Mettre à jour un paramètre existant
                    param = existing_params[int(param_id)]
                    param.name = param_names[i]
                    param.value = param_values[i] if i < len(param_values) else ""
                    processed_ids.add(int(param_id))
                else:
                    # Créer un nouveau paramètre
                    new_param = AdditionalParameter(
                        additional_parameters_config_id=config.id,
                        name=param_names[i],
                        value=param_values[i] if i < len(param_values) else ""
                    )
                    db.session.add(new_param)
            
            # Supprimer les paramètres qui n'ont pas été soumis
            for param_id, param in existing_params.items():
                if param_id not in processed_ids:
                    db.session.delete(param)
            
            db.session.commit()
            flash('Paramètres additionnels mis à jour avec succès', 'success')
            return redirect(url_for('additional_params.view_additional_params', table_name=table_name, table_id=table_id))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour des paramètres : {str(e)}', 'danger')
    
    return render_template(
        'edit/additional_params.html',
        entity=entity,
        entity_name=entity_name,
        table_name=actual_table_name,
        table_id=table_id,
        additional_params=additional_params,
        config=config
    )

@additional_params_bp.route('/<string:model_type>/<string:entity_name>/additionalparameters/add', methods=['GET', 'POST'])
def add_additional_param(model_type, entity_name):
    """Ajoute des paramètres additionnels à une entité"""
    # Récupérer l'entité et le nom de la table en utilisant la fonction améliorée
    entity, table_name = get_entity_by_table_name(model_type, entity_name=entity_name)
    table_id = entity.id
    
    if request.method == 'POST':
        name = request.form.get('name')
        param_type = request.form.get('type')
        
        if not name or not param_type:
            flash("Le nom et le type du paramètre sont obligatoires.", "error")
            return redirect(url_for('additional_params.add_additional_param', model_type=model_type, entity_name=entity_name))
        
        try:
            # Vérifier si une configuration existe déjà
            config = AdditionalParametersConfig.query.filter_by(
                table_name=table_name,
                table_id=table_id
            ).first()
            
            # Si aucune configuration n'existe, en créer une nouvelle
            if not config:
                config = AdditionalParametersConfig(
                    table_name=table_name,
                    table_id=table_id,
                    type=param_type
                )
                db.session.add(config)
                db.session.flush()
            
            # Créer le nouveau paramètre
            if param_type == 'enum':
                # Pour les énumérations, combiner toutes les valeurs en une chaîne séparée par des virgules
                enum_values = request.form.getlist('enum_values[]')
                value = ','.join(filter(None, enum_values))  # Filtrer les valeurs vides
            else:
                value = request.form.get('value', '')
            
            new_param = AdditionalParameter(
                additional_parameters_config_id=config.id,
                name=name,
                value=value
            )
            db.session.add(new_param)
            db.session.commit()
            
            flash(f"Paramètre '{name}' ajouté avec succès !", "success")
            
            # Rediriger vers la page de détail de l'entité
            normalized_model_type = model_type.rstrip('s')
            if normalized_model_type == 'software':
                return redirect(url_for('softwares.view_software_by_name', software_name=entity_name))
            elif normalized_model_type == 'client':
                return redirect(url_for('clients.view_client', client_name=entity_name))
            elif normalized_model_type == 'robot_model':
                return redirect(url_for('robot_models.view_robot_model', robot_model_name=entity_name))
            elif normalized_model_type == 'robot_client':
                return redirect(url_for('robot_clients.view_robot_client', serial_number=entity_name))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout du paramètre : {str(e)}", "error")
    
    # Pour la méthode GET, afficher le formulaire
    return render_template(
        'add/additional_params.html',
        model_type=model_type.rstrip('s'),  # Enlever le 's' pour l'affichage
        entity_name=entity_name,
        entity=entity
    )

# Fonction pour intégrer les paramètres additionnels dans d'autres vues
def get_additional_params_data(table_name, table_id):
    """Récupère les données des paramètres additionnels pour intégration dans d'autres vues"""
    # Normaliser le nom de la table (enlever le 's' final si présent)
    normalized_table_name = table_name.rstrip('s')
    
    # Dictionnaire de correspondance entre le nom normalisé et le nom réel de la table
    table_mappings = {
        'client': 'clients',
        'robot_client': 'robot_clients',
        'robot_model': 'robot_models',
        'software': 'software',
        'software_version': 'software_versions'
    }
    
    # Utiliser le nom de table normalisé pour la recherche si disponible
    actual_table_name = table_mappings.get(normalized_table_name, table_name)
    
    config = AdditionalParametersConfig.query.filter_by(
        table_name=actual_table_name,
        table_id=table_id
    ).first()
    
    if not config:
        return {
            'additional_params': [],
            'has_config': False
        }
    
    additional_params = AdditionalParameter.query.filter_by(
        additional_parameters_config_id=config.id
    ).all()
    
    return {
        'additional_params': additional_params,
        'has_config': True,
        'config': config
    }
