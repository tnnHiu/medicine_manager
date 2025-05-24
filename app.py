from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# Import sau khi tạo app và db
from models import *
from controllers import *

with app.app_context():
    db.create_all()
    # create_admin_if_not_exists()

if __name__ == '__main__':
    app.run(debug=True)
