from flask import Blueprint, request, jsonify
from config_analyzer.models import db, ParametreLogiciel, Software, Client

parametres_bp = Blueprint('parametres', __name__)

@parametres_bp.route('/', methods=['POST'])
def add_parametre():
    data = request.get_json()
    
    new_param = ParametreLogiciel(
        client_id=data['client_id'],
        software_id=data['software_id'],
        version=data['version'],
        config=data['config']
    )
    
    db.session.add(new_param)
    db.session.commit()
    
    return jsonify({'message': 'Paramètre ajouté'}), 201

@parametres_bp.route('/<int:param_id>', methods=['DELETE'])
def delete_parametre(param_id):
    param = ParametreLogiciel.query.get_or_404(param_id)
    db.session.delete(param)
    db.session.commit()
    return jsonify({'message': 'Paramètre supprimé'}), 200

@parametres_bp.route('/api/<int:client_id>')
def get_params(client_id):
    params = ParametreLogiciel.query.filter_by(client_id=client_id).join(Software).all()
    return jsonify([{
        'id': p.id,
        'software': p.software.name,
        'version': p.version,
        'config': p.config
    } for p in params])
