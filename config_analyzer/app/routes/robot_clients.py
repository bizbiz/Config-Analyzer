from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotClient, Client, RobotModel
from app.extensions import db

robot_clients_bp = Blueprint('robot_clients', __name__, url_prefix='/robot-clients')

@robot_clients_bp.route('/list')
def list():
    """Affiche la liste des clients robots"""
    robot_clients = RobotClient.query.all()
    return render_template('list/partials/robot_clients.html', items=robot_clients)

@robot_clients_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute un nouveau client robot"""
    if request.method == 'POST':
        # ... (logique existante inchangée)
        return redirect(url_for('robot_clients.list'))
    
    return render_template('add/robot_client.html', 
                         clients=Client.query.all(),
                         robot_models=RobotModel.query.all(),
                         form_data=request.form)

@robot_clients_bp.route('/edit/<int:robot_client_id>', methods=['GET', 'POST'])
def edit(robot_client_id):
    """Modifie un client robot existant"""
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    
    if request.method == 'POST':
        serial_number = request.form['serial_number']
        length = request.form['length']
        height = request.form['height']

        form_data = request.form

        if RobotClient.query.filter(RobotClient.serial_number == serial_number, RobotClient.id != robot_client_id).first():
            flash("Le numéro de série existe déjà.", "error")
            return render_template('edit/robot_client.html', robot_client=robot_client, serial_number_error=True, form_data=form_data)

        try:
            robot_client.length = float(length) if length else None
        except ValueError:
            flash("La longueur doit être un nombre à virgule.", "error")
            return render_template('edit/robot_client.html', robot_client=robot_client, length_error=True, form_data=form_data)

        try:
            robot_client.height = float(height) if height else None
        except ValueError:
            flash("La hauteur doit être un nombre à virgule.", "error")
            return render_template('edit/robot_client.html', robot_client=robot_client, height_error=True, form_data=form_data)

        robot_client.serial_number = serial_number

        db.session.commit()
        flash("Client robot modifié avec succès !", "success")
        return redirect(url_for('robot_clients.list'))
    
    return render_template('edit/robot_client.html', 
                         robot_client=robot_client,
                         form_data=request.form)

@robot_clients_bp.route('/delete/<int:robot_client_id>')
def delete(robot_client_id):
    """Supprime un client robot"""
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    db.session.delete(robot_client)
    db.session.commit()
    flash("Client robot supprimé avec succès !", "success")
    return redirect(url_for('robot_clients.list'))

@robot_clients_bp.route('/view/<int:robot_client_id>')
def view(robot_client_id):
    """Affiche les détails d'un client robot"""
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    return render_template('view/robot_client.html', robot_client=robot_client)