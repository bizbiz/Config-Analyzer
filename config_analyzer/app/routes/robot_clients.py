from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotClient, Client, RobotModel
from app.extensions import db

robot_clients_bp = Blueprint('robot_clients', __name__)

@robot_clients_bp.route('/robot_clients')
def list_robot_clients():
    robot_clients = RobotClient.query.all()
    return render_template('list/robot_clients.html', robot_clients=robot_clients)

@robot_clients_bp.route('/robot_clients/add', methods=['GET', 'POST'])
def add_robot_client():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        robot_modele_id = request.form.get('robot_modele_id')
        serial_number = request.form.get('serial_number')
        length = request.form.get('length')
        height = request.form.get('height')

        form_data = request.form

        if not serial_number:
            flash("Le numéro de série est obligatoire.", "error")
            return render_template('add/robot_client.html', clients=Client.query.all(), robot_models=RobotModel.query.all(), serial_number_error=True, form_data=form_data)

        if RobotClient.query.filter_by(serial_number=serial_number).first():
            flash("Le numéro de série existe déjà.", "error")
            return render_template('add/robot_client.html', clients=Client.query.all(), robot_models=RobotModel.query.all(), serial_number_error=True, form_data=form_data)

        try:
            length = float(length) if length else None
        except ValueError:
            flash("La longueur doit être un nombre à virgule.", "error")
            return render_template('add/robot_client.html', clients=Client.query.all(), robot_models=RobotModel.query.all(), length_error=True, form_data=form_data)

        try:
            height = float(height) if height else None
        except ValueError:
            flash("La hauteur doit être un nombre à virgule.", "error")
            return render_template('add/robot_client.html', clients=Client.query.all(), robot_models=RobotModel.query.all(), height_error=True, form_data=form_data)

        new_robot_client = RobotClient(
            client_id=client_id,
            robot_modele_id=robot_modele_id,
            serial_number=serial_number,
            length=length,
            height=height
        )
        db.session.add(new_robot_client)
        db.session.commit()

        flash("Client robot ajouté avec succès !", "success")
        return redirect(url_for('robot_clients.list_robot_clients'))

    clients = Client.query.all()
    robot_models = RobotModel.query.all()
    form_data = {}
    return render_template('add/robot_client.html', clients=clients, robot_models=robot_models, form_data=form_data)

@robot_clients_bp.route('/robot_clients/edit/<int:robot_client_id>', methods=['GET', 'POST'])
def edit_robot_client(robot_client_id):
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
        return redirect(url_for('robot_clients.list_robot_clients'))

    form_data = {}
    return render_template('edit/robot_client.html', robot_client=robot_client, form_data=form_data)

@robot_clients_bp.route('/robot_clients/delete/<int:robot_client_id>', methods=['GET'])
def delete_robot_client(robot_client_id):
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    db.session.delete(robot_client)
    db.session.commit()
    flash("Client robot supprimé avec succès !", "success")
    return redirect(url_for('robot_clients.list_robot_clients'))

@robot_clients_bp.route('/robot_clients/view/<int:robot_client_id>', methods=['GET'])
def view_robot_client(robot_client_id):
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    return render_template('view/robot_client.html', robot_client=robot_client)