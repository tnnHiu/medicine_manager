from extensions import db

# Đơn thuốc
class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.Enum('pending', 'dispensed', 'cancelled', name='prescription_status'), default='pending')

    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan')
    doctor = db.relationship('User')

