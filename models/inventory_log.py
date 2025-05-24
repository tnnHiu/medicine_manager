from extensions import db


# Log của kho thuốc

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'))
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id', ondelete='CASCADE'))
    change_type = db.Column(db.Enum('import', 'dispense', name='change_type_enum'))
    quantity = db.Column(db.Integer)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    note = db.Column(db.Text)

    medicine = db.relationship('Medicine')
    batch = db.relationship('MedicineBatch')
    user = db.relationship('User')
