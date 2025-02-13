from . import db

class RobotSoftware(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.Integer, db.ForeignKey('robot.id'), nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('software.id'), nullable=False)
    robot = db.relationship('Robot', backref=db.backref('robot_software', lazy=True))
    software = db.relationship('Software', backref=db.backref('robot_software', lazy=True))