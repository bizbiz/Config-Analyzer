from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Client, PostalCode, RobotClient, Software, ClientConfigurationFile, AdditionalParametersConfig, EntityType
from app.extensions import db
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import ARRAY
from app.utils.param_helpers import get_applicable_params_configs, get_unconfigured_params
import re

# app/routes/clients.py

# Définition du blueprint avec un préfixe explicite
clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/view/<string:slug>')
def view(slug):
    client = Client.query.filter_by(slug=slug).first_or_404()
    
    # Données associées
    robots = RobotClient.query.filter_by(client_id=client.id).all()
    configurations = ClientConfigurationFile.query.filter_by(client_id=client.id).all()
    
    # Configurations de paramètres
    applicable_configs = get_applicable_params_configs('client', client.id)
    unconfigured_params = get_unconfigured_params(client.id, applicable_configs)
    configured_params = [c for c in applicable_configs if c not in unconfigured_params]
    
    return render_template(
        'view/client.html',
        client=client,
        robots=robots,
        configurations=configurations,
        applicable_configs=applicable_configs,
        unconfigured_params=unconfigured_params,
        configured_params=configured_params
    )

@clients_bp.route('/list')
def list():
    clients = Client.query.all()
    form_data = {}
    name_error = postal_code_error = city_error = country_code_error = None

    params_configs = AdditionalParametersConfig.query.filter(
        or_(
            (AdditionalParametersConfig.target_entity == EntityType.CLIENT) &
            (AdditionalParametersConfig.applicable_ids == []),
            
            (AdditionalParametersConfig.target_entity.is_(None)) &
            (AdditionalParametersConfig.applicable_ids == [])
        )
    ).all()

    # Sérialiser les configurations pour JavaScript
    configs_json = [{
        'configuration_values': config.configuration_values,
        'type': config.type.value
    } for config in params_configs]

    return render_template(
        'list/clients.html', 
        params_configs=params_configs,
        configs_json=configs_json,  # Nouveau paramètre
        clients=clients,
        entity_type='client',
        entity_slug='global',
        form_data=form_data,
        name_error=name_error,
        postal_code_error=postal_code_error,
        city_error=city_error,
        country_code_error=country_code_error
    )

@clients_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute un nouveau client."""
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

        # Validation du nom
        if not name:
            flash("Le nom est obligatoire.", "error")
            return render_template('add/client.html', form_data=form_data, name_error="Le nom est obligatoire.")

        # Validation du code postal
        if not re.match(r'^\d{5}$', postal_code_value):
            postal_code_error = "Le code postal doit contenir exactement 5 chiffres."
            return render_template('add/client.html', 
                                 form_data=form_data, 
                                 postal_code_error=postal_code_error)
        
        # Validation du code pays
        if not re.match(r'^[A-Z]{2}$', country_code):
            country_code_error = "Le code pays doit être composé de 2 lettres majuscules."
            return render_template('add/client.html', 
                                 form_data=form_data, 
                                 country_code_error=country_code_error)

        # Chercher si ce code postal existe déjà
        postal_code = PostalCode.query.filter_by(
            code=postal_code_value, 
            city=city, 
            country_code=country_code
        ).first()
        
        # S'il n'existe pas, créer un nouveau code postal
        if not postal_code:
            postal_code = PostalCode(
                code=postal_code_value,
                city=city,
                country_code=country_code
            )
            db.session.add(postal_code)
            db.session.flush()  # Pour obtenir l'ID du code postal
            
        # Créer le nouveau client avec la relation
        new_client = Client(name=name, postal_code_id=postal_code.id)
        
        db.session.add(new_client)
        db.session.commit()

        flash("Client ajouté avec succès !", "success")
        return redirect(url_for('clients.list'))

    return render_template('add/client.html')

@clients_bp.route('/edit/<slug>', methods=['GET', 'POST'])
def edit(slug):
    """Modifie un client existant."""
    client = Client.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        # Mettre à jour le nom du client
        client.name = request.form['name']
        
        # Vérifier si les informations postales ont changé
        code = request.form['postal_code']
        city = request.form['city']
        country_code = request.form['country_code']
        
        # Chercher si ce code postal existe déjà
        postal_code = PostalCode.query.filter_by(
            code=code, 
            city=city, 
            country_code=country_code
        ).first()
        
        # S'il n'existe pas, créer un nouveau code postal
        if not postal_code:
            postal_code = PostalCode(
                code=code,
                city=city,
                country_code=country_code
            )
            db.session.add(postal_code)
            
        # Associer le code postal au client
        client.postal_code_relation = postal_code

        # Mise à jour des paramètres additionnels
        for param_id, value in request.form.items():
            if param_id.startswith('param_'):
                param_id = int(param_id.split('_')[1])
                param = AdditionalParameter.query.get(param_id)
                if param:
                    param.value = value

        # Regénérer le slug après les modifications
        client.generate_slug()
        
        db.session.commit()
        flash("Client et paramètres modifiés avec succès !", "success")
        return redirect(url_for('clients.view', slug=client.slug))

    # Récupération des paramètres pour l'affichage
    applicable_configs = get_applicable_params_configs('client', client.id)
    unconfigured_params = get_unconfigured_params(client.id, applicable_configs)
    configured_params = [p for p in applicable_configs if p not in unconfigured_params]
    
    return render_template('edit/client.html', 
                           client=client, 
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

