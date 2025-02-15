from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import SoftwareVersion, Software
from app.extensions import db

software_versions_bp = Blueprint('software_versions', __name__)

@software_versions_bp.route('/software_versions')
def list_all_software_versions():
    software_versions = SoftwareVersion.query.all()
    return render_template('list/software_versions.html', software_versions=software_versions, all_versions=True)

@software_versions_bp.route('/software_versions/<int:software_id>')
def list_software_versions(software_id):
    software = Software.query.get_or_404(software_id)
    software_versions = SoftwareVersion.query.filter_by(software_id=software_id).all()
    return render_template('list/software_versions.html', software=software, software_versions=software_versions, all_versions=False)

@software_versions_bp.route('/software_versions/add', methods=['GET', 'POST'])
def add_software_version():
    if request.method == 'POST':
        software_id = request.form.get('software_id')
        version = request.form.get('version')

        if not software_id or not version:
            flash("Le logiciel et la version sont obligatoires.", "error")
            return redirect(url_for('software_versions.add_software_version'))

        new_software_version = SoftwareVersion(software_id=software_id, version=version)
        db.session.add(new_software_version)
        db.session.commit()

        flash("Version de logiciel ajoutée avec succès !", "success")
        return redirect(url_for('software_versions.list_software_versions', software_id=software_id))

    # Récupérer tous les logiciels existants
    softwares = Software.query.all()
    return render_template('add/software_version.html', softwares=softwares)

@software_versions_bp.route('/software_versions/edit/<int:software_version_id>', methods=['GET', 'POST'])
def edit_software_version(software_version_id):
    software_version = SoftwareVersion.query.get_or_404(software_version_id)
    if request.method == 'POST':
        software_version.version = request.form['version']

        db.session.commit()
        flash("Version de logiciel modifiée avec succès !", "success")
        return redirect(url_for('software_versions.list_software_versions', software_id=software_version.software_id))

    return render_template('edit/software_version.html', software_version=software_version)

@software_versions_bp.route('/software_versions/delete/<int:software_version_id>', methods=['GET'])
def delete_software_version(software_version_id):
    software_version = SoftwareVersion.query.get_or_404(software_version_id)
    software_id = software_version.software_id
    db.session.delete(software_version)
    db.session.commit()
    flash("Version de logiciel supprimée avec succès !", "success")
    return redirect(url_for('software_versions.list_software_versions', software_id=software_id))