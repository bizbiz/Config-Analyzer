# app/routes/software_version.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.software import Software
from app.models.entities.software_version import SoftwareVersion
from app.extensions import db
from sqlalchemy.exc import IntegrityError

software_versions_bp = Blueprint('software_versions', __name__, url_prefix='/software-versions')

@software_versions_bp.route('/list')
def list():
    versions = []
    software = None
    
    if request.args.get('software_slug'):
        software = Software.query.filter_by(slug=request.args.get('software_slug')).first()
        if software:
            versions = software.versions.all()
    else:
        versions = SoftwareVersion.query.all()
    
    all_softwares = Software.query.all()
    
    return render_template('list/software_versions.html',
                          software=software,
                          versions=versions,
                          all_softwares=all_softwares)

@software_versions_bp.route('/software/<string:software_slug>')
def list_by_software(software_slug):
    software = Software.query.filter_by(slug=software_slug).first_or_404()
    software_versions = software.versions.all()
    return render_template('list/partials/software_versions.html', 
                          software=software, 
                          items=software_versions, 
                          all_versions=False)

@software_versions_bp.route('/view/<string:software_slug>/<string:version_slug>')
def view(software_slug, version_slug):
    software = Software.query.filter_by(slug=software_slug).first_or_404()
    software_version = SoftwareVersion.query.filter_by(
        software_id=software.id, 
        slug=version_slug
    ).first_or_404()
    
    return render_template('view/software_version.html', 
                          software_version=software_version)

@software_versions_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            new_software_version = SoftwareVersion(
                software_id=request.form.get('software_id'),
                version=request.form.get('version')
            )
            db.session.add(new_software_version)
            db.session.commit()
            flash("Version de logiciel ajoutée avec succès !", "success")
            return redirect(url_for('software_versions.list_by_software', 
                                  software_slug=new_software_version.software.slug))
        except IntegrityError:
            db.session.rollback()
            flash("Cette version existe déjà pour ce logiciel.", "error")

    softwares = Software.query.all()
    return render_template('add/software_version.html', softwares=softwares)

@software_versions_bp.route('/software/<string:software_slug>/add', methods=['GET', 'POST'])
def add_for_software(software_slug):
    software = Software.query.filter_by(slug=software_slug).first_or_404()
    
    if request.method == 'POST':
        try:
            new_software_version = SoftwareVersion(
                software_id=software.id,
                version=request.form.get('version')
            )
            db.session.add(new_software_version)
            db.session.commit()
            flash("Version de logiciel ajoutée avec succès !", "success")
            return redirect(url_for('software_versions.list_by_software', 
                                  software_slug=software_slug))
        except IntegrityError:
            db.session.rollback()
            flash("Cette version existe déjà pour ce logiciel.", "error")

    return render_template('add/software_version.html', software=software)

@software_versions_bp.route('/edit/<string:software_slug>/<string:version_slug>', methods=['GET', 'POST'])
def edit(software_slug, version_slug):
    software = Software.query.filter_by(slug=software_slug).first_or_404()
    software_version = SoftwareVersion.query.filter_by(
        software_id=software.id, 
        slug=version_slug
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            software_version.version = request.form['version']
            db.session.commit()
            flash("Version de logiciel modifiée avec succès !", "success")
            return redirect(url_for('software_versions.list_by_software', 
                                  software_slug=software_slug))
        except IntegrityError:
            db.session.rollback()
            flash("Cette version existe déjà pour ce logiciel.", "error")

    return render_template('edit/software_version.html', 
                          software_version=software_version)

@software_versions_bp.route('/delete/<string:software_slug>/<string:version_slug>', methods=['GET', 'POST'])
def delete(software_slug, version_slug):
    software = Software.query.filter_by(slug=software_slug).first_or_404()
    software_version = SoftwareVersion.query.filter_by(
        software_id=software.id, 
        slug=version_slug
    ).first_or_404()
    
    if request.method == 'POST':
        db.session.delete(software_version)
        db.session.commit()
        flash("Version de logiciel supprimée avec succès !", "success")
        return redirect(url_for('software_versions.list_by_software', 
                              software_slug=software_slug))
    
    return render_template('delete/software_version.html', 
                          software_version=software_version)
