from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotModel, Software, RobotModelSoftware
from app.extensions import db

robot_models_bp = Blueprint('robot_models', __name__)

@robot_models_bp.route('/robot_models')
def list_robot_models():
    robot_models = RobotModel.query.all()
    return render_template('robot_models.html', robot_models=robot_models)

@robot_models_bp.route('/robot_models/add', methods=['GET', 'POST'])
def add_robot_model():
    if request.method == 'POST':
        name = request.form.get('name')
        company = request.form.get('company')
        software_ids = request.form.getlist('software_ids')

        if not name or not company:
            flash("Le nom et la société sont obligatoires.", "error")
            return redirect(url_for('robot_models.add_robot_model'))

        new_robot_model = RobotModel(name=name, company=company)
        db.session.add(new_robot_model)
        db.session.commit()

        for software_id in software_ids:
            if software_id:
                robot_model_software = RobotModelSoftware(robot_modele_id=new_robot_model.id, software_id=int(software_id))
                db.session.add(robot_model_software)
        
        db.session.commit()
        flash("Modèle de robot ajouté avec succès !", "success")
        return redirect(url_for('robot_models.list_robot_models'))

    softwares = Software.query.all()
    return render_template('add_robot_model.html', softwares=softwares)

@robot_models_bp.route('/robot_models/edit/<int:robot_model_id>', methods=['GET', 'POST'])
def edit_robot_model(robot_model_id):
    robot_model = RobotModel.query.get_or_404(robot_model_id)
    if request.method == 'POST':
        robot_model.name = request.form['name']
        robot_model.company = request.form['company']
        software_ids = request.form.getlist('software_ids')

        RobotModelSoftware.query.filter_by(robot_modele_id=robot_model_id).delete()
        for software_id in software_ids:
            if software_id:
                robot_model_software = RobotModelSoftware(robot_modele_id=robot_model_id, software_id=int(software_id))
                db.session.add(robot_model_software)

        db.session.commit()
        flash("Modèle de robot modifié avec succès !", "success")
        return redirect(url_for('robot_models.list_robot_models'))
    
    softwares = Software.query.all()
    selected_softwares = [rms.software_id for rms in robot_model.software]
    return render_template('edit_robot_model.html', robot_model=robot_model, softwares=softwares, selected_softwares=selected_softwares)

@robot_models_bp.route('/robot_models/delete/<int:robot_model_id>', methods=['GET'])
def delete_robot_model(robot_model_id):
    robot_model = RobotModel.query.get_or_404(robot_model_id)
    RobotModelSoftware.query.filter_by(robot_modele_id=robot_model_id).delete()
    db.session.delete(robot_model)
    db.session.commit()
    flash("Modèle de robot supprimé avec succès !", "success")
    return redirect(url_for('robot_models.list_robot_models'))