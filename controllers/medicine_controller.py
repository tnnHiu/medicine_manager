from flask import render_template, redirect, request, url_for, flash, session
from controllers.auth_controller import login_required, role_required
from models import Medicine
from extensions import db
import uuid

def register_medicine_routes(app):
    @app.route('/medicines', methods=['GET'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def medicines():
        medicines_list = Medicine.query.all()
        return render_template('medicines.html', medicines=medicines_list)

    @app.route('/medicines/add', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_medicine():
        try:
            name = request.form.get('name').strip()
            unit = request.form.get('unit').strip()

            if not name or not unit:
                flash('Tên thuốc và đơn vị là bắt buộc!', 'error')
                return redirect(url_for('medicines'))

            if Medicine.query.filter_by(name=name).first():
                flash('Tên thuốc đã tồn tại!', 'error')
                return redirect(url_for('medicines'))

            new_medicine = Medicine(
                name=name,
                code=f'MED-{uuid.uuid4().hex[:8]}',
                unit=unit
            )
            db.session.add(new_medicine)
            db.session.commit()

            flash('Thêm thuốc thành công!', 'success')
            return redirect(url_for('medicines'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicines'))

    @app.route('/medicines/edit/<int:medicine_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def edit_medicine(medicine_id):
        try:
            medicine = Medicine.query.get_or_404(medicine_id)
            name = request.form.get('name').strip()
            unit = request.form.get('unit').strip()

            if not name or not unit:
                flash('Tên thuốc và đơn vị là bắt buộc!', 'error')
                return redirect(url_for('medicines'))

            existing_medicine = Medicine.query.filter_by(name=name).first()
            if existing_medicine and existing_medicine.id != medicine_id:
                flash('Tên thuốc đã tồn tại!', 'error')
                return redirect(url_for('medicines'))

            medicine.name = name
            medicine.unit = unit
            db.session.commit()

            flash('Cập nhật thuốc thành công!', 'success')
            return redirect(url_for('medicines'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicines'))

    @app.route('/medicines/delete/<int:medicine_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def delete_medicine(medicine_id):
        try:
            medicine = Medicine.query.get_or_404(medicine_id)

            db.session.delete(medicine)
            db.session.commit()

            flash('Xóa thuốc thành công!', 'success')
            return redirect(url_for('medicines'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicines'))