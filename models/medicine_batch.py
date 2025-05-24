from extensions import db

# Thông tin lô thuốc
class MedicineBatch(db.Model):
    __tablename__ = 'medicine_batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False)
    supplier = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    batch_items = db.relationship('MedicineBatchItem', backref='batch', cascade='all, delete-orphan')
