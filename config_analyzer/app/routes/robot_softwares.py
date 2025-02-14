# routes/robot_softwares.py
from flask import Blueprint, request, jsonify
from config_analyzer.models import db, Robot, Software, robot_software

robot_softwares_bp = Blueprint('robot_softwares', __name__)

@robot_softwares_bp.route('/api/robot-softwares', methods=['POST'])
def add_compatibility():
    data = request.json
    robot = Robot.query.get(data['robot_id'])
    software = Software.query.get(data['software_id'])
    
    insert = robot_softwares.insert().values(
        robot_id=robot.id,
        software_id=software.id,
        version=data['version']
    )
    db.session.execute(insert)
    db.session.commit()
    
    return jsonify({'message': 'Compatibilité ajoutée'}), 201

@robot_softwares_bp.route('/api/robot-softwares/<int:robot_id>')
def get_compatibilities(robot_id):
    robot = Robot.query.get(robot_id)
    compatibilities = db.session.query(
        Software.name,
        robot_softwares.c.version
    ).join(robot_softwares).filter(
        robot_softwares.c.robot_id == robot_id
    ).all()
    
    return jsonify([{
        'software': c[0],
        'version': c[1]
    } for c in compatibilities])
