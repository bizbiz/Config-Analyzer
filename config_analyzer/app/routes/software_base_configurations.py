from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software
from app.extensions import db

software_base_configurations_bp = Blueprint('software_base_configurations', __name__)

@software_base_configurations_bp.route('/software_base_configurations/<int:software_version_id>')
def list_software_base_configurations(software_version_id):
    software_version = SoftwareVersion.query.get_or_404(software_version_id)
    base_configurations = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=software_version_id).all()
    return render_template('software_base_configurations.html', software_version=software_version, base_configurations=base_configurations)

@software_base_configurations_bp.route('/software_base_configurations/add/<int:software_version_id>', methods=['GET', 'POST'])
def add_software_base_configuration(software_version_id):
    if request.method == 'POST':
        file_name = request.form.get('file_name')
        path = request.form.get('path')
        content = request.form.get('content')

        if not file_name or not path or not content:
            flash("Le nom du fichier, le chemin et le contenu sont obligatoires.", "error")
            return redirect(url_for('software_base_configurations.add_software_base_configuration', software_version_id=software_version_id))

        existing_configuration = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=software_version_id, file_name=file_name).first()
        if existing_configuration:
            flash("Une configuration de base avec ce nom de fichier existe déjà pour cette version de logiciel.", "error")
            return redirect(url_for('software_base_configurations.add_software_base_configuration', software_version_id=software_version_id))

        new_base_configuration = SoftwareBaseConfigurationFile(software_version_id=software_version_id, file_name=file_name, path=path, content=content)
        db.session.add(new_base_configuration)
        db.session.commit()

        flash("Configuration de base ajoutée avec succès !", "success")
        return redirect(url_for('software_base_configurations.list_software_base_configurations', software_version_id=software_version_id))

    return render_template('add_software_base_configuration.html', software_version_id=software_version_id)

@software_base_configurations_bp.route('/software_base_configurations/edit/<int:base_configuration_id>', methods=['GET', 'POST'])
def edit_software_base_configuration(base_configuration_id):
    base_configuration = SoftwareBaseConfigurationFile.query.get_or_404(base_configuration_id)
    software_version_id = base_configuration.software_version_id
    if request.method == 'POST':
        base_configuration.file_name = request.form['file_name']
        base_configuration.path = request.form['path']
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

@software_base_configurations_bp.route('/software_base_configuration/<int:base_configuration_id>')
def view_software_base_configuration(base_configuration_id):
    base_configuration = SoftwareBaseConfigurationFile.query.get_or_404(base_configuration_id)
    return render_template('view_software_base_configuration.html', base_configuration=base_configuration)