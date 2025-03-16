from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Client
from app.extensions import db

# Définition du blueprint avec un préfixe explicite
clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/list')
def list():
    """Affiche la liste des clients."""
    clients = Client.query.all()
    return render_template('list/partials/clients.html', items=clients)

@clients_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajoute un nouveau client."""
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')

        if not name or not address:
            flash("Le nom et l'adresse sont obligatoires.", "error")
            return redirect(url_for('clients.add'))

        new_client = Client(name=name, address=address)
        db.session.add(new_client)
        db.session.commit()

        flash("Client ajouté avec succès !", "success")
        return redirect(url_for('clients.list'))

    return render_template('add/client.html')

@clients_bp.route('/edit/<int:client_id>', methods=['GET', 'POST'])
def edit(client_id):
    """Modifie un client existant."""
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.address = request.form['address']

        db.session.commit()
        flash("Client modifié avec succès !", "success")
        return redirect(url_for('clients.list'))

    return render_template('edit/client.html', client=client)

@clients_bp.route('/delete/<int:client_id>', methods=['GET'])
def delete(client_id):
    """Supprime un client."""
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client supprimé avec succès !", "success")
    return redirect(url_for('clients.list'))
