import os

# Cấu hình Database
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:10012003@localhost:3306/medicine_manager'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Cấu hình Flask
SECRET_KEY = os.urandom(32)
DEBUG = True
