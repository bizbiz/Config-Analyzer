from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Software, RobotModel
from app.extensions import db
from app.routes.additional_params import get_additional_params_data

softwares_bp = Blueprint('softwares', __name__, url_prefix='/softwares')

# Ajoutez cette fonction pour rendre get_additional_params_data disponible dans les templates
@softwares_bp.app_template_global()
def get_template_additional_params_data(table_name, table_id):
    return get_additional_params_data(table_name, table_id)

@softwares_bp.route('/list')
def list():
    """Liste tous les logiciels"""
    softwares = Software.query.all()
    robot_models = RobotModel.query.all()
    return render_template('list/partials/softwares.html', 
                          items=softwares, 
                          robot_models=robot_models)

@softwares_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute un nouveau logiciel"""
    if request.method == 'POST':
        name = request.form.get('name')
        robot_model_ids = request.form.getlist('robot_model_ids')
        
        if not name:
            flash("Le nom du logiciel est obligatoire.", "error")
            return redirect(url_for('softwares.add'))
        
        # Vérifier si le logiciel existe déjà
        existing = Software.query.filter_by(name=name).first()
        if existing:
            flash("Un logiciel avec ce nom existe déjà.", "error")
            return redirect(url_for('softwares.add'))
        
        new_software = Software(name=name)
        db.session.add(new_software)
        db.session.commit()

        # Associer les modèles de robots
        for robot_model_id in robot_model_ids:
            if robot_model_id:  # Vérifier que l'ID n'est pas vide
                robot_model = RobotModel.query.get(robot_model_id)
                if robot_model:
                    new_software.robot_models.append(robot_model)
        
        db.session.commit()
        
        flash("Logiciel ajouté avec succès !", "success")
        return redirect(url_for('softwares.list'))
    
    robot_models = RobotModel.query.all()
    return render_template('add/software.html', robot_models=robot_models)

@softwares_bp.route('/edit/<string:name>', methods=['GET', 'POST'])
def edit(name):
    """Édite un logiciel existant"""
    software = Software.query.filter_by(name=name).first_or_404()
    
    if request.method == 'POST':
        new_name = request.form['name']
        robot_model_ids = request.form.getlist('robot_model_ids')

        # Vérifier si le nouveau nom existe déjà (si différent de l'ancien)
        if new_name != name:
            existing = Software.query.filter_by(name=new_name).first()
            if existing:
                flash("Un logiciel avec ce nom existe déjà.", "error")
                return redirect(url_for('softwares.edit', name=name))

        software.name = new_name
        
        # Mettre à jour les associations avec les modèles de robots
        software.robot_models.clear()
        for robot_model_id in robot_model_ids:
            if robot_model_id:  # Vérifier que l'ID n'est pas vide
                robot_model = RobotModel.query.get(robot_model_id)
                if robot_model:
                    software.robot_models.append(robot_model)
        
        db.session.commit()
        flash("Logiciel modifié avec succès !", "success")
        return redirect(url_for('softwares.list'))
    
    robot_models = RobotModel.query.all()
    return render_template('edit/software.html', 
                          software=software, 
                          robot_models=robot_models)

@softwares_bp.route('/delete/<string:name>', methods=['GET', 'POST'])
def delete(name):
    """Supprime un logiciel"""
    software = Software.query.filter_by(name=name).first_or_404()
    
    if request.method == 'POST':
        db.session.delete(software)
        db.session.commit()
        flash("Logiciel supprimé avec succès !", "success")
        return redirect(url_for('softwares.list'))
    
    # Pour une requête GET, demander confirmation
    return render_template('delete/software.html', software=software)

@softwares_bp.route('/view/<string:name>', methods=['GET'])
def view(name):
    """Affiche les détails d'un logiciel"""
    software = Software.query.filter_by(name=name).first_or_404()
    return render_template('view/software.html', 
                          software=software, 
                          get_additional_params_data=get_additional_params_data)
