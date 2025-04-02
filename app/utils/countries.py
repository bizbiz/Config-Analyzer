# app/utils/countries.py
"""
Utilitaire pour la gestion des pays avec codes ISO 3166-1 alpha-3.
"""

def get_countries_list(sort=True):
    """
    Retourne la liste des pays avec la France en premier.
    
    Args:
        sort (bool): Si True, les pays autres que la France sont triés par ordre alphabétique.
    
    Returns:
        list: Liste de dictionnaires contenant le code (3 lettres) et le nom des pays.
    """
    # Liste des pays avec la France en premier
    countries = [
        {"code": "FRA", "name": "France"},
        {"code": "DEU", "name": "Allemagne"},
        {"code": "BEL", "name": "Belgique"},
        {"code": "CHE", "name": "Suisse"},
        {"code": "ESP", "name": "Espagne"},
        {"code": "GBR", "name": "Royaume-Uni"},
        {"code": "ITA", "name": "Italie"},
        {"code": "LUX", "name": "Luxembourg"},
        {"code": "NLD", "name": "Pays-Bas"},
        {"code": "PRT", "name": "Portugal"},
        {"code": "USA", "name": "États-Unis"},
        {"code": "CAN", "name": "Canada"},
        {"code": "AUS", "name": "Australie"},
        {"code": "JPN", "name": "Japon"},
        {"code": "CHN", "name": "Chine"},
        {"code": "IND", "name": "Inde"},
        {"code": "BRA", "name": "Brésil"},
        {"code": "RUS", "name": "Russie"},
        {"code": "ZAF", "name": "Afrique du Sud"},
        # Vous pouvez compléter cette liste selon vos besoins
    ]
    
    if sort:
        # Trier par nom, en gardant la France au début
        countries_sorted = sorted(countries[1:], key=lambda x: x["name"])
        countries = [countries[0]] + countries_sorted
    
    return countries

def get_country_by_code(code):
    """
    Retrouve un pays par son code ISO 3166-1 alpha-3.
    
    Args:
        code (str): Code ISO 3166-1 alpha-3 du pays à retrouver.
    
    Returns:
        dict or None: Dictionnaire contenant le code et le nom du pays, ou None si non trouvé.
    """
    countries = get_countries_list(sort=False)
    for country in countries:
        if country["code"] == code:
            return country
    return None

def convert_alpha2_to_alpha3(alpha2_code):
    """
    Convertit un code ISO 3166-1 alpha-2 en code alpha-3.
    Utile pour la migration des données existantes.
    
    Args:
        alpha2_code (str): Code ISO 3166-1 alpha-2 (2 lettres).
    
    Returns:
        str or None: Code ISO 3166-1 alpha-3 correspondant, ou None si non trouvé.
    """
    # Correspondance entre codes alpha-2 et alpha-3
    conversion_map = {
        "FR": "FRA",
        "DE": "DEU",
        "BE": "BEL",
        "CH": "CHE",
        "ES": "ESP",
        "GB": "GBR",
        "IT": "ITA",
        "LU": "LUX",
        "NL": "NLD",
        "PT": "PRT",
        "US": "USA",
        "CA": "CAN",
        "AU": "AUS",
        "JP": "JPN",
        "CN": "CHN",
        "IN": "IND",
        "BR": "BRA",
        "RU": "RUS",
        "ZA": "ZAF",
        # Complétez cette liste selon vos besoins
    }
    
    return conversion_map.get(alpha2_code)