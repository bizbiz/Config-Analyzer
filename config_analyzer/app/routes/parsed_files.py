from flask import Blueprint, render_template, jsonify
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software, ClientConfigurationFile, BaseConfigFileParameter
from app.extensions import db
from app.utils.custom_config_parser import CustomConfigParser
from sqlalchemy import select, func
from datetime import datetime

parsed_files_bp = Blueprint('parsed_files', __name__)

@parsed_files_bp.route('/<software_name>/<software_version>/<file_name>')
def edit_base_parsed_content(software_name, software_version, file_name):
    # Récupération de la configuration de base
    base_config = SoftwareBaseConfigurationFile.query \
        .join(SoftwareVersion) \
        .join(Software) \
        .filter(
            Software.name == software_name,
            SoftwareVersion.version == software_version,
            SoftwareBaseConfigurationFile.file_name == file_name
        ) \
        .first_or_404()

    # Comptage direct des clients associés
    client_count = db.session.execute(
        select(func.count(ClientConfigurationFile.id))
        .where(ClientConfigurationFile.software_base_configuration_id == base_config.id)
    ).scalar()

    # Comptage direct des paramètres
    parameter_count = db.session.execute(
        select(func.count(BaseConfigFileParameter.id))
        .where(BaseConfigFileParameter.base_config_file_id == base_config.id)
    ).scalar()

    # Création de l'instance pour parser le contenu
    parser = CustomConfigParser()
    parsed_data = parser.parse(base_config.content)

    # Préparer les données pour le tableau
    table_data = []
    for key, value in parsed_data.items():
        # Vérifier si un paramètre existe dans la DB pour cette clé
        param = BaseConfigFileParameter.query.filter_by(
            base_config_file_id=base_config.id,
            name=key
        ).first()

        if param:
            # Si le paramètre existe dans la DB, utiliser ses valeurs
            table_data.append({
                'name': param.name,
                'value': param.value,
                'type': 'integer' if param.is_numeric_values else 'text',
                'min_value': param.min_value,
                'default_value': param.value,
                'max_value': param.max_value,
                'numeric_rule': param.numeric_rule,
                'regex_rule': param.regex_rule,
                'status': 'À jour'
            })
        else:
            # Si le paramètre n'existe pas dans la DB, utiliser les valeurs par défaut du parsing
            table_data.append({
                'name': key,
                'value': value,
                'type': 'integer' if isinstance(value, int) else ('float' if isinstance(value, float) else 'text'),
                'min_value': None,
                'default_value': value,
                'max_value': None,
                'numeric_rule': None,
                'regex_rule': None,
                'status': 'Inconnu'
            })

    return render_template(
        'view/parsed_base_config_file.html',
        table_data=table_data,
        base_config=base_config,
        client_count=client_count,
        parameter_count=parameter_count
    )

    
@parsed_files_bp.route('/update_parameter/<int:param_id>', methods=['POST'])
def update_parameter(param_id):
    try:
        param = BaseConfigFileParameter.query.get_or_404(param_id)
        data = request.get_json()
        
        # Validation des données
        if not all(key in data for key in ['value', 'min', 'max', 'numeric_rule', 'regex']):
            raise ValueError("Données manquantes")
        
        # Mise à jour des champs
        param.value = data['value']
        param.min_value = float(data['min']) if data['min'] else None
        param.max_value = float(data['max']) if data['max'] else None
        param.numeric_rule = data['numeric_rule']
        param.regex_rule = data['regex']
        param.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'last_modified': max(
                param.base_config_file.last_modified,
                param.updated_at
            ).strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400


@parsed_files_bp.route('/get_initial_value/<int:param_id>')
def get_initial_value(param_id):
    param = BaseConfigFileParameter.query.get_or_404(param_id)
    return jsonify({
        'value': param.value,
        'min': param.min_value,
        'max': param.max_value,
        'numeric_rule': param.numeric_rule,
        'regex': param.regex_rule
    })

@parsed_files_bp.route('/create_parameter', methods=['POST'])
def create_parameter():
    try:
        data = request.get_json()
        new_param = BaseConfigFileParameter(
            base_config_file_id=data['base_config_file_id'],
            name=data['name'],  # À extraire du template
            value=data['value'],
            min_value=float(data['min_value']) if data['min_value'] else None,
            max_value=float(data['max_value']) if data['max_value'] else None,
            numeric_rule=data['numeric_rule'],
            regex_rule=data['regex_rule'],
            is_numeric_values=data['type'] in ['integer', 'float'],
            is_text_value=data['type'] == 'text'
        )
        db.session.add(new_param)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'new_param_id': new_param.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
