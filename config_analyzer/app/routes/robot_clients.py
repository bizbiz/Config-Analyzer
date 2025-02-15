from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import RobotClient
from app.extensions import db

robot_clients_bp = Blueprint('robot_clients', __name__)

@robot_clients_bp.route('/robot_clients')
def list_robot_clients():
    robot_clients = RobotClient.query.all()
    return render_template('list/robot_clients.html', robot_clients=robot_clients)

@robot_clients_bp.route('/robot_clients/<int:robot_client_id>/view')
def view_robot_client(robot_client_id):
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    return render_template('view/robot_client.html', robot_client=robot_client)

@robot_clients_bp.route('/robot_clients/add', methods=['GET', 'POST'])
def add_robot_client():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        robot_modele_id = request.form.get('robot_modele_id')
        serial_number = request.form.get('serial_number')
        length = request.form.get('length')
        height = request.form.get('height')

        if not serial_number:
            flash("Le numéro de série est obligatoire.", "error")
            return redirect(url_for('robot_clients.add_robot_client'))

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

    return render_template('add/robot_client.html')

@robot_clients_bp.route('/robot_clients/edit/<int:robot_client_id>', methods=['GET', 'POST'])
def edit_robot_client(robot_client_id):
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    if request.method == 'POST':
        robot_client.client_id = request.form['client_id']
        robot_client.robot_modele_id = request.form['robot_modele_id']
        robot_client.serial_number = request.form['serial_number']
        robot_client.length = request.form['length']
        robot_client.height = request.form['height']

        db.session.commit()
        flash("Client robot modifié avec succès !", "success")
        return redirect(url_for('robot_clients.list_robot_clients'))

    return render_template('edit/robot_client.html', robot_client=robot_client)

@robot_clients_bp.route('/robot_clients/delete/<int:robot_client_id>', methods=['GET'])
def delete_robot_client(robot_client_id):
    robot_client = RobotClient.query.get_or_404(robot_client_id)
    db.session.delete(robot_client)
    db.session.commit()
    flash("Client robot supprimé avec succès !", "success")
    return redirect(url_for('robot_clients.list_robot_clients'))