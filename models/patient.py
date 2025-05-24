from app import db

from sqlalchemy import Enum
import enum

# Bệnh nhân

class GenderEnum(enum.Enum):
    M = "M"
    F = "F"

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(GenderEnum))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    prescriptions = db.relationship('Prescription', backref='patient', cascade='all, delete-orphan')
