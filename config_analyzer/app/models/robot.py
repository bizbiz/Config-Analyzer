from . import db

class Robot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('software.id'), nullable=False)
    software = db.relationship('Software', back_populates='robots')

    def __init__(self, name, software_id):
        self.name = name
        self.software_id = software_id

# Import Software here to avoid circular import issues
from .software import Software