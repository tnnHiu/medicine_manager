from app import db


class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(20), unique=True)
    unit = db.Column(db.String(20))
    quantity = db.Column(db.Integer)
    expiration_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
