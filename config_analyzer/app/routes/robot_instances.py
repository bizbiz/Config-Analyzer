# app/routes/robot_instances.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.entities.client import Client
from app.models.entities.robot_model import RobotModel
from app.models.entities.robot_instance import RobotInstance
from app.extensions import db

robot_instances_bp = Blueprint('robot_instances', __name__, url_prefix='/robot-instances')

@robot_instances_bp.route('/list')
def list():
    robots = RobotInstance.query.options(
        db.joinedload(RobotInstance.client),
        db.joinedload(RobotInstance.model)
    ).all()
    
    return render_template('list/robot_instances.html', 
                         robots=robots,
                         clients=Client.query.all(),
                         robot_models=RobotModel.query.all())

@robot_instances_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            new_robot = RobotInstance(
                serial_number=request.form['serial_number'],
                client_id=request.form['client_id'],
                robot_model_id=request.form['robot_model_id'],
                length=float(request.form['length']) if request.form['length'] else None,
                height=float(request.form['height']) if request.form['height'] else None
            )
            db.session.add(new_robot)
            db.session.commit()
            flash("Instance robot ajoutée avec succès", "success")
            return redirect(url_for('robot_instances.list_instances'))
            
        except ValueError:
            db.session.rollback()
            flash("Erreur de format numérique", "error")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur base de données : {str(e)}", "error")
    
    return render_template('add/robot_instance.html',
                         clients=Client.query.all(),
                         robot_models=RobotModel.query.all(),
                         preselected_model_id=request.args.get('robot_model_id'))

@robot_instances_bp.route('/edit/<string:serial_number>', methods=['GET', 'POST'])
def edit(serial_number):
    robot = RobotInstance.query.filter_by(serial_number=serial_number).first_or_404()
    
    if request.method == 'POST':
        try:
            robot.serial_number = request.form['serial_number']
            robot.client_id = request.form['client_id']
            robot.robot_model_id = request.form['robot_model_id']
            robot.length = float(request.form['length']) if request.form['length'] else None
            robot.height = float(request.form['height']) if request.form['height'] else None
            
            db.session.commit()
            flash("Modifications enregistrées", "success")
            return redirect(url_for('robot_instances.list_instances'))
            
        except ValueError:
            flash("Valeurs numériques invalides", "error")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur base de données : {str(e)}", "error")
    
    return render_template('edit/robot_instance.html',
                         robot_instance=robot,
                         clients=Client.query.all(),
                         robot_models=RobotModel.query.all())

@robot_instances_bp.route('/delete/<string:serial_number>', methods=['POST'])
def delete(serial_number):
    robot = RobotInstance.query.filter_by(serial_number=serial_number).first_or_404()
    
    try:
        db.session.delete(robot)
        db.session.commit()
        flash("Instance robot supprimée", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur suppression : {str(e)}", "error")
    
    return redirect(url_for('robot_instances.list_instances'))

@robot_instances_bp.route('/view/<string:serial_number>')
def view(serial_number):
    robot = RobotInstance.query.options(
        db.joinedload(RobotInstance.client),
        db.joinedload(RobotInstance.model)
    ).filter_by(serial_number=serial_number).first_or_404()
    
    return render_template('view/robot_instance.html', 
                         robot_instance=robot)
