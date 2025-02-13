from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Client, db

clients_bp = Blueprint('clients', __name__)

# Route pour la page d'accueil
@clients_bp.route('/')
def home():
    return render_template('home.html')  # Le template doit être 

@clients_bp.route('/clients')
def list_clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@clients_bp.route('/add_client', methods=['POST'])
def add_client():
    name = request.form.get('name')
    postal_code = request.form.get('postal_code')

    if not name or not postal_code:
        flash("Le nom et le code postal sont obligatoires.", "error")
        return redirect(url_for('clients.list_clients'))

    existing_client = Client.query.filter_by(name=name, postal_code=postal_code).first()
    if existing_client:
        flash("Un client avec ce nom et ce code postal existe déjà.", "error")
        return redirect(url_for('clients.list_clients'))

    new_client = Client(name=name, postal_code=postal_code)
    db.session.add(new_client)
    db.session.commit()
    flash("Client ajouté avec succès !", "success")
    return redirect(url_for('clients.list_clients'))

@clients_bp.route('/edit_client/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.postal_code = request.form['postal_code']
        db.session.commit()
        flash("Client modifié avec succès !", "success")
        return redirect(url_for('clients.list_clients'))
    return render_template('edit_client.html', client=client)

@clients_bp.route('/delete_client/<int:client_id>', methods=['GET'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client supprimé avec succès !", "success")
    return redirect(url_for('clients.list_clients'))
