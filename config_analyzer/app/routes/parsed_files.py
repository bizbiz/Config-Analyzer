from flask import Blueprint, render_template, jsonify, request
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software, ClientConfigurationFile, BaseConfigFileParameter
from app.extensions import db
from app.utils.custom_config_parser import CustomConfigParser
from sqlalchemy import select, func
from datetime import datetime

parsed_files_bp = Blueprint('parsed_files', __name__)

@parsed_files_bp.route('/<software_name>/<software_version>/<file_name>')
def edit_base_parsed_content(software_name, software_version, file_name):
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

    parameter_count = db.session.execute(
        select(func.count(BaseConfigFileParameter.id))
        .where(BaseConfigFileParameter.base_config_file_id == base_config.id)
    ).scalar()

    parser = CustomConfigParser()
    parsed_data = parser.parse(base_config.content)

    table_data = []
    for key, value in parsed_data.items():
        param = BaseConfigFileParameter.query.filter_by(
            base_config_file_id=base_config.id,
            name=key
        ).first()

        if param:
            table_data.append({
                'name': param.name,
                'value': param.value,
                'type': param.type,
                'min_value': param.min_value,
                'default_value': param.value,
                'max_value': param.max_value,
                'numeric_rule': param.numeric_rule,
                'regex_rule': param.regex_rule,
                'status': 'À jour'
            })
        else:
            table_data.append({
                'name': key,
                'value': value,
                'type': 'float' if isinstance(value, (int, float)) else 'text',
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
        
        if not all(key in data for key in ['value', 'min', 'max', 'numeric_rule', 'regex', 'type']):
            raise ValueError("Données manquantes")
        
        param.value = data['value']
        param.min_value = float(data['min']) if data['min'] else None
        param.max_value = float(data['max']) if data['max'] else None
        param.numeric_rule = data['numeric_rule']
        param.regex_rule = data['regex']
        param.type = data['type']
        param.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        base_config = param.base_config_file
        last_modified = get_last_modified(base_config.id)
        parameter_count = BaseConfigFileParameter.query.filter_by(base_config_file_id=base_config.id).count()
        
        return jsonify({
            'status': 'success',
            'last_modified': last_modified.strftime('%d/%m/%Y %H:%M') if last_modified else 'Jamais modifié',
            'parameter_count': parameter_count
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
        'regex': param.regex_rule,
        'type': param.type
    })

@parsed_files_bp.route('/create_parameter', methods=['POST'])
def create_parameter():
    try:
        data = request.get_json()
        
        required_fields = ['base_config_file_id', 'name', 'value', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Champ manquant: {field}'}), 400

        try:
            base_config_file_id = int(data['base_config_file_id'])
        except ValueError:
            return jsonify({'status': 'error', 'message': 'base_config_file_id invalide'}), 400

        new_param = BaseConfigFileParameter(
            base_config_file_id=base_config_file_id,
            name=data['name'],
            value=data['value'],
            min_value=float(data['min_value']) if data.get('min_value') else None,
            max_value=float(data['max_value']) if data.get('max_value') else None,
            numeric_rule=data.get('numeric_rule'),
            regex_rule=data.get('regex_rule'),
            type=data['type'],
            in_use=True
        )
        db.session.add(new_param)
        db.session.commit()

        last_modified = get_last_modified(base_config_file_id)
        parameter_count = BaseConfigFileParameter.query.filter_by(base_config_file_id=base_config_file_id).count()

        return jsonify({
            'status': 'success',
            'new_param_id': new_param.id,
            'last_modified': last_modified.strftime('%d/%m/%Y %H:%M') if last_modified else 'Jamais modifié',
            'parameter_count': parameter_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

def get_last_modified(base_config_file_id):
    last_modified = db.session.query(func.max(func.coalesce(BaseConfigFileParameter.updated_at, BaseConfigFileParameter.created_at))).filter_by(base_config_file_id=base_config_file_id).scalar()
    base_config = SoftwareBaseConfigurationFile.query.get(base_config_file_id)
    base_date = base_config.updated_at or base_config.created_at
    return max(filter(None, [last_modified, base_date]))
