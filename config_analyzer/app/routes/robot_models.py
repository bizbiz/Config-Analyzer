# app/routes/robot_models.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.robot_model import RobotModel
from app.models.entities.software import Software
from app.models.associations.robot_model_software import RobotModelSoftware
from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType
from app.extensions import db
from app.utils.param_helpers import get_unconfigured_params
import traceback

robot_models_bp = Blueprint('robot_models', __name__, url_prefix='/robot-models')

@robot_models_bp.route('/list')
def list():
    robot_models = RobotModel.query.options(
        db.joinedload(RobotModel.software_associations).joinedload(RobotModelSoftware.software)
    ).all()
    
    return render_template('list/robot_models.html', 
                         robot_models=robot_models,
                         softwares=Software.query.all())

@robot_models_bp.route('/view/<string:slug>')
def view(slug):
    # Supprimez joinedload sur 'instances' qui cause l'erreur
    robot_model = RobotModel.query.filter_by(slug=slug).options(
        db.joinedload(RobotModel.software_associations).joinedload(RobotModelSoftware.software)
    ).first_or_404()

    # Chargez les instances séparément car il s'agit d'une requête dynamique
    instances = robot_model.instances.all()

    # Récupération des paramètres
    applicable_configs = ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == EntityType.ROBOT_MODEL
    ).all()
    
    configured_params = ParameterValue.query.filter(
        ParameterValue.entity_id == robot_model.id,
        ParameterValue.entity_type == EntityType.ROBOT_MODEL
    ).all()
    
    return render_template(
        'view/robot_model.html',
        robot_model=robot_model,
        instances=instances,  # Passer les instances chargées séparément
        configured_params=configured_params,
        unconfigured_params=get_unconfigured_params(robot_model.id, applicable_configs)
    )

@robot_models_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        company = request.form.get('company', '').strip()
        software_ids = request.form.getlist('software_ids')  # Récupère tous les logiciels sélectionnés

        if not name:
            flash("Le nom du modèle est obligatoire", "error")
            return redirect(url_for('robot_models.add'))

        try:
            # Créer le modèle de robot
            new_model = RobotModel(name=name, company=company)
            db.session.add(new_model)
            db.session.flush()  # Obtenir l'ID sans commit complet
            
            # Ajouter les associations de logiciels si sélectionnées
            for software_id in software_ids:
                if software_id:  # Ignorer les sélections vides
                    software = Software.query.get(software_id)
                    if software:
                        association = RobotModelSoftware(
                            robot_model_id=new_model.id,
                            software_id=software.id
                        )
                        db.session.add(association)
            
            db.session.commit()
            flash("Modèle créé avec succès", "success")
            return redirect(url_for('robot_models.list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création : {str(e)}", "error")
            print(traceback.format_exc())  # Pour le débogage
            
    return render_template('add/robot_model.html',
                         softwares=Software.query.all())

@robot_models_bp.route('/edit/<string:slug>', methods=['GET', 'POST'])
def edit(slug):
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        robot_model.name = request.form.get('name', '').strip()
        robot_model.company = request.form.get('company', '').strip()
        
        # Gérer les associations de logiciels
        software_ids = request.form.getlist('software_ids')
        
        # Supprimer toutes les associations existantes
        RobotModelSoftware.query.filter_by(robot_model_id=robot_model.id).delete()
        
        # Ajouter les nouvelles associations
        for software_id in software_ids:
            if software_id:  # Ignorer les sélections vides
                software = Software.query.get(software_id)
                if software:
                    association = RobotModelSoftware(
                        robot_model_id=robot_model.id,
                        software_id=software.id
                    )
                    db.session.add(association)

        try:
            db.session.commit()
            flash("Modèle mis à jour avec succès", "success")
            return redirect(url_for('robot_models.view', slug=robot_model.slug))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur de mise à jour : {str(e)}", "error")
            print(traceback.format_exc())  # Pour le débogage

    # Précharger les logiciels associés pour le formulaire
    selected_software_ids = [assoc.software_id for assoc in robot_model.software_associations]
    
    return render_template('edit/robot_model.html',
                         robot_model=robot_model,
                         softwares=Software.query.all(),
                         selected_software_ids=selected_software_ids)

@robot_models_bp.route('/delete/<string:slug>', methods=['POST'])
def delete(slug):
    robot_model = RobotModel.query.filter_by(slug=slug).first_or_404()
    
    try:
        # Les associations seront supprimées automatiquement grâce au cascade="all, delete-orphan"
        db.session.delete(robot_model)
        db.session.commit()
        flash("Modèle supprimé avec succès", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur de suppression : {str(e)}", "error")
        print(traceback.format_exc())  # Pour le débogage
    
    return redirect(url_for('robot_models.list'))