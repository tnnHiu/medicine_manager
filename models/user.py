from app import db
import enum

# Người dùng

class RoleEnum(enum.Enum):
    admin = "admin"
    doctor = "doctor"
    pharmacist = "pharmacist"

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

