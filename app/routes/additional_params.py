#app/routes/additional_params.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from app.models.entities import Client, RobotInstance, RobotModel, Software, SoftwareVersion
from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError

additional_params_bp = Blueprint('additional_params', __name__, url_prefix='/additional-params')

def get_entity_by_table_name(table_name, table_id=None, entity_name=None):
    entity_mappings = {
        'client': Client,
        'robot_instance': RobotInstance,
        'robot_model': RobotModel,
        'software': Software,
        'software_version': SoftwareVersion
    }
    
    EntityClass = entity_mappings.get(table_name.lower().rstrip('s'))
    if not EntityClass:
        abort(404, f"Type d'entité inconnu: {table_name}")
    
    if entity_name:
        entity = EntityClass.query.filter_by(name=entity_name).first_or_404()
    else:
        entity = EntityClass.query.get_or_404(table_id)
    
    return entity, EntityClass.__tablename__



# Fonction utilitaire pour obtenir le nom d'affichage de l'entité
def get_entity_display_name(entity, table_name):
    if table_name == 'clients':
        return entity.name
    elif table_name == 'robot_clients':
        return f"Robot {entity.serial_number} - {entity.client.name}"
    elif table_name == 'robot_models':
        return entity.name
    elif table_name == 'software':
        return entity.name
    elif table_name == 'software_versions':
        return f"{entity.software.name} v{entity.version}"
    else:
        return f"Entité #{entity.id}"

# ======== ROUTES D'AFFICHAGE ========

@additional_params_bp.route('/view/<string:table_name>/<string:entity_identifier>')
def view_additional_params(table_name, entity_identifier):
    entity, actual_table_name = get_entity_by_table_name(table_name, entity_name=entity_identifier)
    entity_name = get_entity_display_name(entity, actual_table_name)
    
    parameter_definitions = ParameterDefinition.query.filter_by(target_entity=entity.entity_type).all()
    parameter_values = ParameterValue.query.filter_by(
        entity_id=entity.id,
        entity_type=entity.entity_type
    ).all()
    
    return render_template(
        'view/additional_params.html',
        entity=entity,
        entity_name=entity_name,
        table_name=actual_table_name,
        parameter_definitions=parameter_definitions,
        parameter_values=parameter_values
    )


@additional_params_bp.route('/list')
def list_additional_params():
    """Liste toutes les configurations de paramètres additionnels"""
    configs = ParameterDefinition.query.all()
    
    # Enrichir les configurations avec des informations supplémentaires
    for config in configs:
        config.param_count = ParameterValue.query.filter_by(
            additional_parameters_config_id=config.id
        ).count()
        
        try:
            entity, actual_table_name = get_entity_by_table_name(config.table_name, table_id=config.table_id)
            config.entity_name = get_entity_display_name(entity, actual_table_name)
        except:
            config.entity_name = f"Entité inconnue ({config.table_name} #{config.table_id})"
    
    return render_template(
        'list/additional_params.html',
        configs=configs
    )

# ======== ROUTES D'ÉDITION ========

@additional_params_bp.route('/edit/<string:table_name>/<string:entity_identifier>', methods=['GET', 'POST'])
def edit_additional_params(table_name, entity_identifier):
    entity, actual_table_name = get_entity_by_table_name(table_name, entity_name=entity_identifier)
    entity_name = entity.name
    
    if request.method == 'POST':
        try:
            for key, value in request.form.items():
                if key.startswith('param_'):
                    param_id = int(key.split('_')[1])
                    param_value = ParameterValue.query.get(param_id)
                    if param_value:
                        param_value.value = value
                    else:
                        new_param = ParameterValue(
                            parameter_definition_id=param_id,
                            entity_id=entity.id,
                            entity_type=entity.entity_type,
                            value=value
                        )
                        db.session.add(new_param)
            
            db.session.commit()
            flash('Paramètres mis à jour avec succès', 'success')
            return redirect(url_for('additional_params.view_additional_params', table_name=table_name, entity_identifier=entity_identifier))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour des paramètres : {str(e)}', 'danger')
    
    parameter_definitions = ParameterDefinition.query.filter_by(target_entity=entity.entity_type).all()
    parameter_values = ParameterValue.query.filter_by(entity_id=entity.id, entity_type=entity.entity_type).all()
    
    return render_template(
        'edit/additional_params.html',
        entity=entity,
        entity_name=entity_name,
        table_name=actual_table_name,
        parameter_definitions=parameter_definitions,
        parameter_values=parameter_values
    )


@additional_params_bp.route('/add/<string:table_name>/<string:entity_identifier>', methods=['GET', 'POST'])
def add_additional_param(table_name, entity_identifier):
    entity, actual_table_name = get_entity_by_table_name(table_name, entity_name=entity_identifier)
    
    if request.method == 'POST':
        name = request.form.get('name')
        param_type = request.form.get('type')
        
        if not name or not param_type:
            flash("Le nom et le type du paramètre sont obligatoires.", "error")
            return redirect(url_for('additional_params.add_additional_param', table_name=table_name, entity_identifier=entity_identifier))
        
        try:
            # Créer la nouvelle définition de paramètre
            new_definition = ParameterDefinition(
                name=name,
                target_entity=entity.entity_type,
                type=param_type
            )
            db.session.add(new_definition)
            db.session.flush()
            
            # Créer la nouvelle valeur de paramètre
            value = request.form.get('value', '')
            if param_type == 'enum':
                enum_values = request.form.getlist('enum_values[]')
                value = ','.join(filter(None, enum_values))
            
            new_value = ParameterValue(
                parameter_definition_id=new_definition.id,
                entity_id=entity.id,
                entity_type=entity.entity_type,
                value=value
            )
            db.session.add(new_value)
            db.session.commit()
            
            flash(f"Paramètre '{name}' ajouté avec succès !", "success")
            return redirect(url_for('additional_params.view_additional_params', table_name=table_name, entity_identifier=entity_identifier))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout du paramètre : {str(e)}", "error")
    
    return render_template(
        'add/additional_params.html',
        table_name=actual_table_name,
        entity_name=entity.name,
        entity=entity
    )


def get_additional_params_data(entity):
    """Récupère les données des paramètres additionnels pour une entité donnée"""
    parameter_definitions = ParameterDefinition.query.filter_by(target_entity=entity.entity_type).all()
    parameter_values = ParameterValue.query.filter_by(
        entity_id=entity.id,
        entity_type=entity.entity_type
    ).all()
    
    return {
        'parameter_definitions': parameter_definitions,
        'parameter_values': parameter_values,
        'has_params': len(parameter_values) > 0
    }
