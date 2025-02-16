from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotModel, Software
from app.extensions import db

robot_models_bp = Blueprint('robot_models', __name__)

@robot_models_bp.route('/robot_models')
def list_robot_models():
    robot_models = RobotModel.query.all()
    softwares = Software.query.all()
    return render_template('list/robot_models.html', robot_models=robot_models, softwares=softwares)

@robot_models_bp.route('/robot_models/<int:robot_model_id>/view')
def view_robot_model(robot_model_id):
    robot_model = RobotModel.query.get_or_404(robot_model_id)
    return render_template('view/robot_model.html', robot_model=robot_model)

@robot_models_bp.route('/robot_models/add', methods=['GET', 'POST'])
def add_robot_model():
    if request.method == 'POST':
        name = request.form.get('name')
        company = request.form.get('company')
        software_id = request.form.get('software_id')
        
        if not name:
            flash("Le nom du modèle de robot est obligatoire.", "error")
            return redirect(url_for('robot_models.add_robot_model'))
        
        new_robot_model = RobotModel(name=name, company=company, software_id=software_id)
        db.session.add(new_robot_model)
        db.session.commit()
        
        flash("Modèle de robot ajouté avec succès !", "success")
        return redirect(url_for('robot_models.list_robot_models'))
    
    softwares = Software.query.all()
    return render_template('add/robot_model.html', softwares=softwares)

@robot_models_bp.route('/robot_models/edit/<int:robot_model_id>', methods=['GET', 'POST'])
def edit_robot_model(robot_model_id):
    robot_model = RobotModel.query.get_or_404(robot_model_id)
    if request.method == 'POST':
        robot_model.name = request.form['name']
        robot_model.company = request.form['company']
        robot_model.software_id = request.form['software_id']
        
        db.session.commit()
        flash("Modèle de robot modifié avec succès !", "success")
        return redirect(url_for('robot_models.list_robot_models'))
    
    softwares = Software.query.all()
    return render_template('edit/robot_model.html', robot_model=robot_model, softwares=softwares)

@robot_models_bp.route('/robot_models/delete/<int:robot_model_id>', methods=['GET'])
def delete_robot_model(robot_model_id):
    robot_model = RobotModel.query.get_or_404(robot_model_id)
    db.session.delete(robot_model)
    db.session.commit()
    flash("Modèle de robot supprimé avec succès !", "success")
    return redirect(url_for('robot_models.list_robot_models'))