from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# Import các controllers
from controllers import connection_status_controller

if __name__ == '__main__':
    app.run(debug=True)