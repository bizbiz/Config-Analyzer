# app/routes/parsed_files.py

from flask import Blueprint, render_template, jsonify, request
from app.models.configuration import ConfigurationInstance, ConfigSchema
from app.models.entities import Software, SoftwareVersion
from app.models.parameters import ParameterDefinition, ParameterValue
from app.extensions import db
from app.utils.custom_config_parser import CustomConfigParser
from sqlalchemy import select, func
from datetime import datetime
import uuid
import traceback
import logging

parsed_files_bp = Blueprint('parsed_files', __name__)

@parsed_files_bp.route('/edit_config/<int:config_id>')
def edit_parsed_content(config_id):
    """Affiche l'éditeur de configuration avec analyse des paramètres"""
    config = ConfigurationInstance.query.get_or_404(config_id)
    
    # Récupérer l'entité associée (Software ou SoftwareVersion)
    entity = config.linked_entities[0] if config.linked_entities else None
    
    # Récupérer les paramètres actifs pour cette configuration
    active_parameters = ParameterValue.query.filter_by(
        configuration_instance_id=config.id,
        is_active=True
    ).all()
    
    # Parser le contenu du fichier
    parser = CustomConfigParser()
    parsed_data = parser.parse(config.raw_content)

    table_data = []
    for key, value in parsed_data.items():
        param_def = ParameterDefinition.query.filter_by(name=key).first()
        if param_def:
            param_value = next((p for p in active_parameters if p.parameter_definition_id == param_def.id), None)
            if param_value:
                table_data.append({
                    'name': param_def.name,
                    'value': param_value.value,
                    'type': param_def.type,
                    'id': param_value.id,
                    'status': 'À jour'
                })
            else:
                table_data.append({
                    'name': param_def.name,
                    'value': value,
                    'type': param_def.type,
                    'status': 'Non configuré'
                })
        else:
            table_data.append({
                'name': key,
                'value': value,
                'type': 'unknown',
                'status': 'Nouveau'
            })

    return render_template(
        'edit/parsed_config_file.html',
        table_data=table_data,
        config=config,
        entity=entity,
        parameter_count=len(active_parameters)
    )

@parsed_files_bp.route('/create_parameter', methods=['POST'])
def create_parameter():
    """Crée un nouveau paramètre de configuration"""
    try:
        data = request.get_json()
        config_id = int(data['config_id'])
        
        new_def = ParameterDefinition(
            name=data['name'],
            type=data['type']
        )
        db.session.add(new_def)
        db.session.flush()
        
        new_value = ParameterValue(
            parameter_definition_id=new_def.id,
            configuration_instance_id=config_id,
            value=data['value'],
            is_active=True
        )
        db.session.add(new_value)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'new_param_id': new_value.id,
            'last_modified': new_value.created_at.strftime('%d/%m/%Y %H:%M')
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erreur lors de la création du paramètre: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@parsed_files_bp.route('/update_parameter/<int:param_id>', methods=['POST'])
def update_parameter(param_id):
    """Met à jour un paramètre existant"""
    try:
        param_value = ParameterValue.query.get_or_404(param_id)
        data = request.get_json()
        
        param_value.value = data['value']
        param_value.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'last_modified': param_value.updated_at.strftime('%d/%m/%Y %H:%M')
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erreur lors de la mise à jour du paramètre: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
