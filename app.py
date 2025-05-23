from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# Import sau khi tạo app và db
from models import *
from controllers import *


def create_admin_if_not_exists():
    from models.user import User, RoleEnum

    admin = User.query.filter_by(username="admin").first()
    if admin:
        return
    admin_user = User(
        username="admin",
        password_hash=generate_password_hash("admin"),
        full_name="Quản trị viên",
        role=RoleEnum.admin
    )
    try:
        db.session.add(admin_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)


with app.app_context():
    db.create_all()
    create_admin_if_not_exists()

if __name__ == '__main__':
    app.run(debug=True)
