from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software
from app.extensions import db

# Utiliser un préfixe d'URL explicite
software_base_configurations_bp = Blueprint('software_base_configurations', __name__, url_prefix='/software-base-configs')

@software_base_configurations_bp.route('/list')
def list():
    """Liste toutes les configurations de base"""
    base_configurations = SoftwareBaseConfigurationFile.query.all()
    return render_template('list/partials/software_base_configurations.html', items=base_configurations)

@software_base_configurations_bp.route('/software/<string:software_name>')
def list_by_software(software_name):
    """Liste les configurations de base pour un logiciel spécifique"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    base_configurations = SoftwareBaseConfigurationFile.query.join(SoftwareVersion).filter(
        SoftwareVersion.software_id == software.id
    ).all()
    return render_template('list/partials/software_base_configurations.html', 
                          items=base_configurations, 
                          software=software)

@software_base_configurations_bp.route('/software/<string:software_name>/version/<string:version>')
def list_by_version(software_name, version):
    """Liste les configurations de base pour une version spécifique de logiciel"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    version_obj = SoftwareVersion.query.filter_by(software_id=software.id, version=version).first_or_404()
    base_configurations = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=version_obj.id).all()
    return render_template('list/partials/software_base_configurations.html', 
                          items=base_configurations, 
                          software_version=version_obj)

@software_base_configurations_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute une nouvelle configuration de base (choix du logiciel/version)"""
    softwares = Software.query.all()
    if request.method == 'POST':
        software_id = request.form.get('software')
        software_version_id = request.form.get('software_version')
        file_name = request.form.get('file_name')
        path = request.form.get('path')
        content = request.form.get('content')

        if not all([software_id, software_version_id, file_name, path, content]):
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('software_base_configurations.add'))

        # Vérifier si la configuration existe déjà
        existing = SoftwareBaseConfigurationFile.query.filter_by(
            software_version_id=software_version_id, 
            file_name=file_name
        ).first()
        
        if existing:
            flash("Une configuration avec ce nom existe déjà pour cette version.", "error")
            return redirect(url_for('software_base_configurations.add'))

        # Créer la nouvelle configuration
        new_config = SoftwareBaseConfigurationFile(
            software_version_id=software_version_id, 
            file_name=file_name, 
            path=path, 
            content=content
        )
        db.session.add(new_config)
        db.session.commit()

        flash("Configuration de base ajoutée avec succès !", "success")
        
        # Rediriger vers la liste des configurations pour cette version
        version = SoftwareVersion.query.get(software_version_id)
        return redirect(url_for('software_base_configurations.list_by_version', 
                              software_name=version.software.name, 
                              version=version.version))

    return render_template('add/software_base_configuration.html', 
                          softwares=softwares, 
                          software_version_id=None)

@software_base_configurations_bp.route('/add/version/<int:version_id>', methods=['GET', 'POST'])
def add_for_version(version_id):
    """Ajoute une configuration pour une version spécifique"""
    version = SoftwareVersion.query.get_or_404(version_id)
    
    if request.method == 'POST':
        file_name = request.form.get('file_name')
        path = request.form.get('path')
        content = request.form.get('content')

        if not all([file_name, path, content]):
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('software_base_configurations.add_for_version', version_id=version_id))

        # Vérifier si la configuration existe déjà
        existing = SoftwareBaseConfigurationFile.query.filter_by(
            software_version_id=version_id, 
            file_name=file_name
        ).first()
        
        if existing:
            flash("Une configuration avec ce nom existe déjà pour cette version.", "error")
            return redirect(url_for('software_base_configurations.add_for_version', version_id=version_id))

        # Créer la nouvelle configuration
        new_config = SoftwareBaseConfigurationFile(
            software_version_id=version_id, 
            file_name=file_name, 
            path=path, 
            content=content
        )
        db.session.add(new_config)
        db.session.commit()

        flash("Configuration de base ajoutée avec succès !", "success")
        return redirect(url_for('software_base_configurations.list_by_version', 
                              software_name=version.software.name, 
                              version=version.version))

    return render_template('add/software_base_configuration.html', 
                          software_version=version,
                          software_version_id=version_id)

@software_base_configurations_bp.route('/view/<string:software_name>/<string:version>/<string:file_name>')
def view(software_name, version, file_name):
    """Affiche une configuration de base spécifique"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    version_obj = SoftwareVersion.query.filter_by(software_id=software.id, version=version).first_or_404()
    config = SoftwareBaseConfigurationFile.query.filter_by(
        software_version_id=version_obj.id, 
        file_name=file_name
    ).first_or_404()
    
    return render_template('view/software_base_configuration.html', 
                          base_configuration=config)

@software_base_configurations_bp.route('/delete/<string:software_name>/<string:version>/<string:file_name>', methods=['GET', 'POST'])
def delete(software_name, version, file_name):
    """Supprime une configuration de base"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    version_obj = SoftwareVersion.query.filter_by(software_id=software.id, version=version).first_or_404()
    config = SoftwareBaseConfigurationFile.query.filter_by(
        software_version_id=version_obj.id, 
        file_name=file_name
    ).first_or_404()
    
    if request.method == 'POST':
        db.session.delete(config)
        db.session.commit()
        flash("Configuration de base supprimée avec succès !", "success")
        return redirect(url_for('software_base_configurations.list_by_version', 
                              software_name=software_name, 
                              version=version))
    
    # Pour une requête GET, afficher une page de confirmation
    return render_template('delete/software_base_configuration.html', 
                          base_configuration=config)

@software_base_configurations_bp.route('/api/software-versions/<int:software_id>')
def get_software_versions(software_id):
    """API pour récupérer les versions d'un logiciel (utilisé par JavaScript)"""
    software_versions = SoftwareVersion.query.filter_by(software_id=software_id).all()
    return jsonify({
        'software_versions': [
            {'id': version.id, 'version': version.version} 
            for version in software_versions
        ]
    })
