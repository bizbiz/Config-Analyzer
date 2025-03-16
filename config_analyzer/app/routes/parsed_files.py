from flask import Blueprint, render_template, jsonify, request
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software, ClientConfigurationFile, BaseConfigFileParameter
from app.extensions import db
from app.utils.custom_config_parser import CustomConfigParser
from sqlalchemy import select, func
from datetime import datetime
import uuid
import traceback
import logging

parsed_files_bp = Blueprint('parsed_files', __name__)

@parsed_files_bp.route('/edit_base_config_file/<software_name>/<software_version>/<file_name>')
def edit_base_parsed_content(software_name, software_version, file_name):
    """Affiche l'éditeur de configuration avec analyse des paramètres"""
    base_config = SoftwareBaseConfigurationFile.query \
        .join(SoftwareVersion) \
        .join(Software) \
        .filter(
            Software.name == software_name,
            SoftwareVersion.version == software_version,
            SoftwareBaseConfigurationFile.file_name == file_name
        ) \
        .first_or_404()

    client_count = db.session.execute(
        select(func.count(ClientConfigurationFile.id))
        .where(ClientConfigurationFile.software_base_configuration_id == base_config.id)
    ).scalar()

    # Récupérer les paramètres actifs (in_use=True) pour ce fichier de configuration
    active_parameters = BaseConfigFileParameter.query.filter_by(
        base_config_file_id=base_config.id,
        in_use=True
    ).all()
    
    # Créer un dictionnaire des paramètres actifs par nom
    active_params_dict = {param.name: param for param in active_parameters}
    
    # Parser le contenu du fichier
    parser = CustomConfigParser()
    parsed_data = parser.parse(base_config.content)

    table_data = []
    for key, value in parsed_data.items():
        if key in active_params_dict:
            # Paramètre existant et actif
            param = active_params_dict[key]
            table_data.append({
                'name': param.name,
                'value': param.value,
                'type': param.type,
                'min_value': param.min_value,
                'default_value': param.value,
                'max_value': param.max_value,
                'numeric_rule': param.numeric_rule,
                'regex_rule': param.regex_rule,
                'notes': param.notes,
                'id': param.id,
                'parameter_group_id': param.parameter_group_id,
                'version': param.version,
                'status': 'À jour'
            })
        else:
            # Nouveau paramètre
            table_data.append({
                'name': key,
                'value': value,
                'type': 'float' if isinstance(value, (int, float)) else 'text',
                'min_value': None,
                'default_value': value,
                'max_value': None,
                'numeric_rule': None,
                'regex_rule': None,
                'notes': None,
                'parameter_group_id': None,
                'version': 1,
                'status': 'Inconnu'
            })

    return render_template(
        'edit/parsed_base_config_file.html',
        table_data=table_data,
        base_config=base_config,
        client_count=client_count,
        parameter_count=len(active_parameters)
    )


@parsed_files_bp.route('/get_initial_value/<int:param_id>')
def get_initial_value(param_id):
    """Récupère les valeurs initiales d'un paramètre pour la réinitialisation"""
    param = BaseConfigFileParameter.query.get_or_404(param_id)
    return jsonify({
        'value': param.value,
        'min': param.min_value,
        'max': param.max_value,
        'numeric_rule': param.numeric_rule,
        'regex': param.regex_rule,
        'type': param.type,
        'notes': param.notes
    })

@parsed_files_bp.route('/create_parameter', methods=['POST'])
def create_parameter():
    """Crée un nouveau paramètre de configuration"""
    try:
        # Vérifier si les données sont bien au format JSON
        if not request.is_json:
            logging.error("Les données ne sont pas au format JSON")
            return jsonify({'status': 'error', 'message': 'Les données doivent être au format JSON'}), 400
            
        data = request.get_json()
        logging.info(f"Données reçues: {data}")
        
        # Vérifier les champs requis
        required_fields = ['base_config_file_id', 'name', 'value', 'type']
        for field in required_fields:
            if field not in data:
                logging.error(f"Champ manquant: {field}")
                return jsonify({'status': 'error', 'message': f'Champ manquant: {field}'}), 400

        try:
            base_config_file_id = int(data['base_config_file_id'])
        except ValueError as e:
            logging.error(f"base_config_file_id invalide: {data['base_config_file_id']}")
            return jsonify({'status': 'error', 'message': f'base_config_file_id invalide: {str(e)}'}), 400

        # Générer un identifiant de groupe unique pour ce nouveau paramètre
        parameter_group_id = f"{base_config_file_id}_{data['name']}_{uuid.uuid4().hex[:8]}"
        
        # Afficher les valeurs avant création
        logging.info(f"Création d'un paramètre avec: base_config_file_id={base_config_file_id}, name={data['name']}")
        
        # Créer le nouveau paramètre avec des valeurs par défaut pour les champs non requis
        new_param = BaseConfigFileParameter(
            base_config_file_id=base_config_file_id,
            name=data['name'],
            value=data['value'],
            min_value=float(data['min_value']) if data.get('min_value') else None,
            max_value=float(data['max_value']) if data.get('max_value') else None,
            numeric_rule=data.get('numeric_rule'),
            regex_rule=data.get('regex_rule'),
            type=data['type'],
            notes=data.get('notes'),
            parameter_group_id=parameter_group_id,
            version=1,
            in_use=True,
            view_access_level=0,  # Valeur par défaut
            edit_access_level=0,  # Valeur par défaut
            created_by_user_id=None  # Valeur par défaut (à remplacer par current_user.id quand l'authentification sera implémentée)
        )
        
        db.session.add(new_param)
        db.session.commit()
        logging.info(f"Paramètre créé avec succès, ID: {new_param.id}")

        parameter_count = BaseConfigFileParameter.query.filter_by(
            base_config_file_id=base_config_file_id, 
            in_use=True
        ).count()

        return jsonify({
            'status': 'success',
            'new_param_id': new_param.id,
            'parameter_group_id': parameter_group_id,
            'version': 1,
            'last_modified': new_param.created_at.strftime('%d/%m/%Y %H:%M'),
            'parameter_count': parameter_count
        })
    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        logging.error(f"Erreur lors de la création du paramètre: {str(e)}\n{error_details}")
        return jsonify({'status': 'error', 'message': str(e), 'details': error_details}), 400

