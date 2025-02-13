from . import db

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    
    parametres = db.relationship('ParametreLogiciel', back_populates='client')
