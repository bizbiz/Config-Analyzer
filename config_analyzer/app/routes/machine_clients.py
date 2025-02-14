from flask import Blueprint, render_template, redirect, url_for, flash, request
from config_analyzer.models import Client, db, MachineClient, Robot, Software

machine_clients_bp = Blueprint('machine_clients', __name__)

@machine_clients_bp.route('/machine-clients')
def list_machine_clients():
    # Ajouter le chargement des logiciels
    softwares = Software.query.order_by(Software.name).all()
    clients = Client.query.all()
    robots = Robot.query.all()
    
    return render_template(
        'machine_clients.html',
        machine_clients=MachineClient.query.all(),
        softwares=softwares,  # Ajout crucial
        clients=clients,
        robots=robots
    )


@machine_clients_bp.route('/add-machine-client', methods=['POST'])
def add_machine_client():
    try:
        # Vérification des données requises
        if not all(key in request.form for key in ['software_id', 'robot_id', 'client_id', 'serial_number']):
            flash("Tous les champs obligatoires doivent être remplis", "danger")
            return redirect(url_for('machine_clients.list_machine_clients'))
            
        new_mc = MachineClient(
            software_id=request.form['software_id'],
            robot_id=request.form['robot_id'],
            client_id=request.form['client_id'],
            serial_number=request.form['serial_number']
        )
        db.session.add(new_mc)
        db.session.commit()
        flash("Machine client ajoutée avec succès", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur : {str(e)}", "danger")
    return redirect(url_for('machine_clients.list_machine_clients'))


@machine_clients_bp.route('/edit-machine-client/<int:machine_client_id>', methods=['GET', 'POST'])
def edit_machine_client(machine_client_id):
    mc = MachineClient.query.get_or_404(machine_client_id)
    if request.method == 'POST':
        try:
            mc.robot_id = request.form['robot_id']
            mc.client_id = request.form['client_id']
            mc.serial_number = request.form['serial_number']
            db.session.commit()
            flash('Modifications enregistrées', 'success')
            return redirect(url_for('machine_clients.list_machine_clients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur : {str(e)}', 'danger')
    
    robots = Robot.query.all()
    clients = Client.query.all()
    return render_template('edit_machine_client.html', 
                         machine_client=mc,
                         robots=robots,
                         clients=clients)

@machine_clients_bp.route('/delete-machine-client/<int:machine_client_id>')
def delete_machine_client(machine_client_id):
    mc = MachineClient.query.get_or_404(machine_client_id)
    try:
        db.session.delete(mc)
        db.session.commit()
        flash('Machine client supprimée', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('machine_clients.list_machine_clients'))
