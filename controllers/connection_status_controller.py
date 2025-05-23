from flask import render_template
from app import app, db
from sqlalchemy import text

@app.route("/")
def home():
    try:
        # Kiểm tra kết nối database
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        status = {
            'state': 'success',
            'message': 'Kết nối cơ sở dữ liệu thành công!',
            'details': 'MySQL đã được kết nối và hoạt động bình thường.'
        }
    except Exception as e:
        status = {
            'state': 'error',
            'message': 'Không thể kết nối đến cơ sở dữ liệu!',
            'details': str(e)
        }
        db.session.rollback()
    finally:
        db.session.close()

    return render_template('status.html', status=status)