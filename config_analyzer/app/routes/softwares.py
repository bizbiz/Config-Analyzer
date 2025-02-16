from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Software, RobotModel
from app.extensions import db

softwares_bp = Blueprint('softwares', __name__)

@softwares_bp.route('/softwares')
def list_softwares():
    softwares = Software.query.all()
    robot_models = RobotModel.query.all()
    return render_template('list/softwares.html', softwares=softwares, robot_models=robot_models)

@softwares_bp.route('/softwares/add', methods=['GET', 'POST'])
def add_software():
    if request.method == 'POST':
        name = request.form.get('name')
        robot_model_ids = request.form.getlist('robot_model_ids')
        
        if not name:
            flash("Le nom du logiciel est obligatoire.", "error")
            return redirect(url_for('softwares.add_software'))
        
        new_software = Software(name=name)
        db.session.add(new_software)
        db.session.commit()

        for robot_model_id in robot_model_ids:
            robot_model = RobotModel.query.get(robot_model_id)
            if robot_model:
                new_software.robot_models.append(robot_model)
        
        db.session.commit()
        
        flash("Logiciel ajouté avec succès !", "success")
        return redirect(url_for('softwares.list_softwares'))
    
    robot_models = RobotModel.query.all()
    return render_template('add/software.html', robot_models=robot_models)

@softwares_bp.route('/softwares/edit/<int:software_id>', methods=['GET', 'POST'])
def edit_software(software_id):
    software = Software.query.get_or_404(software_id)
    if request.method == 'POST':
        software.name = request.form['name']
        robot_model_ids = request.form.getlist('robot_model_ids')

        software.robot_models.clear()
        for robot_model_id in robot_model_ids:
            robot_model = RobotModel.query.get(robot_model_id)
            if robot_model:
                software.robot_models.append(robot_model)
        
        db.session.commit()
        flash("Logiciel modifié avec succès !", "success")
        return redirect(url_for('softwares.list_softwares'))
    
    robot_models = RobotModel.query.all()
    return render_template('edit/software.html', software=software, robot_models=robot_models)

@softwares_bp.route('/softwares/delete/<int:software_id>', methods=['GET'])
def delete_software(software_id):
    software = Software.query.get_or_404(software_id)
    db.session.delete(software)
    db.session.commit()
    flash("Logiciel supprimé avec succès !", "success")
    return redirect(url_for('softwares.list_softwares'))

@softwares_bp.route('/softwares/<int:software_id>/view', methods=['GET'])
def view_software(software_id):
    software = Software.query.get_or_404(software_id)
    return render_template('view/software.html', software=software)