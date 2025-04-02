# app/utils/validators.py
"""
Utilitaires pour la validation des formulaires.
"""
import re
from flask import flash, render_template
from app.models.basic.postal_code import PostalCode
from app.extensions import db

def validate_client_form(name, postal_code, city, country_code, countries, template_name, form_data=None, **kwargs):
    """
    Valide les données d'un formulaire client.
    
    Args:
        name (str): Nom du client
        postal_code (str): Code postal
        city (str): Ville
        country_code (str): Code pays
        countries (list): Liste des pays pour le rendu du template
        template_name (str): Nom du template à rendre en cas d'erreur
        form_data (dict, optional): Données du formulaire
        **kwargs: Arguments supplémentaires pour le rendu du template
    
    Returns:
        tuple: (bool, response) - (True, None) si validation réussie, 
                                  (False, template) si validation échouée
    """
    if form_data is None:
        form_data = {
            'name': name,
            'postal_code': postal_code,
            'city': city,
            'country_code': country_code
        }
    
    # Validation du nom
    if not name:
        flash("Le nom est obligatoire.", "error")
        return False, render_template(
            template_name, 
            form_data=form_data, 
            countries=countries,
            name_error="Le nom est obligatoire.",
            **kwargs
        )

    # Validation du code postal
    if not re.match(r'^\d{5}$', postal_code):
        postal_code_error = "Le code postal doit contenir exactement 5 chiffres."
        return False, render_template(
            template_name, 
            form_data=form_data, 
            countries=countries,
            postal_code_error=postal_code_error,
            **kwargs
        )
    
    # Validation du code pays
    if not re.match(r'^[A-Z]{3}$', country_code):
        country_code_error = "Veuillez sélectionner un pays valide."
        return False, render_template(
            template_name, 
            form_data=form_data, 
            countries=countries,
            country_code_error=country_code_error,
            **kwargs
        )
    
    return True, None

def get_or_create_postal_code(code, city, country_code):
    """
    Récupère un code postal existant ou en crée un nouveau.
    
    Args:
        code (str): Code postal
        city (str): Ville
        country_code (str): Code pays
    
    Returns:
        PostalCode: Instance de code postal
    """
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
        db.session.flush()  # Pour obtenir l'ID du code postal
    
    return postal_code