from app import db

# Thuốc - Đơn thuốc

class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='SET NULL'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id', ondelete='SET NULL'), nullable=True)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

    medicine = db.relationship('Medicine')
    batch = db.relationship('MedicineBatch')
