# controllers/medicine_controller.py
from flask import render_template, redirect, request, url_for, flash, session
from app import app, db
from models.medicine import Medicine
from controllers.auth_controller import login_required, role_required
from datetime import datetime


@app.route('/medicines')
@login_required
def medicines():
    medicines_list = Medicine.query.all()
    current_date = datetime.now()  # Thêm biến current_date
    return render_template('medicines.html',
                           medicines=medicines_list,
                           current_date=current_date)