from app import db


class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id'))
    change_type = db.Column(db.Enum('import', 'dispense'))
    quantity = db.Column(db.Integer)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    note = db.Column(db.Text)

    medicine = db.relationship('Medicine')
    batch = db.relationship('MedicineBatch')
    user = db.relationship('User')