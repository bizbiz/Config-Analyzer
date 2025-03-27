# app/routes/robot_models.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.robot_model import RobotModel
from app.models.entities.software import Software
from app.models.parameters.definitions import ParameterDefinition
from app.models.entities.robot_instance import RobotInstance
from app.models.enums import EntityType
from app.extensions import db
from app.utils.param_helpers import get_applicable_params_configs, get_unconfigured_params

robot_models_bp = Blueprint('robot_models', __name__, url_prefix='/robot-models')

@robot_models_bp.route('/list')
def list():
    robot_models = RobotModel.query.options(
        db.joinedload(RobotModel.software)
    ).all()
    
    return render_template('list/robot_models.html', 
                         robot_models=robot_models,
                         softwares=Software.query.all())

@robot_models_bp.route('/view/<string:slug>')
def view(slug):
    robot_model = RobotModel.query.filter_by(slug=slug).options(
        db.joinedload(RobotModel.software),
        db.joinedload(RobotModel.instances)
    ).first_or_404()

    # Récupération des paramètres
    applicable_configs = ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == EntityType.ROBOT_MODEL
    ).all()
    
    configured_params = ParameterValue.query.filter(
        ParameterValue.entity_id == robot_model.id,
        ParameterValue.entity_type == EntityType.ROBOT_MODEL
    ).all()
    
    return render_template(
        'view/robot_model.html',
        robot_model=robot_model,
        instances=robot_model.instances,
        configured_params=configured_params,
        unconfigured_params=get_unconfigured_params(robot_model.id, applicable_configs)
    )

@robot_models_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        company = request.form.get('company').strip()
        software_id = request.form.get('software_id')

        if not name:
            flash("Le nom du modèle est obligatoire", "error")
            return redirect(url_for('robot_models.add'))

        try:
            new_model = RobotModel(
                name=name,
                company=company,
                software_id=software_id
            )
            db.session.add(new_model)
            db.session.commit()
            flash("Modèle créé avec succès", "success")
            return redirect(url_for('robot_models.list_models'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création : {str(e)}", "error")

    return render_template('add/robot_model.html',
                         softwares=Software.query.all())

@robot_models_bp.route('/edit/<string:slug>', methods=['GET', 'POST'])
def edit(slug):
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        robot_model.name = request.form['name'].strip()
        robot_model.company = request.form['company'].strip()
        robot_model.software_id = request.form['software_id']

        try:
            db.session.commit()
            flash("Modèle mis à jour avec succès", "success")
            return redirect(url_for('robot_models.view', slug=robot_model.slug))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur de mise à jour : {str(e)}", "error")

    return render_template('edit/robot_model.html',
                         robot_model=robot_model,
                         softwares=Software.query.all())

@robot_models_bp.route('/delete/<string:slug>', methods=['POST'])
def delete(slug):
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    try:
        db.session.delete(robot_model)
        db.session.commit()
        flash("Modèle supprimé avec succès", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur de suppression : {str(e)}", "error")
    
    return redirect(url_for('robot_models.list_models'))
