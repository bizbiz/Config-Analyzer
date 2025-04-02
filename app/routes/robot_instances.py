# config_analyzer/app/routes/robot_instances.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.client import Client
from app.models.entities.robot_model import RobotModel
from app.models.entities.robot_instance import RobotInstance
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError  # Ajout de l'import manquant

robot_instances_bp = Blueprint('robot_instances', __name__, url_prefix='/robot-instances')

@robot_instances_bp.route('/list')
def list():
    # Récupérer tous les robots
    robot_instances = RobotInstance.query.options(
        db.joinedload(RobotInstance.client),
        db.joinedload(RobotInstance.model),
        db.joinedload(RobotInstance.software_versions)
    ).all()
    
    # Calculer les statistiques
    robots_with_software = sum(1 for ri in robot_instances if ri.software_versions)
    
    # Obtenir le nombre de clients uniques
    client_ids = set(ri.client_id for ri in robot_instances)
    unique_clients = len(client_ids)
    
    # Récupérer les configurations de paramètres pour les robots
    from app.models.parameters.definitions import ParameterDefinition
    from app.models.enums import EntityType
    
    params_configs = ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == EntityType.ROBOT_INSTANCE
    ).all()
    
    # Sérialiser pour JavaScript
    configs_json = [{
        'id': config.id,
        'name': config.name,
        'description': config.description,
        'type': config.definition_type
    } for config in params_configs]
    
    return render_template('list/robot_instances.html', 
                          robot_instances=robot_instances,
                          robots_with_software=robots_with_software,
                          unique_clients=unique_clients,
                          configs_json=configs_json,
                          clients=Client.query.all(),
                          robot_models=RobotModel.query.all(),
                          form_data={},
                          preselected_model_id=None,
                          serial_number_error=None,
                          length_error=None,
                          height_error=None)

@robot_instances_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            # Récupération et validation des données du formulaire
            serial_number = request.form.get('serial_number')
            client_id = request.form.get('client_id')
            robot_model_id = request.form.get('robot_model_id')
            if not robot_model_id:
                robot_model_id = request.form.get('robot_modele_id')
            
            # Validation
            if not serial_number or not client_id or not robot_model_id:
                flash("Tous les champs obligatoires doivent être remplis", "error")
                return render_template('add/robot_instance.html',
                                    clients=Client.query.all(),
                                    robot_models=RobotModel.query.all(),
                                    form_data=request.form)
            
            # Obtenir les données du client et du modèle pour créer un nom
            client = Client.query.get(client_id)
            robot_model = RobotModel.query.get(robot_model_id)
            
            if not client or not robot_model:
                flash("Client ou modèle de robot invalide", "error")
                return render_template('add/robot_instance.html',
                                      clients=Client.query.all(),
                                      robot_models=RobotModel.query.all(),
                                      form_data=request.form)
            
            # Créer un nom pour l'entité (obligatoire)
            name = f"{client.name} - {robot_model.name} - {serial_number}"
            
            # Création du robot avec le nom
            new_robot = RobotInstance(
                name=name,  # Ajout du nom obligatoire
                serial_number=serial_number,
                client_id=int(client_id),
                robot_model_id=int(robot_model_id)
            )
                
            db.session.add(new_robot)
            db.session.commit()
            flash("Instance robot ajoutée avec succès", "success")
            return redirect(url_for('robot_instances.list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Erreur de format numérique : {str(e)}", "error")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur base de données : {str(e)}", "error")
        except TypeError as e:
            db.session.rollback()
            flash(f"Erreur type : {str(e)}", "error")
    
    return render_template('add/robot_instance.html',
                         clients=Client.query.all(),
                         robot_models=RobotModel.query.all(),
                         preselected_model_id=request.args.get('robot_model_id'))

@robot_instances_bp.route('/edit/<string:slug>', methods=['GET', 'POST'])
def edit(serial_number):
    robot = RobotInstance.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        try:
            robot.serial_number = request.form['serial_number']
            robot.client_id = request.form['client_id']
            robot.robot_model_id = request.form['robot_model_id']
            robot.length = float(request.form['length']) if request.form['length'] else None
            robot.height = float(request.form['height']) if request.form['height'] else None
            
            db.session.commit()
            flash("Modifications enregistrées", "success")
            return redirect(url_for('robot_instances.list'))
            
        except ValueError:
            flash("Valeurs numériques invalides", "error")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur base de données : {str(e)}", "error")
    
    return render_template('edit/robot_instance.html',
                         robot_instance=robot,
                         clients=Client.query.all(),
                         robot_models=RobotModel.query.all())

@robot_instances_bp.route('/delete/<string:slug>', methods=['POST'])
def delete(serial_number):
    robot = RobotInstance.query.filter_by(slug=slug).first_or_404()
    
    try:
        db.session.delete(robot)
        db.session.commit()
        flash("Instance robot supprimée", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur suppression : {str(e)}", "error")
    
    return redirect(url_for('robot_instances.list'))

@robot_instances_bp.route('/view/<string:slug>')
def view(slug):
    robot = RobotInstance.query.options(
        db.joinedload(RobotInstance.client),
        db.joinedload(RobotInstance.model),
        db.joinedload(RobotInstance.software_versions)
    ).filter_by(slug=slug).first_or_404()
    
    # Récupérer les configurations de paramètres applicables pour ce robot
    from app.models.parameters.definitions import ParameterDefinition
    from app.models.parameters.values import ParameterValue
    from app.models.enums import EntityType
    from app.utils.param_helpers import get_unconfigured_params
    
    applicable_configs = ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == EntityType.ROBOT_INSTANCE
    ).all()
    
    configured_params = ParameterValue.query.filter(
        ParameterValue.entity_id == robot.id,
        ParameterValue.entity_type == EntityType.ROBOT_INSTANCE
    ).all()
    
    unconfigured_params = get_unconfigured_params(robot.id, applicable_configs)
    
    return render_template('view/robot_instance.html', 
                          robot_instance=robot,
                          configured_params=configured_params,
                          unconfigured_params=unconfigured_params)