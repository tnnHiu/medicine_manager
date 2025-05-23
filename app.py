from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# Import sau khi tạo app và db
from models import *
from controllers import *

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
