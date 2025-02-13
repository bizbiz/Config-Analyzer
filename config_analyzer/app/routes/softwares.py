from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Software, db

softwares_bp = Blueprint('softwares', __name__)

@softwares_bp.route('/softwares')
def list_softwares():
    softwares = Software.query.order_by(Software.name).all()
    return render_template('softwares.html', softwares=softwares)

@softwares_bp.route('/add-software', methods=['POST'])
def add_software():
    try:
        new_software = Software(
            name=request.form['name'],
            version=request.form['version']
        )
        db.session.add(new_software)
        db.session.commit()
        flash('Logiciel ajouté avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur : {str(e)}", 'danger')
    return redirect(url_for('softwares.list_softwares'))

@softwares_bp.route('/edit-software/<int:software_id>', methods=['GET', 'POST'])
def edit_software(software_id):
    software = Software.query.get_or_404(software_id)
    if request.method == 'POST':
        try:
            software.name = request.form['name']
            software.version = request.form['version']
            db.session.commit()
            flash('Modifications enregistrées', 'success')
            return redirect(url_for('softwares.list_softwares'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur : {str(e)}', 'danger')
    
    return render_template('edit_software.html', software=software)

@softwares_bp.route('/delete-software/<int:software_id>')
def delete_software(software_id):
    software = Software.query.get_or_404(software_id)
    try:
        db.session.delete(software)
        db.session.commit()
        flash('Logiciel supprimé', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('softwares.list_softwares'))
