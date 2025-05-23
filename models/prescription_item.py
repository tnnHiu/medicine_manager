from app import db

class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

    prescription = db.relationship('Prescription', backref='items')
    medicine = db.relationship('Medicine')
