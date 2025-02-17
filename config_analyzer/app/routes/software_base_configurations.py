from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.models import SoftwareBaseConfigurationFile, SoftwareVersion, Software
from app.extensions import db



software_base_configurations_bp = Blueprint('software_base_configurations', __name__)

@software_base_configurations_bp.route('/software_base_configurations')
def list_all_software_base_configurations():
    base_configurations = SoftwareBaseConfigurationFile.query.all()
    return render_template('list/software_base_configurations.html', base_configurations=base_configurations)

@software_base_configurations_bp.route('/software_base_configurations/<software_name>')
def list_software_base_configurations_by_software(software_name):
    software = Software.query.filter_by(name=software_name).first_or_404()
    base_configurations = SoftwareBaseConfigurationFile.query.join(SoftwareVersion).filter(SoftwareVersion.software_id == software.id).all()
    return render_template('list/software_base_configurations.html', base_configurations=base_configurations, software=software)

@software_base_configurations_bp.route('/software_base_configurations/<software_name>/<software_version>')
def list_software_base_configurations_by_version(software_name, software_version):
    software = Software.query.filter_by(name=software_name).first_or_404()
    version = SoftwareVersion.query.filter_by(software_id=software.id, version=software_version).first_or_404()
    base_configurations = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=version.id).all()
    return render_template('list/software_base_configurations.html', base_configurations=base_configurations, software_version=version)

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
        return redirect(url_for('software_base_configurations.list_software_base_configurations_by_version', software_name=new_base_configuration.software_version.software.name, software_version=new_base_configuration.software_version.version))

    return render_template('add/software_base_configuration.html', software_version_id=software_version_id)

@software_base_configurations_bp.route('/software_base_configurations/add', methods=['GET', 'POST'])
def add_generic_software_base_configuration():
    softwares = Software.query.all()
    if request.method == 'POST':
        software_id = request.form.get('software')
        software_version_id = request.form.get('software_version')
        file_name = request.form.get('file_name')
        path = request.form.get('path')
        content = request.form.get('content')

        if not software_id or not software_version_id or not file_name or not path or not content:
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('software_base_configurations.add_generic_software_base_configuration'))

        new_base_configuration = SoftwareBaseConfigurationFile(software_version_id=software_version_id, file_name=file_name, path=path, content=content)
        db.session.add(new_base_configuration)
        db.session.commit()

        flash("Configuration de base ajoutée avec succès !", "success")
        return redirect(url_for('software_base_configurations.list_all_software_base_configurations'))

    return render_template('add/software_base_configuration.html', softwares=softwares, software_version_id=None)

@software_base_configurations_bp.route('/get_software_versions/<int:software_id>')
def get_software_versions(software_id):
    software_versions = SoftwareVersion.query.filter_by(software_id=software_id).all()
    return jsonify({'software_versions': [{'id': version.id, 'version': version.version} for version in software_versions]})


@software_base_configurations_bp.route('/software_base_configurations/edit/<software_name>/<software_version>/<file_name>', methods=['GET', 'POST'])
def edit_software_base_configuration(software_name, software_version, file_name):
    software = Software.query.filter_by(name=software_name).first_or_404()
    version = SoftwareVersion.query.filter_by(software_id=software.id, version=software_version).first_or_404()
    base_configuration = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=version.id, file_name=file_name).first_or_404()

    if request.method == 'POST':
        base_configuration.file_name = request.form['file_name']
        base_configuration.path = request.form['path']
        base_configuration.content = request.form['content']

        db.session.commit()
        flash("Configuration de base modifiée avec succès !", "success")
        return redirect(url_for('software_base_configurations.view_software_base_configuration', software_name=software_name, software_version=software_version, file_name=base_configuration.file_name))

    return render_template('edit/software_base_configuration.html', base_configuration=base_configuration)

@software_base_configurations_bp.route('/software_base_configurations/delete/<int:base_configuration_id>', methods=['GET'])
def delete_software_base_configuration(base_configuration_id):
    base_configuration = SoftwareBaseConfigurationFile.query.get_or_404(base_configuration_id)
    software_version_id = base_configuration.software_version_id
    db.session.delete(base_configuration)
    db.session.commit()
    flash("Configuration de base supprimée avec succès !", "success")
    return redirect(url_for('software_base_configurations.list_software_base_configurations_by_version', software_name=base_configuration.software_version.software.name, software_version=base_configuration.software_version.version))

@software_base_configurations_bp.route('/software_base_configuration/<software_name>/<software_version>/<file_name>')
def view_software_base_configuration(software_name, software_version, file_name):
    software = Software.query.filter_by(name=software_name).first_or_404()
    version = SoftwareVersion.query.filter_by(software_id=software.id, version=software_version).first_or_404()
    base_configuration = SoftwareBaseConfigurationFile.query.filter_by(software_version_id=version.id, file_name=file_name).first_or_404()
    return render_template('view/software_base_configuration.html', base_configuration=base_configuration)

