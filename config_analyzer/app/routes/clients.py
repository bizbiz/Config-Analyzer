# app/routes/clients.py
"""
Routes pour la gestion des clients.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.client import Client
from app.models.basic.postal_code import PostalCode
from app.models.entities.robot_instance import RobotInstance
from app.models.entities.software import Software
from app.models.configuration import ConfigurationInstance
from app.models.parameters.definitions import ParameterDefinition
from app.models.parameters.values import ParameterValue
from app.models.enums import EntityType
from app.extensions import db
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import ARRAY
from app.utils.param_helpers import get_applicable_params_configs, get_unconfigured_params
from app.utils.countries import get_countries_list
from app.utils.validators import validate_client_form, get_or_create_postal_code

# Définition du blueprint avec un préfixe explicite
clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/view/<string:slug>')
def view(slug):
    """Affiche les détails d'un client."""
    client = Client.query.filter_by(slug=slug).options(
        joinedload(Client.postal_code_relation)
    ).first_or_404()

    # Le reste du code reste inchangé
    applicable_configs = ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == EntityType.CLIENT
    ).all()
    
    configured_params = ParameterValue.query.filter(
        ParameterValue.entity_id == client.id,
        ParameterValue.entity_type == EntityType.CLIENT
    ).all()
    
    unconfigured_params = [c for c in applicable_configs if c.id not in [p.parameter_definition_id for p in configured_params]]
    
    return render_template(
        'view/client.html',
        client=client,
        robots=client.robots.all(),
        configurations=client.configurations,
        configured_params=configured_params,
        unconfigured_params=unconfigured_params
    )


@clients_bp.route('/list')
def list():
    """Liste tous les clients."""
    # Charger explicitement la relation postal_code
    clients = Client.query.options(
        db.joinedload(Client.postal_code_relation)
    ).all()
    
    # Calcul des statistiques
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Date du début du mois courant
    current_month_start = datetime(datetime.now().year, datetime.now().month, 1)
    
    # Nouveaux clients ce mois-ci
    new_clients = Client.query.filter(Client.created_at >= current_month_start).count()
    
    # Total des robots pour tous les clients
    total_robots = db.session.query(func.count(RobotInstance.id)).scalar()
    
    # Vérifier si tous les clients ont le même code pays
    same_country = True
    country_code = None
    
    if clients:
        country_code = clients[0].postal_code_relation.country_code if clients[0].postal_code_relation else None
        for client in clients:
            if not client.postal_code_relation or client.postal_code_relation.country_code != country_code:
                same_country = False
                break
    
    # Obtenir la liste des pays pour le formulaire d'ajout rapide
    countries = get_countries_list()

    # Récupérer les définitions de paramètres globaux pour les clients
    params_configs = ParameterDefinition.query.filter(
        ParameterDefinition.target_entity == EntityType.CLIENT
    ).all()

    return render_template(
        'list/clients.html', 
        params_configs=params_configs,
        clients=clients,
        countries=countries,
        name_error=None,
        postal_code_error=None,
        city_error=None,
        country_code_error=None,
        form_data={},
        # Colonnes pour le tableau - envoyées directement
        columns=['name', 'postal_code_relation.code', 'postal_code_relation.city', 'robots'],
        headers=['Nom', 'Code Postal', 'Ville', 'Robots', 'Actions'],
        # Statistiques
        new_clients=new_clients,
        total_robots=total_robots,
        # Info pays
        same_country=same_country,
        country_code=country_code
    )

@clients_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute un nouveau client."""
    # Obtenir la liste des pays
    countries = get_countries_list()
    
    if request.method == 'POST':
        name = request.form.get('name')
        postal_code_value = request.form.get('postal_code')
        city = request.form.get('city')
        country_code = request.form.get('country_code')

        form_data = {
            'name': name,
            'postal_code': postal_code_value,
            'city': city,
            'country_code': country_code
        }

        # Validation du formulaire
        is_valid, response = validate_client_form(
            name, postal_code_value, city, country_code, 
            countries, 'add/client.html', form_data
        )
        if not is_valid:
            return response

        # Récupérer ou créer le code postal
        postal_code = get_or_create_postal_code(postal_code_value, city, country_code)
            
        # Créer le nouveau client avec la relation
        new_client = Client(name=name, postal_code_id=postal_code.id)
        
        db.session.add(new_client)
        db.session.commit()

        flash("Client ajouté avec succès !", "success")
        return redirect(url_for('clients.list'))

    return render_template('add/client.html', countries=countries)

@clients_bp.route('/edit/<slug>', methods=['GET', 'POST'])
def edit(slug):
    """Modifie un client existant."""
    client = Client.query.filter_by(slug=slug).first_or_404()
    
    # Obtenir la liste des pays
    countries = get_countries_list()
    
    # Récupérer les configurations existantes pour la vue
    applicable_configs = get_applicable_params_configs('client', client.id)
    unconfigured_params = get_unconfigured_params(client.id, applicable_configs)
    configured_params = [p for p in applicable_configs if p not in unconfigured_params]
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('postal_code')
        city = request.form.get('city')
        country_code = request.form.get('country_code')
        
        form_data = {
            'name': name,
            'postal_code': code,
            'city': city,
            'country_code': country_code
        }
        
        # Validation du formulaire client
        is_valid, response = validate_client_form(
            name, code, city, country_code, 
            countries, 'edit/client.html', form_data,
            client=client,
            configured_params=configured_params,
            unconfigured_params=unconfigured_params
        )
        if not is_valid:
            return response
        
        # Mettre à jour le nom du client
        client.name = name
        
        # Récupérer ou créer le code postal
        postal_code = get_or_create_postal_code(code, city, country_code)
        
        # Mettre à jour la relation
        client.postal_code_relation = postal_code

        # Traiter les paramètres supplémentaires
        for key, value in request.form.items():
            if key.startswith('param_'):
                param_id = int(key.split('_')[1])
                config = AdditionalParametersConfig.query.get(param_id)
                value = value.strip()

                active_param = next((p for p in config.additional_parameters if p.is_active), None)

                if active_param:
                    if active_param.value == value:
                        continue
                    active_param.is_active = False

                if value:
                    new_param = AdditionalParameter(
                        additional_parameters_config_id=param_id,
                        value=value,
                        is_active=True,
                        notes=request.form.get(f'notes_{param_id}', None)
                    )
                    db.session.add(new_param)
        
        db.session.commit()
        flash("Modifications enregistrées avec succès !", "success")
        return redirect(url_for('clients.view', slug=client.slug))

    # Récupérer les infos du code postal actuel
    postal_code = client.postal_code_relation
    
    # Préparer les données du formulaire
    form_data = {
        'name': client.name,
        'postal_code': postal_code.code if postal_code else '',
        'city': postal_code.city if postal_code else '',
        'country_code': postal_code.country_code if postal_code else 'FRA'
    }

    return render_template('edit/client.html', 
                          client=client,
                          form_data=form_data,
                          countries=countries,
                          configured_params=configured_params,
                          unconfigured_params=unconfigured_params)


@clients_bp.route('/delete/<slug>', methods=['POST'])
def delete(slug):
    """Supprime un client en utilisant son slug."""
    client = Client.query.filter_by(slug=slug).first_or_404()
    
    try:
        db.session.delete(client)
        db.session.commit()
        flash("Client supprimé avec succès !", "success")
    except Exception as e:
        db.session.rollback()
        # Si le client a des relations qui empêchent la suppression
        flash(f"Impossible de supprimer ce client : {str(e)}", "error")
    
    return redirect(url_for('clients.list'))