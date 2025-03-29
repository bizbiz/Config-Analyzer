# app/routes/configurations.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.configuration import ConfigurationInstance, ConfigSchema, ConfigFileParser
from app.models.entities import Client, Software, SoftwareVersion
from app.models.parameters import ParameterDefinition, ParameterValue
from app.models.enums import EntityType
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError

configurations_bp = Blueprint('configurations', __name__, url_prefix='/configurations')

@configurations_bp.route('/list')
def list():
    configurations = ConfigurationInstance.query.all()
    
    # Calcul des statistiques
    
    # Nombre de logiciels concernés
    # Nous comptons les logiciels distincts liés aux versions de logiciels utilisées
    # dans les configurations
    total_softwares = db.session.query(func.count(distinct(Software.id)))\
        .join(SoftwareVersion, SoftwareVersion.software_id == Software.id)\
        .join(ConfigurationInstance, ConfigurationInstance.software_version_id == SoftwareVersion.id)\
        .scalar()
    
    # Nombre de clients utilisant ces configurations
    total_clients = db.session.query(func.count(distinct(Client.id)))\
        .join(ClientConfiguration, ClientConfiguration.client_id == Client.id)\
        .join(ConfigurationInstance, ConfigurationInstance.id == ClientConfiguration.config_id)\
        .scalar()
    
    return render_template('list/configuration_instances.html', 
                          configurations=configurations,
                          total_softwares=total_softwares,
                          total_clients=total_clients)

@configurations_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            file = request.files['config_file']
            entity_type = request.form['entity_type']
            entity_id = request.form['entity_id']
            
            # Créer une nouvelle instance de configuration
            new_config = ConfigurationInstance(
                entity_type=EntityType[entity_type.upper()],
                entity_id=entity_id,
                file_name=file.filename,
                raw_content=file.read().decode('utf-8')
            )
            
            db.session.add(new_config)
            db.session.flush()  # Pour obtenir l'ID de la nouvelle configuration
            
            # Parser le fichier et extraire les paramètres
            parser = ConfigFileParser(new_config)
            for name, value in parser.parse():
                definition = ParameterDefinition.query.filter_by(name=name).first()
                if not definition:
                    definition = new_config._create_definition(name, value)
                    db.session.add(definition)
                
                param_value = ParameterValue(
                    definition=definition,
                    value=value,
                    configuration_instance=new_config
                )
                db.session.add(param_value)
            
            db.session.commit()
            flash("Configuration ajoutée avec succès", "success")
            return redirect(url_for('configurations.list_configurations'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de la configuration : {str(e)}", "error")
    
    entities = {
        'client': Client.query.all(),
        'software': Software.query.all(),
        'software_version': SoftwareVersion.query.all()
    }
    return render_template('add/configuration.html', entities=entities)

@configurations_bp.route('/view/<int:config_id>')
def view(config_id):
    config = ConfigurationInstance.query.get_or_404(config_id)
    return render_template('view/configuration.html', config=config)

@configurations_bp.route('/edit/<int:config_id>', methods=['GET', 'POST'])
def edit(config_id):
    config = ConfigurationInstance.query.get_or_404(config_id)
    if request.method == 'POST':
        try:
            # Mise à jour des paramètres existants
            for param in config.parameters:
                new_value = request.form.get(f'param_{param.id}')
                if new_value != param.value:
                    param.value = new_value
            
            db.session.commit()
            flash("Configuration mise à jour avec succès", "success")
            return redirect(url_for('configurations.view_configuration', config_id=config.id))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour : {str(e)}", "error")
    
    return render_template('edit/configuration.html', config=config)

@configurations_bp.route('/delete/<int:config_id>', methods=['POST'])
def delete(config_id):
    config = ConfigurationInstance.query.get_or_404(config_id)
    try:
        db.session.delete(config)
        db.session.commit()
        flash("Configuration supprimée avec succès", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    return redirect(url_for('configurations.list_configurations'))
