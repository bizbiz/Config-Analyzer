from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software
from app.extensions import db

software_base_configurations_bp = Blueprint('software_base_configurations', __name__)

@software_base_configurations_bp.route('/software_base_configurations/<int:software_version_id>')
def list_software_base_configurations(software_version_id):
    software_version = SoftwareVersion.query.get_or_404(software_version_id)
    base_configurations = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=software_version_id).all()
    return render_template('software_base_configurations.html', software_version=software_version, base_configurations=base_configurations)

@software_base_configurations_bp.route('/software_base_configurations/add', methods=['POST'])
def add_software_base_configuration():
    software_version_id = request.form.get('software_version_id')
    file_name = request.form.get('file_name')
    content = request.form.get('content')

    if not software_version_id or not file_name or not content:
        flash("La version du logiciel, le nom du fichier et le contenu sont obligatoires.", "error")
        return redirect(url_for('software_base_configurations.list_software_base_configurations', software_version_id=software_version_id))

    new_base_configuration = SoftwareBaseConfigurationFile(software_version_id=software_version_id, file_name=file_name, content=content)
    db.session.add(new_base_configuration)
    db.session.commit()

    flash("Configuration de base ajoutée avec succès !", "success")
    return redirect(url_for('software_base_configurations.list_software_base_configurations', software_version_id=software_version_id))

@software_base_configurations_bp.route('/software_base_configurations/edit/<int:base_configuration_id>', methods=['GET', 'POST'])
def edit_software_base_configuration(base_configuration_id):
    base_configuration = SoftwareBaseConfigurationFile.query.get_or_404(base_configuration_id)
    software_version_id = base_configuration.software_version_id
    if request.method == 'POST':
        base_configuration.file_name = request.form['file_name']
        base_configuration.content = request.form['content']

        db.session.commit()
        flash("Configuration de base modifiée avec succès !", "success")
        return redirect(url_for('software_base_configurations.list_software_base_configurations', software_version_id=software_version_id))

    return render_template('edit_software_base_configuration.html', base_configuration=base_configuration)

@software_base_configurations_bp.route('/software_base_configurations/delete/<int:base_configuration_id>', methods=['GET'])
def delete_software_base_configuration(base_configuration_id):
    base_configuration = SoftwareBaseConfigurationFile.query.get_or_404(base_configuration_id)
    software_version_id = base_configuration.software_version_id
    db.session.delete(base_configuration)
    db.session.commit()
    flash("Configuration de base supprimée avec succès !", "success")
    return redirect(url_for('software_base_configurations.list_software_base_configurations', software_version_id=software_version_id))