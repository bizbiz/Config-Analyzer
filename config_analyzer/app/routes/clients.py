from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Client, PostalCode
from app.extensions import db  # Import db ici

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients')
def list_clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@clients_bp.route('/clients/add', methods=['POST'])
def add_client():
    name = request.form.get('name')
    postal_code = request.form.get('postal_code')
    city = request.form.get('city')
    country_code = request.form.get('country_code')

    if not name or not postal_code or not city or not country_code:
        flash("Le nom, le code postal, la ville et le code pays sont obligatoires.", "error")
        return redirect(url_for('clients.list_clients'))

    existing_postal_code = PostalCode.query.filter_by(code=postal_code, city=city, country_code=country_code).first()
    if not existing_postal_code:
        new_postal_code = PostalCode(code=postal_code, city=city, country_code=country_code)
        db.session.add(new_postal_code)
        db.session.commit()

    new_client = Client(name=name, postal_code=postal_code, postal_code_city=city, postal_code_country_code=country_code)
    db.session.add(new_client)
    db.session.commit()
    flash("Client ajouté avec succès !", "success")
    return redirect(url_for('clients.list_clients'))

@clients_bp.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.postal_code = request.form['postal_code']
        client.postal_code_city = request.form['city']
        client.postal_code_country_code = request.form['country_code']
        db.session.commit()
        flash("Client modifié avec succès !", "success")
        return redirect(url_for('clients.list_clients'))
    return render_template('edit_client.html', client=client)

@clients_bp.route('/clients/delete/<int:client_id>', methods=['GET'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client supprimé avec succès !", "success")
    return redirect(url_for('clients.list_clients'))