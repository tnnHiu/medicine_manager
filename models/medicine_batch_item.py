from extensions import db

# Thuốc - Lô thuốc
class MedicineBatchItem(db.Model):
    __tablename__ = 'medicine_batch_items'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'))
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id', ondelete='CASCADE'))
    quantity = db.Column(db.Integer, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
