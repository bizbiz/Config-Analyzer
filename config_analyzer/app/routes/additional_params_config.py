from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from app.models import AdditionalParametersConfig, AdditionalParameter, RobotModel
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user

additional_params_config_bp = Blueprint('additional_params_config', __name__)

@additional_params_config_bp.route('/robot_models/<string:robot_model_name>/params_config/add', methods=['GET', 'POST'])
def add_params_config(robot_model_name):
    """Ajoute une configuration de paramètres pour un modèle de robot"""
    robot_model = RobotModel.query.filter_by(name=robot_model_name).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        param_type = request.form.get('type')
        
        if not name or not param_type:
            flash("Le nom et le type sont obligatoires", "error")
            return redirect(url_for('additional_params_config.add_params_config', robot_model_name=robot_model_name))
        
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
            return redirect(url_for('robot_models.view_robot_model', robot_model_name=robot_model_name))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de la configuration : {str(e)}", "error")
    
    return render_template(
        'add/params_config.html',
        robot_model=robot_model
    )

@additional_params_config_bp.route('/robot_models/<string:robot_model_name>/params_config/<int:config_id>/edit', methods=['GET', 'POST'])
def edit_params_config(robot_model_name, config_id):
    """Édite une configuration de paramètres existante"""
    robot_model = RobotModel.query.filter_by(name=robot_model_name).first_or_404()
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
            return redirect(url_for('robot_models.view_robot_model', robot_model_name=robot_model_name))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour : {str(e)}", "error")
    
    return render_template(
        'edit/params_config.html',
        robot_model=robot_model,
        config=config
    )


@additional_params_config_bp.route('/robot_models/<string:robot_model_name>/params_config/<int:config_id>/delete', methods=['POST'])
def delete_params_config(robot_model_name, config_id):
    """Supprime une configuration de paramètres"""
    robot_model = RobotModel.query.filter_by(name=robot_model_name).first_or_404()
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
    
    return redirect(url_for('robot_models.view_robot_model', robot_model_name=robot_model_name))
