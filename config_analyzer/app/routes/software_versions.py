from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import SoftwareVersion, Software
from app.extensions import db

software_versions_bp = Blueprint('software_versions', __name__, url_prefix='/software-versions')

@software_versions_bp.route('/list')
def list():
    """Liste toutes les versions de logiciels"""
    software_versions = SoftwareVersion.query.all()
    softwares = Software.query.all()
    return render_template('list/partials/software_versions.html', 
                          items=software_versions, 
                          softwares=softwares, 
                          all_versions=True)

@software_versions_bp.route('/software/<string:software_name>')
def list_by_software(software_name):
    """Liste les versions pour un logiciel spécifique"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    software_versions = SoftwareVersion.query.filter_by(software_id=software.id).all()
    return render_template('list/partials/software_versions.html', 
                          software=software, 
                          items=software_versions, 
                          all_versions=False)

@software_versions_bp.route('/view/<string:software_name>/<string:version>')
def view(software_name, version):
    """Affiche une version spécifique de logiciel"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    software_version = SoftwareVersion.query.filter_by(
        software_id=software.id, 
        version=version
    ).first_or_404()
    
    return render_template('view/software_version.html', 
                          software_version=software_version)

@software_versions_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute une nouvelle version de logiciel"""
    if request.method == 'POST':
        software_id = request.form.get('software_id')
        version = request.form.get('version')

        if not software_id or not version:
            flash("Le logiciel et la version sont obligatoires.", "error")
            return redirect(url_for('software_versions.add'))

        # Vérifier si cette version existe déjà pour ce logiciel
        existing = SoftwareVersion.query.filter_by(
            software_id=software_id, 
            version=version
        ).first()
        
        if existing:
            flash("Cette version existe déjà pour ce logiciel.", "error")
            return redirect(url_for('software_versions.add'))

        new_software_version = SoftwareVersion(
            software_id=software_id, 
            version=version
        )
        db.session.add(new_software_version)
        db.session.commit()

        software = Software.query.get(software_id)
        flash("Version de logiciel ajoutée avec succès !", "success")
        return redirect(url_for('software_versions.list_by_software', 
                              software_name=software.name))

    # Récupérer tous les logiciels existants
    softwares = Software.query.all()
    return render_template('add/software_version.html', softwares=softwares)

@software_versions_bp.route('/software/<string:software_name>/add', methods=['GET', 'POST'])
def add_for_software(software_name):
    """Ajoute une version pour un logiciel spécifique"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    
    if request.method == 'POST':
        version = request.form.get('version')

        if not version:
            flash("La version est obligatoire.", "error")
            return redirect(url_for('software_versions.add_for_software', 
                                  software_name=software_name))

        # Vérifier si cette version existe déjà
        existing = SoftwareVersion.query.filter_by(
            software_id=software.id, 
            version=version
        ).first()
        
        if existing:
            flash("Cette version existe déjà pour ce logiciel.", "error")
            return redirect(url_for('software_versions.add_for_software', 
                                  software_name=software_name))

        new_software_version = SoftwareVersion(
            software_id=software.id, 
            version=version
        )
        db.session.add(new_software_version)
        db.session.commit()

        flash("Version de logiciel ajoutée avec succès !", "success")
        return redirect(url_for('software_versions.list_by_software', 
                              software_name=software_name))

    return render_template('add/software_version.html', software=software)

@software_versions_bp.route('/edit/<string:software_name>/<string:version>', methods=['GET', 'POST'])
def edit(software_name, version):
    """Édite une version de logiciel existante"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    software_version = SoftwareVersion.query.filter_by(
        software_id=software.id, 
        version=version
    ).first_or_404()
    
    if request.method == 'POST':
        new_version = request.form['version']

        # Vérifier si la nouvelle version n'existe pas déjà
        if new_version != version:
            existing = SoftwareVersion.query.filter_by(
                software_id=software.id, 
                version=new_version
            ).first()
            
            if existing:
                flash("Cette version existe déjà pour ce logiciel.", "error")
                return redirect(url_for('software_versions.edit', 
                                      software_name=software_name,
                                      version=version))

        software_version.version = new_version
        db.session.commit()
        
        flash("Version de logiciel modifiée avec succès !", "success")
        return redirect(url_for('software_versions.list_by_software', 
                              software_name=software_name))

    return render_template('edit/software_version.html', 
                          software_version=software_version)

@software_versions_bp.route('/delete/<string:software_name>/<string:version>', methods=['GET', 'POST'])
def delete(software_name, version):
    """Supprime une version de logiciel"""
    software = Software.query.filter_by(name=software_name).first_or_404()
    software_version = SoftwareVersion.query.filter_by(
        software_id=software.id, 
        version=version
    ).first_or_404()
    
    if request.method == 'POST':
        db.session.delete(software_version)
        db.session.commit()
        
        flash("Version de logiciel supprimée avec succès !", "success")
        return redirect(url_for('software_versions.list_by_software', 
                              software_name=software_name))
    
    # Pour une requête GET, demander confirmation
    return render_template('delete/software_version.html', 
                          software_version=software_version)
