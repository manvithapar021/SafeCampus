from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    existing = User.query.filter_by(email="admin@safecampus.com").first()
    if existing:
        print("Admin already exists!")
    else:
        admin = User(
            name="Admin Security",
            email="admin@safecampus.com",
            password=generate_password_hash("Admin@123"),
            role="admin",
            phone="9999999999"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully!")
