from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Robot, db

robots_bp = Blueprint('robots', __name__)

@robots_bp.route('/robots')
def list_robots():
    robots = Robot.query.order_by(Robot.name).all()
    return render_template('robots.html', robots=robots)

@robots_bp.route('/add_robot', methods=['POST'])
def add_robot():
    name = request.form.get('name')
    manufacturer = request.form.get('manufacturer')
    
    if Robot.query.filter_by(name=name).first():
        flash('Un robot avec ce nom existe déjà', 'error')
        return redirect(url_for('robots.list_robots'))
    
    new_robot = Robot(name=name, manufacturer=manufacturer)
    db.session.add(new_robot)
    db.session.commit()
    flash('Robot ajouté avec succès', 'success')
    return redirect(url_for('robots.list_robots'))

@robots_bp.route('/edit_robot/<int:robot_id>', methods=['GET', 'POST'])
def edit_robot(robot_id):
    robot = Robot.query.get_or_404(robot_id)
    if request.method == 'POST':
        robot.name = request.form['name']
        robot.manufacturer = request.form['manufacturer']
        db.session.commit()
        flash('Robot mis à jour', 'success')
        return redirect(url_for('robots.list_robots'))
    return render_template('edit_robot.html', robot=robot)

@robots_bp.route('/delete_robot/<int:robot_id>')
def delete_robot(robot_id):
    robot = Robot.query.get_or_404(robot_id)
    db.session.delete(robot)
    db.session.commit()
    flash('Robot supprimé', 'success')
    return redirect(url_for('robots.list_robots'))
