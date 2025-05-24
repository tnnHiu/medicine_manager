from flask import render_template, redirect, request, url_for, flash, session
from controllers.auth_controller import login_required, role_required
from models import Patient
from extensions import db
from datetime import datetime

from models.patient import GenderEnum


def register_patient_routes(app):
    @app.route('/patients', methods=['GET'], endpoint='patients')
    @login_required
    @role_required(['admin', 'doctor', 'pharmacist'])
    def patients():
        patients_list = Patient.query.all()
        return render_template('patients.html',
                               patients=patients_list)

    @app.route('/patients/add', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_patient():
        try:
            # Lấy dữ liệu từ form
            full_name = request.form.get('full_name')
            id_card = request.form.get('id_card')
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            phone = request.form.get('phone')
            address = request.form.get('address')

            # Kiểm tra dữ liệu đầu vào
            if not id_card:
                flash('Số căn cước là bắt buộc!', 'error')
                return redirect(url_for('patients'))

            # Kiểm tra xem id_card đã tồn tại chưa
            if Patient.query.filter_by(id_card=id_card).first():
                flash('Số căn cước đã tồn tại!', 'error')
                return redirect(url_for('patients'))

            # Kiểm tra gender hợp lệ
            if gender not in [g.value for g in GenderEnum]:
                flash('Giới tính không hợp lệ!', 'error')
                return redirect(url_for('patients'))

            # Chuyển đổi date_of_birth thành datetime
            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None

            # Tạo bệnh nhân mới
            new_patient = Patient(
                full_name=full_name,
                id_card=id_card,
                date_of_birth=date_of_birth,
                gender=GenderEnum[gender] if gender else None,
                phone=phone,
                address=address
            )

            # Lưu vào cơ sở dữ liệu
            db.session.add(new_patient)
            db.session.commit()

            flash('Thêm bệnh nhân thành công!', 'success')
            return redirect(url_for('patients'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('patients'))

    @app.route('/patients/edit/<int:patient_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def edit_patient(patient_id):
        try:
            # Tìm bệnh nhân theo ID
            patient = Patient.query.get_or_404(patient_id)

            # Lấy dữ liệu từ form
            full_name = request.form.get('full_name')
            id_card = request.form.get('id_card')
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            phone = request.form.get('phone')
            address = request.form.get('address')

            # Kiểm tra dữ liệu đầu vào
            if not id_card:
                flash('Số căn cước là bắt buộc!', 'error')
                return redirect(url_for('patients'))

            # Kiểm tra xem id_card đã tồn tại chưa (trừ chính bệnh nhân đang chỉnh sửa)
            existing_patient = Patient.query.filter_by(id_card=id_card).first()
            if existing_patient and existing_patient.id != patient_id:
                flash('Số căn cước đã tồn tại!', 'error')
                return redirect(url_for('patients'))

            # Kiểm tra gender hợp lệ
            if gender and gender not in [g.value for g in GenderEnum]:
                flash('Giới tính không hợp lệ!', 'error')
                return redirect(url_for('patients'))

            # Cập nhật thông tin bệnh nhân
            patient.full_name = full_name
            patient.id_card = id_card
            patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None
            patient.gender = GenderEnum[gender] if gender else None
            patient.phone = phone
            patient.address = address

            # Lưu vào cơ sở dữ liệu
            db.session.commit()

            flash('Cập nhật bệnh nhân thành công!', 'success')
            return redirect(url_for('patients'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('patients'))

    @app.route('/patients/delete/<int:patient_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def delete_patient(patient_id):
        try:
            # Tìm bệnh nhân theo ID
            patient = Patient.query.get_or_404(patient_id)

            # Xóa bệnh nhân
            db.session.delete(patient)
            db.session.commit()

            flash('Xóa bệnh nhân thành công!', 'success')
            return redirect(url_for('patients'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('patients'))
