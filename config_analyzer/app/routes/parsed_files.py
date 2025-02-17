from flask import Blueprint, render_template
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software, ClientConfigurationFile, BaseConfigFileParameter
from app.extensions import db
from app.utils.custom_config_parser import CustomConfigParser
from sqlalchemy import select, func

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

    #Creation de l'instance pour parse
    parser = CustomConfigParser()

    # Parsing du contenu
    parsed_data = parser.parse(base_config.content)

    return render_template(
        'view/parsed_base_config_file.html',
        parsed_data=parsed_data,
        base_config=base_config,
        client_count=client_count,
        parameter_count=parameter_count
    )

    
@parsed_files_bp.route('/update_parameter/<int:param_id>', methods=['POST'])
def update_parameter(param_id):
    param = BaseConfigFileParameter.query.get_or_404(param_id)
    data = request.get_json()
    
    try:
        param.value = data['value']
        param.min_value = float(data['min']) if data['min'] else None
        param.max_value = float(data['max']) if data['max'] else None
        param.numeric_rule = data['numeric_rule']
        param.regex_rule = data['regex']
        param.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'last_modified': param.base_config_file.last_modified.strftime('%d/%m/%Y %H:%M')
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