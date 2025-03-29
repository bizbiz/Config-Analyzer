# app/utils/slug_helpers.py

import re
import unicodedata
from sqlalchemy import inspect

def slugify(text, max_length=None):
    """
    Convertit un texte en slug URL-friendly.
    
    Args:
        text: Le texte à convertir
        max_length: Longueur maximale du slug (optionnel)
    
    Returns:
        str: Un slug
    """
    if not text:
        return ""
    
    # Normaliser le texte (enlever les accents)
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    # Convertir en minuscules et supprimer les caractères non autorisés
    text = re.sub(r'[^\w\s-]', '', text.lower())
    # Remplacer les espaces et caractères de séparation par un tiret
    text = re.sub(r'[-\s]+', '-', text).strip('-_')
    
    # Tronquer si une longueur maximale est spécifiée
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text

def generate_model_slug(base_text, model_class, custom_value=None, max_length=25):
    """
    Génère un slug unique pour n'importe quel modèle, en respectant strictement max_length.
    Permet également d'essayer un slug personnalisé avec une valeur supplémentaire avant d'ajouter un compteur.
    
    Args:
        base_text: Le texte à convertir en slug (username, name, etc.)
        model_class: La classe du modèle (User, UserGroup, etc.)
        custom_value: Valeur supplémentaire à utiliser pour le slug (optionnel)
        max_length: Longueur maximale du slug
    
    Returns:
        str: Un slug unique de longueur <= max_length
    """
    # Réserver de l'espace pour le suffixe potentiel "-999"
    suffix_length = 4  
    safe_length = max_length - suffix_length
    
    # Générer le slug de base avec une longueur réduite pour accommoder un éventuel suffixe
    base_slug = slugify(base_text, safe_length)
    slug = base_slug
    
    # Création de la requête pour vérifier si le slug existe déjà
    query = model_class.query.filter(model_class.slug == slug)
    
    # Vérifier si le slug existe déjà
    if query.first():
        # Si une valeur personnalisée est fournie, essayer un slug avec cette valeur
        if custom_value:
            # Calculer l'espace disponible pour chaque partie du slug composé
            combined_safe_length = max_length - suffix_length - 1  # -1 pour le tiret de séparation
            part1_length = int(combined_safe_length * 0.7)  # 70% pour le texte principal
            part2_length = combined_safe_length - part1_length  # Le reste pour la valeur personnalisée
            
            # Générer le slug composé
            custom_slug = f"{slugify(base_text, part1_length)}-{slugify(custom_value, part2_length)}"
            
            # Vérifier si ce slug composé existe déjà
            custom_query = model_class.query.filter(model_class.slug == custom_slug)
            
            if not custom_query.first():
                return custom_slug
    
        # Si le slug existe ou si le slug composé existe aussi, ajouter un compteur
        counter = 1
        while query.first():
            # Si le compteur atteint 1000, réduire davantage la base pour un suffixe plus long
            if counter == 1000:
                suffix_length += 1
                base_slug = slugify(base_text, max_length - suffix_length)
            
            slug = f"{base_slug}-{counter}"
            counter += 1
            query = model_class.query.filter(model_class.slug == slug)
    
    return slug