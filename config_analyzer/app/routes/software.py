from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Software, RobotModel, RobotModelSoftware
from app.extensions import db

software_bp = Blueprint('software', __name__)

@software_bp.route('/software')
def list_software():
    softwares = Software.query.all()
    return render_template('software.html', softwares=softwares)

@software_bp.route('/software/add', methods=['GET', 'POST'])
def add_software():
    if request.method == 'POST':
        name = request.form.get('name')
        robot_model_ids = request.form.getlist('robot_model_ids')

        if not name:
            flash("Le nom est obligatoire.", "error")
            return redirect(url_for('software.add_software'))

        new_software = Software(name=name)
        db.session.add(new_software)
        db.session.commit()

        for robot_model_id in robot_model_ids:
            if robot_model_id:
                robot_model_software = RobotModelSoftware(software_id=new_software.id, robot_modele_id=int(robot_model_id))
                db.session.add(robot_model_software)
        
        db.session.commit()
        flash("Software ajouté avec succès !", "success")
        return redirect(url_for('software.list_software'))

    robot_models = RobotModel.query.all()
    return render_template('add_software.html', robot_models=robot_models)

@software_bp.route('/software/edit/<int:software_id>', methods=['GET', 'POST'])
def edit_software(software_id):
    software = Software.query.get_or_404(software_id)
    if request.method == 'POST':
        software.name = request.form['name']
        robot_model_ids = request.form.getlist('robot_model_ids')

        RobotModelSoftware.query.filter_by(software_id=software_id).delete()
        for robot_model_id in robot_model_ids:
            if robot_model_id:
                robot_model_software = RobotModelSoftware(software_id=software_id, robot_modele_id=int(robot_model_id))
                db.session.add(robot_model_software)

        db.session.commit()
        flash("Software modifié avec succès !", "success")
        return redirect(url_for('software.list_software'))
    
    robot_models = RobotModel.query.all()
    selected_robot_models = [rms.robot_modele_id for rms in software.robot_modeles]
    return render_template('edit_software.html', software=software, robot_models=robot_models, selected_robot_models=selected_robot_models)

@software_bp.route('/software/delete/<int:software_id>', methods=['GET'])
def delete_software(software_id):
    software = Software.query.get_or_404(software_id)
    RobotModelSoftware.query.filter_by(software_id=software_id).delete()
    db.session.delete(software)
    db.session.commit()
    flash("Software supprimé avec succès !", "success")
    return redirect(url_for('software.list_software'))