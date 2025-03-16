from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from app.models import AdditionalParametersConfig, AdditionalParameter, RobotModel, ParameterType
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user

# Renommer le blueprint pour plus de clarté
params_config_bp = Blueprint('params_config', __name__, url_prefix='/params-config')

@params_config_bp.route('/list')
def list():
    """Liste toutes les configurations de paramètres"""
    configs = AdditionalParametersConfig.query.all()
    
    # Enrichir les données avec des informations sur l'entité liée
    for config in configs:
        try:
            if config.table_name == 'robot_models':
                entity = RobotModel.query.get(config.table_id)
                config.entity_name = entity.name if entity else "Modèle inconnu"
            else:
                config.entity_name = f"{config.table_name} #{config.table_id}"
        except Exception:
            config.entity_name = "Entité inconnue"
    
    return render_template('list/partials/params_config.html', items=configs)

@params_config_bp.route('/add/<string:entity_name>', methods=['GET', 'POST'])
def add(entity_name):
    """Ajoute une configuration de paramètres pour une entité"""
    robot_model = RobotModel.query.filter_by(name=entity_name).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        param_type = request.form.get('type')
        
        if not name or not param_type:
            flash("Le nom et le type sont obligatoires", "error")
            return redirect(url_for('params_config.add', entity_name=entity_name))
        
        try:
            # Convertir le type en ParameterType enum
            enum_type = ParameterType(param_type)
            
            # Initialiser le tableau de valeurs
            values_array = []
            
            # Gérer les valeurs selon le type
            if enum_type == ParameterType.ENUM:
                # Récupérer les valeurs d'énumération (filtre les valeurs vides)
                values_array = [v for v in request.form.getlist('enum_values[]') if v.strip()]
            else:
                # Pour text et numeric, on prend juste la valeur unique
                value = request.form.get('value')
                if value:
                    values_array = [value]
            
            # Créer le nouveau paramètre
            new_config = AdditionalParametersConfig(
                table_name='robot_models',
                table_id=robot_model.id,
                type=enum_type,
                name=name,
                values=values_array,
                created_by_user_id=current_user.id if current_user.is_authenticated else None
            )
            
            db.session.add(new_config)
            db.session.commit()
            
            flash(f"Configuration de paramètre '{name}' ajoutée avec succès", "success")
            return redirect(url_for('robot_models.view', robot_model_name=entity_name))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de la configuration : {str(e)}", "error")
    
    return render_template(
        'add/params_config.html',
        robot_model=robot_model
    )

@params_config_bp.route('/edit/<string:entity_name>/<int:config_id>', methods=['GET', 'POST'])
def edit(entity_name, config_id):
    """Édite une configuration de paramètres existante"""
    robot_model = RobotModel.query.filter_by(name=entity_name).first_or_404()
    config = AdditionalParametersConfig.query.get_or_404(config_id)
    
    # Vérifier que la configuration appartient bien à ce modèle de robot
    if config.table_name != 'robot_models' or config.table_id != robot_model.id:
        abort(404)
    
    if request.method == 'POST':
        config.name = request.form.get('name')
        new_type = ParameterType(request.form.get('type'))
        config.type = new_type
        
        # Gérer les valeurs selon le type
        if new_type == ParameterType.ENUM:
            # Récupérer les valeurs d'énumération (filtre les valeurs vides)
            config.values = [v for v in request.form.getlist('enum_values[]') if v.strip()]
        else:
            # Pour text et numeric, on prend juste la valeur unique
            value = request.form.get('value')
            config.values = [value] if value else []
        
        config.updated_by_user_id = current_user.id if current_user.is_authenticated else None
        
        try:
            db.session.commit()
            flash("Configuration mise à jour avec succès", "success")
            return redirect(url_for('robot_models.view', robot_model_name=entity_name))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour : {str(e)}", "error")
    
    return render_template(
        'edit/params_config.html',
        robot_model=robot_model,
        config=config
    )

@params_config_bp.route('/delete/<string:entity_name>/<int:config_id>', methods=['POST'])
def delete(entity_name, config_id):
    """Supprime une configuration de paramètres"""
    robot_model = RobotModel.query.filter_by(name=entity_name).first_or_404()
    config = AdditionalParametersConfig.query.get_or_404(config_id)
    
    # Vérifier que la configuration appartient bien à ce modèle de robot
    if config.table_name != 'robot_models' or config.table_id != robot_model.id:
        abort(404)
    
    try:
        # Supprimer d'abord tous les paramètres associés
        AdditionalParameter.query.filter_by(additional_parameters_config_id=config.id).delete()
        
        # Puis supprimer la configuration
        db.session.delete(config)
        db.session.commit()
        
        flash("Configuration et paramètres associés supprimés avec succès", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    return redirect(url_for('robot_models.view', robot_model_name=entity_name))
