from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Software, RobotModel
from app.extensions import db

software_bp = Blueprint('software', __name__)

@software_bp.route('/software')
def list_software():
    software = Software.query.all()
    robot_models = RobotModel.query.all()
    return render_template('list/software.html', software=software, robot_models=robot_models)

@software_bp.route('/software/add', methods=['GET', 'POST'])
def add_software():
    if request.method == 'POST':
        name = request.form.get('name')
        version = request.form.get('version')

        if not name or not version:
            flash("Le nom et la version sont obligatoires.", "error")
            return redirect(url_for('software.add_software'))

        new_software = Software(name=name, version=version)
        db.session.add(new_software)
        db.session.commit()

        flash("Logiciel ajouté avec succès !", "success")
        return redirect(url_for('software.list_software'))

    robot_models = RobotModel.query.all()
    return render_template('add/software.html', robot_models=robot_models)

@software_bp.route('/software/edit/<int:software_id>', methods=['GET', 'POST'])
def edit_software(software_id):
    software = Software.query.get_or_404(software_id)
    if request.method == 'POST':
        software.name = request.form['name']
        software.version = request.form['version']

        db.session.commit()
        flash("Logiciel modifié avec succès !", "success")
        return redirect(url_for('software.list_software'))

    robot_models = RobotModel.query.all()
    selected_robot_models = [robot_model.id for robot_model in software.robot_modeles]
    return render_template('edit/software.html', software=software, robot_models=robot_models, selected_robot_models=selected_robot_models)

@software_bp.route('/software/delete/<int:software_id>', methods=['GET'])
def delete_software(software_id):
    software = Software.query.get_or_404(software_id)
    db.session.delete(software)
    db.session.commit()
    flash("Logiciel supprimé avec succès !", "success")
    return redirect(url_for('software.list_software'))