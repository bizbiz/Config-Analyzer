from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotModel, Software, AdditionalParametersConfig
from app.extensions import db

# Définir le préfixe d'URL pour toutes les routes liées aux modèles de robots
robot_models_bp = Blueprint('robot_models', __name__, url_prefix='/robot-models')

@robot_models_bp.route('/list')
def list():
    """Liste tous les modèles de robots"""
    robot_models = RobotModel.query.all()
    softwares = Software.query.all()
    return render_template('list/partials/robot_models.html', items=robot_models, softwares=softwares)

@robot_models_bp.route('/view/<string:name>')
def view(name):
    """Affiche un modèle de robot spécifique"""
    # Récupérer le modèle de robot par son nom
    robot_model = RobotModel.query.filter_by(name=name).first_or_404()
    
    # Récupérer les configurations de paramètres pour ce modèle
    params_configs = AdditionalParametersConfig.query.filter_by(
        table_name='robot_models',
        table_id=robot_model.id
    ).all()
    
    return render_template(
        'view/robot_model.html',
        robot_model=robot_model,
        params_configs=params_configs,
        entity=robot_model,
        entity_type='robot_model'
    )

@robot_models_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute un nouveau modèle de robot"""
    if request.method == 'POST':
        name = request.form.get('name')
        company = request.form.get('company')
        software_id = request.form.get('software_id')
        
        if not name:
            flash("Le nom du modèle de robot est obligatoire.", "error")
            return redirect(url_for('robot_models.add'))
        
        new_robot_model = RobotModel(name=name, company=company, software_id=software_id)
        db.session.add(new_robot_model)
        db.session.commit()
        
        flash("Modèle de robot ajouté avec succès !", "success")
        return redirect(url_for('robot_models.list'))
    
    softwares = Software.query.all()
    return render_template('add/robot_model.html', softwares=softwares)

@robot_models_bp.route('/edit/<string:name>', methods=['GET', 'POST'])
def edit(name):
    """Édite un modèle de robot existant"""
    robot_model = RobotModel.query.filter_by(name=name).first_or_404()
    
    if request.method == 'POST':
        robot_model.name = request.form['name']
        robot_model.company = request.form['company']
        robot_model.software_id = request.form['software_id']
        
        db.session.commit()
        flash("Modèle de robot modifié avec succès !", "success")
        return redirect(url_for('robot_models.list'))
    
    softwares = Software.query.all()
    return render_template('edit/robot_model.html', robot_model=robot_model, softwares=softwares)

@robot_models_bp.route('/delete/<string:name>', methods=['GET', 'POST'])
def delete(name):
    """Supprime un modèle de robot"""
    robot_model = RobotModel.query.filter_by(name=name).first_or_404()
    
    if request.method == 'POST':
        db.session.delete(robot_model)
        db.session.commit()
        flash("Modèle de robot supprimé avec succès !", "success")
        return redirect(url_for('robot_models.list'))
    
    # Pour une requête GET, demander confirmation
    return render_template('delete/robot_model.html', robot_model=robot_model)
