from . import db

class Software(db.Model):
    __tablename__ = 'softwares'  # Ensure table name matches the foreign key reference
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parametres = db.relationship('ParametreLogiciel', back_populates='software')  # Add back-reference

    def __init__(self, name):
        self.name = name

# Import RobotSoftware here to avoid circular import issues
from .robot_software import RobotSoftware