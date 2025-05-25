from flask import render_template, redirect, request, url_for, flash, session
from controllers.auth_controller import login_required, role_required
from models import Patient, Prescription
from models.patient import GenderEnum
from extensions import db
from datetime import datetime


def register_patient_routes(app):
    @app.route('/patients', methods=['GET'], endpoint='patients')
    @login_required
    @role_required(['admin', 'doctor', 'pharmacist'])
    def patients():
        patients_list = Patient.query.all()
        # Tải trước đơn thuốc để tránh N+1 query
        for patient in patients_list:
            patient.prescriptions = Prescription.query.filter(
                Prescription.patient_id == patient.id,
                Prescription.status.in_(['pending', 'dispensed'])
            ).all()
        return render_template('patients.html', patients=patients_list)

    @app.route('/patients/add', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_patient():
        try:
            full_name = request.form.get('full_name')
            id_card = request.form.get('id_card')
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            phone = request.form.get('phone')
            address = request.form.get('address')

            if not id_card:
                flash('Số căn cước là bắt buộc!', 'error')
                return redirect(url_for('patients'))

            if Patient.query.filter_by(id_card=id_card).first():
                flash('Số căn cước đã tồn tại!', 'error')
                return redirect(url_for('patients'))

            if gender and gender not in [g.value for g in GenderEnum]:
                flash('Giới tính không hợp lệ!', 'error')
                return redirect(url_for('patients'))

            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None

            new_patient = Patient(
                full_name=full_name,
                id_card=id_card,
                date_of_birth=date_of_birth,
                gender=GenderEnum[gender] if gender else None,
                phone=phone,
                address=address
            )

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
            patient = Patient.query.get_or_404(patient_id)

            full_name = request.form.get('full_name')
            id_card = request.form.get('id_card')
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            phone = request.form.get('phone')
            address = request.form.get('address')

            if not id_card:
                flash('Số căn cước là bắt buộc!', 'error')
                return redirect(url_for('patients'))

            existing_patient = Patient.query.filter_by(id_card=id_card).first()
            if existing_patient and existing_patient.id != patient_id:
                flash('Số căn cước đã tồn tại!', 'error')
                return redirect(url_for('patients'))

            if gender and gender not in [g.value for g in GenderEnum]:
                flash('Giới tính không hợp lệ!', 'error')
                return redirect(url_for('patients'))

            patient.full_name = full_name
            patient.id_card = id_card
            patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None
            patient.gender = GenderEnum[gender] if gender else None
            patient.phone = phone
            patient.address = address

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
            patient = Patient.query.get_or_404(patient_id)

            db.session.delete(patient)
            db.session.commit()

            flash('Xóa bệnh nhân thành công!', 'success')
            return redirect(url_for('patients'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('patients'))
