# app/models/associations/client_configuration.py

from app.extensions import db

class ClientConfiguration(db.Model):
    config_instance_id = db.Column(db.Integer, db.ForeignKey('configuration_instances.id'))
    parameter_value_id = db.Column(db.Integer, db.ForeignKey('parameter_values.id'))
