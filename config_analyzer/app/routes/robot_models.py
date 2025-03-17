from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotModel, Software, AdditionalParametersConfig, RobotClient
from app.extensions import db

# Définir le préfixe d'URL pour toutes les routes liées aux modèles de robots
robot_models_bp = Blueprint('robot_models', __name__, url_prefix='/robot-models')

@robot_models_bp.route('/list')
def list():
    """Liste tous les modèles de robots"""
    robot_models = RobotModel.query.all()
    softwares = Software.query.all()
    return render_template('list/robot_models.html', robot_models=robot_models, softwares=softwares)

@robot_models_bp.route('/view/<string:slug>')
def view(slug):
    """Affiche un modèle de robot spécifique via son slug"""
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    # Récupérer les robots clients qui utilisent ce modèle
    robot_clients = RobotClient.query.filter_by(robot_modele_id=robot_model.id).all()
    
    # Pagination pour les configurations de paramètres
    page = request.args.get('config_page', 1, type=int)
    items_per_page = 20
    
    # Récupérer les configurations de paramètres pour ce modèle
    params_query = AdditionalParametersConfig.query.filter_by(
        table_name='robot_models',
        table_id=robot_model.id
    )
    
    total_items = params_query.count()
    params_configs = params_query.paginate(
        page=page, 
        per_page=items_per_page, 
        error_out=False
    ).items
    
    return render_template(
        'view/robot_model.html',
        robot_model=robot_model,
        robot_clients=robot_clients,  # Ajouter cette variable
        params_configs=params_configs,
        total_items=total_items,
        items_per_page=items_per_page,
        page=page,
        total_pages=(total_items + items_per_page - 1) // items_per_page,
        offset=(page - 1) * items_per_page,
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
        
        # Vérifie si un modèle avec ce nom existe déjà
        slug = RobotModel.generate_slug(name)
        existing = RobotModel.query.filter_by(slug=slug).first()
        if existing:
            flash(f"Un modèle avec ce nom ou un nom similaire existe déjà: {existing.name}", "error")
            return redirect(url_for('robot_models.add'))
        
        new_robot_model = RobotModel(name=name, company=company, software_id=software_id)
        db.session.add(new_robot_model)
        db.session.commit()
        
        flash("Modèle de robot ajouté avec succès !", "success")
        return redirect(url_for('robot_models.list'))
    
    softwares = Software.query.all()
    return render_template('add/robot_model.html', softwares=softwares)

@robot_models_bp.route('/edit/<string:slug>', methods=['GET', 'POST'])
def edit(slug):
    """Édite un modèle de robot existant via son slug"""
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        new_name = request.form['name']
        new_slug = RobotModel.generate_slug(new_name)
        
        # Vérifier si le nouveau slug existe déjà et n'appartient pas à ce modèle
        if new_slug != robot_model.slug:
            existing = RobotModel.query.filter_by(slug=new_slug).first()
            if existing and existing.id != robot_model.id:
                flash(f"Un modèle avec ce nom ou un nom similaire existe déjà: {existing.name}", "error")
                return render_template('edit/robot_model.html', robot_model=robot_model, softwares=Software.query.all())
        
        # Mettre à jour les champs
        robot_model.name = new_name
        robot_model.slug = new_slug  # Mettre à jour le slug
        robot_model.company = request.form['company']
        robot_model.software_id = request.form['software_id']
        
        db.session.commit()
        flash("Modèle de robot modifié avec succès !", "success")
        return redirect(url_for('robot_models.list'))
    
    softwares = Software.query.all()
    return render_template('edit/robot_model.html', robot_model=robot_model, softwares=softwares)

@robot_models_bp.route('/delete/<string:slug>', methods=['GET', 'POST'])
def delete(slug):
    """Supprime un modèle de robot via son slug"""
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        db.session.delete(robot_model)
        db.session.commit()
        flash("Modèle de robot supprimé avec succès !", "success")
        return redirect(url_for('robot_models.list'))
    
    # Pour une requête GET, demander confirmation
    return render_template('delete/robot_model.html', robot_model=robot_model)
