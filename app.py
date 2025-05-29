from flask import Flask
from extensions import db
from flask_migrate import Migrate
from models import *
from controllers import register_all_routes
from werkzeug.security import generate_password_hash
from models.user import RoleEnum  # Import enum nếu cần

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)

with app.app_context():
    db.create_all()

    from models import User
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin'),
            full_name='Quản trị viên',
            role=RoleEnum.admin
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin / admin")
    else:
        print("ℹ️ Admin user already exists")

register_all_routes(app)

if __name__ == '__main__':
    app.run()
