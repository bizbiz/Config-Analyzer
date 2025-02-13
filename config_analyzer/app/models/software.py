from . import db

class Software(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    robots = db.relationship('Robot', back_populates='software')

    def __init__(self, name):
        self.name = name

# Import RobotSoftware here to avoid circular import issues
from .robot_software import RobotSoftware