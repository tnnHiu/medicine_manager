from app import db


class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, default=0)  # Tổng số lượng từ các lô
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    def __repr__(self):
        return f"<Medicine {self.name}>"