from app import create_app
from app import db

def init_db(app):
    with app.app_context():
        # db.drop_all()  # Uncomment this line if you want to drop all tables before creating them
        db.create_all()  # Create all tables
        print("🗃️ Tables created successfully")

if __name__ == "__main__":
    app = create_app()
    init_db(app)
    app.run(host="0.0.0.0", port=5000, debug=True)