@parsed_files_bp.route('/update_parameter_complete/<int:param_id>', methods=['POST'])
def update_parameter_complete(param_id):
    """Crée une nouvelle version d'un paramètre plutôt que de le mettre à jour"""
    try:
        # Récupérer le paramètre existant
        old_param = BaseConfigFileParameter.query.get_or_404(param_id)
        data = request.get_json()
        
        # Vérifier si les données ont réellement changé
        has_changes = False
        for field in ['value', 'min_value', 'max_value', 'numeric_rule', 'regex_rule', 'type', 'notes']:
            if field in data and getattr(old_param, field) != data.get(field):
                has_changes = True
                break
                
        if not has_changes:
            # Aucun changement, retourner simplement un succès
            return jsonify({
                'status': 'success',
                'message': 'Aucun changement détecté',
                'last_modified': old_param.created_at.strftime('%d/%m/%Y %H:%M'),
                'parameter_count': BaseConfigFileParameter.query.filter_by(
                    base_config_file_id=old_param.base_config_file_id, 
                    in_use=True
                ).count()
            })
        
        # Créer un parameter_group_id s'il n'existe pas encore
        parameter_group_id = old_param.parameter_group_id or f"{old_param.base_config_file_id}_{old_param.name}_{uuid.uuid4().hex[:8]}"
        
        # Désactiver l'ancien paramètre
        old_param.in_use = False
        
        # Créer un nouveau paramètre avec les nouvelles valeurs
        new_param = BaseConfigFileParameter(
            base_config_file_id=old_param.base_config_file_id,
            name=old_param.name,
            value=data.get('value', old_param.value),
            min_value=float(data.get('min_value')) if data.get('min_value') else None,
            max_value=float(data.get('max_value')) if data.get('max_value') else None,
            numeric_rule=data.get('numeric_rule', old_param.numeric_rule),
            regex_rule=data.get('regex_rule', old_param.regex_rule),
            type=data.get('type', old_param.type),
            notes=data.get('notes', old_param.notes),
            parameter_group_id=parameter_group_id,
            version=old_param.version + 1,
            in_use=True,
            view_access_level=old_param.view_access_level,
            edit_access_level=old_param.edit_access_level,
            created_by_user_id=None  # À remplacer par current_user.id quand l'authentification sera implémentée
        )
        
        db.session.add(new_param)
        db.session.commit()
        
        # Récupérer les informations pour la réponse
        parameter_count = BaseConfigFileParameter.query.filter_by(
            base_config_file_id=old_param.base_config_file_id, 
            in_use=True
        ).count()
        
        return jsonify({
            'status': 'success',
            'new_param_id': new_param.id,
            'parameter_group_id': parameter_group_id,
            'version': new_param.version,
            'last_modified': new_param.created_at.strftime('%d/%m/%Y %H:%M'),
            'parameter_count': parameter_count
        })
        
    except Exception as e:
        db.session.rollback()
        error_details = traceback.format_exc()
        logging.error(f"Erreur lors de la mise à jour du paramètre: {str(e)}\n{error_details}")
        return jsonify({'status': 'error', 'message': str(e), 'details': error_details}), 400


def get_last_modified(base_config_file_id):
    """Récupère la date de dernière modification pour un fichier de configuration"""
    last_modified = db.session.query(func.max(func.coalesce(BaseConfigFileParameter.created_at, BaseConfigFileParameter.created_at))).filter_by(base_config_file_id=base_config_file_id).scalar()
    base_config = SoftwareBaseConfigurationFile.query.get(base_config_file_id)
    base_date = base_config.updated_at or base_config.created_at
    return max(filter(None, [last_modified, base_date]))

@parsed_files_bp.route('/parameter_history/<parameter_group_id>')
def parameter_history(parameter_group_id):
    """Affiche l'historique des versions d'un paramètre"""
    parameters = BaseConfigFileParameter.query.filter_by(
        parameter_group_id=parameter_group_id
    ).order_by(BaseConfigFileParameter.version.desc()).all()
    
    if not parameters:
        abort(404)
    
    # Récupérer les informations du fichier de configuration
    base_config = parameters[0].base_config_file
    
    return render_template(
        'view/parameter_history.html',
        parameters=parameters,
        base_config=base_config
    )
