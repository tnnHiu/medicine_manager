from app import db
from datetime import datetime


class MedicineBatch(db.Model):
    __tablename__ = 'medicine_batches'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    manufacturing_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    supplier = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    medicine = db.relationship('Medicine', backref='batches')

    def __repr__(self):
        return f"<MedicineBatch {self.batch_number} for {self.medicine.name}>"
