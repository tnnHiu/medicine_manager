from flask import Flask
from extensions import db
from flask_migrate import Migrate
from models import *
from controllers import register_all_routes

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
# migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

register_all_routes(app)

if __name__ == '__main__':
    app.run()
