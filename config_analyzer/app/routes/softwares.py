# app/routes/softwares.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.software import Software
from app.models.entities.robot_model import RobotModel
from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType
from app.extensions import db
from sqlalchemy.exc import IntegrityError

softwares_bp = Blueprint('softwares', __name__, url_prefix='/softwares')

@softwares_bp.route('/list')
def list():
    softwares = Software.query.all()
    robot_models = RobotModel.query.all()
    return render_template('list/softwares.html', 
                           softwares=softwares,
                           robot_models=robot_models)

@softwares_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            new_software = Software(
                name=request.form['name'],
                description=request.form.get('description', '')
            )
            db.session.add(new_software)
            
            for robot_model_id in request.form.getlist('robot_model_ids'):
                robot_model = RobotModel.query.get(robot_model_id)
                if robot_model:
                    new_software.robot_models.append(robot_model)
            
            db.session.commit()
            flash("Logiciel ajouté avec succès", "success")
            return redirect(url_for('softwares.list_softwares'))
        except IntegrityError:
            db.session.rollback()
            flash("Un logiciel avec ce nom existe déjà", "error")
    
    robot_models = RobotModel.query.all()
    return render_template('add/software.html', robot_models=robot_models)

@softwares_bp.route('/edit/<string:slug>', methods=['GET', 'POST'])
def edit(slug):
    software = Software.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        try:
            software.name = request.form['name']
            software.description = request.form.get('description', '')
            
            software.robot_models = []
            for robot_model_id in request.form.getlist('robot_model_ids'):
                robot_model = RobotModel.query.get(robot_model_id)
                if robot_model:
                    software.robot_models.append(robot_model)
            
            db.session.commit()
            flash("Logiciel mis à jour avec succès", "success")
            return redirect(url_for('softwares.list_softwares'))
        except IntegrityError:
            db.session.rollback()
            flash("Un logiciel avec ce nom existe déjà", "error")
    
    robot_models = RobotModel.query.all()
    return render_template('edit/software.html', 
                           software=software, 
                           robot_models=robot_models)

@softwares_bp.route('/delete/<string:slug>', methods=['POST'])
def delete(slug):
    software = Software.query.filter_by(slug=slug).first_or_404()
    try:
        db.session.delete(software)
        db.session.commit()
        flash("Logiciel supprimé avec succès", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    return redirect(url_for('softwares.list_softwares'))

@softwares_bp.route('/view/<string:slug>')
def view_software(slug):
    software = Software.query.filter_by(slug=slug).first_or_404()
    parameter_definitions = ParameterDefinition.query.filter_by(target_entity=EntityType.SOFTWARE).all()
    parameter_values = ParameterValue.query.filter_by(entity_id=software.id, entity_type=EntityType.SOFTWARE).all()
    return render_template('view/software.html', 
                           software=software,
                           parameter_definitions=parameter_definitions,
                           parameter_values=parameter_values)
