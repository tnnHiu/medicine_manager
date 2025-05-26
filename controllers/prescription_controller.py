from flask import render_template, redirect, request, url_for, flash, session
from controllers.auth_controller import login_required, role_required
from models import Prescription, PrescriptionItem, Patient, MedicineBatch, Medicine, InventoryLog, MedicineBatchItem
from extensions import db
from datetime import datetime
import logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Định nghĩa giá trị hợp lệ cho change_type
VALID_CHANGE_TYPES = {'import', 'dispense'}


def register_prescription_routes(app):
    @app.route('/prescriptions', methods=['GET'])
    @login_required
    @role_required(['doctor', 'pharmacist', 'admin'])
    def prescriptions():
        try:
            prescriptions_list = Prescription.query.filter_by(
                status='pending'
            ).options(
                joinedload(Prescription.patient),
                joinedload(Prescription.doctor)
            ).order_by(
                Prescription.created_at.asc()
            ).all()
            logger.debug(f"Loaded {len(prescriptions_list)} pending prescriptions")
            return render_template('prescriptions.html', prescriptions=prescriptions_list)
        except Exception as e:
            logger.error(f"Error loading prescriptions: {str(e)}")
            flash(f'Có lỗi xảy ra khi tải danh sách đơn thuốc: {str(e)}', 'error')
            return render_template('prescriptions.html', prescriptions=[])

    @app.route('/prescriptions/add', methods=['GET', 'POST'])
    @login_required
    @role_required(['doctor', 'admin'])
    def add_prescription():
        if request.method == 'POST':
            try:
                patient_id = request.form.get('patient_id')
                medicine_ids = request.form.getlist('medicine_id[]')
                dosages = request.form.getlist('dosage[]')
                frequencies = request.form.getlist('frequency[]')
                durations = request.form.getlist('duration[]')
                quantities = request.form.getlist('quantity[]')

                if not patient_id or not medicine_ids or len(medicine_ids) != len(dosages) or len(medicine_ids) != len(
                        frequencies) or len(medicine_ids) != len(durations) or len(medicine_ids) != len(quantities):
                    flash('Thông tin đơn thuốc không hợp lệ!', 'error')
                    return redirect(url_for('add_prescription'))

                patient = Patient.query.get(patient_id)
                if not patient:
                    flash('Bệnh nhân không tồn tại!', 'error')
                    return redirect(url_for('add_prescription'))

                new_prescription = Prescription(
                    patient_id=patient_id,
                    doctor_id=session.get('user_id')
                )
                db.session.add(new_prescription)
                db.session.flush()

                for i in range(len(medicine_ids)):
                    medicine_id = int(medicine_ids[i])
                    dosage = dosages[i].strip()
                    frequency = frequencies[i].strip()
                    duration = durations[i].strip()
                    try:
                        quantity = int(quantities[i])
                    except ValueError:
                        flash(f'Số lượng thuốc thứ {i + 1} không hợp lệ!', 'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    if not dosage or not frequency or not duration or quantity <= 0:
                        flash(f'Thông tin thuốc thứ {i + 1} không hợp lệ!', 'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    medicine = Medicine.query.get(medicine_id)
                    if not medicine:
                        flash(f'Thuốc ID {medicine_id} không tồn tại!', 'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    # Kiểm tra tổng tồn kho từ lô hoạt động và chưa hết hạn
                    total_stock = db.session.query(func.coalesce(func.sum(MedicineBatchItem.quantity), 0)).join(
                        MedicineBatch, MedicineBatchItem.batch_id == MedicineBatch.id
                    ).filter(
                        MedicineBatchItem.medicine_id == medicine_id,
                        MedicineBatchItem.quantity > 0,
                        MedicineBatch.is_active == True,
                        MedicineBatchItem.expiration_date > datetime.now().date()
                    ).scalar()

                    logger.debug(
                        f"Medicine ID {medicine_id} ({medicine.name}): Total stock = {total_stock}, Requested = {quantity}")

                    if total_stock == 0:
                        flash(
                            f'Thuốc {medicine.name or "ID " + str(medicine_id)} không có trong kho hoặc không có lô hoạt động/chưa hết hạn!',
                            'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    if quantity > total_stock:
                        flash(
                            f'Số lượng yêu cầu cho {medicine.name or "ID " + str(medicine_id)} ({quantity}) vượt quá tồn kho ({total_stock})!',
                            'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    batch_items = MedicineBatchItem.query.join(MedicineBatch).filter(
                        MedicineBatchItem.medicine_id == medicine_id,
                        MedicineBatchItem.quantity > 0,
                        MedicineBatch.is_active == True,
                        MedicineBatchItem.expiration_date > datetime.now().date()
                    ).order_by(MedicineBatch.created_at.asc()).all()

                    if not batch_items:
                        flash(
                            f'Thuốc {medicine.name or "ID " + str(medicine_id)} không có lô nào khả dụng với số lượng lớn hơn 0!',
                            'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    logger.debug(
                        f"Available batches for Medicine ID {medicine_id}: {[(b.batch_id, b.quantity, b.batch.batch_number) for b in batch_items]}")

                    remaining_quantity = quantity
                    allocated_batches = []
                    for batch_item in batch_items:
                        if remaining_quantity <= 0:
                            break
                        available_quantity = min(batch_item.quantity, remaining_quantity)
                        batch_item.quantity -= available_quantity
                        remaining_quantity -= available_quantity
                        allocated_batches.append((batch_item.batch_id, available_quantity))

                        logger.debug(
                            f"Batch {batch_item.batch_id} ({batch_item.batch.batch_number}): Reduced {available_quantity}, now {batch_item.quantity}")

                        log = InventoryLog(
                            medicine_id=medicine_id,
                            batch_id=batch_item.batch_id,
                            change_type='dispense',
                            quantity=-available_quantity,
                            performed_by=session.get('user_id'),
                            note=f'Tạo đơn thuốc ID {new_prescription.id} cho {patient.full_name}: {medicine.name or "ID " + str(medicine_id)} ({available_quantity} {medicine.unit or "N/A"}) từ lô {batch_item.batch.batch_number}'
                        )
                        db.session.add(log)

                    if remaining_quantity > 0:
                        flash(
                            f'Không đủ số lượng thuốc {medicine.name or "ID " + str(medicine_id)} trong kho! Còn thiếu {remaining_quantity} {medicine.unit or "N/A"}.',
                            'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))
                    new_item = PrescriptionItem(
                        prescription_id=new_prescription.id,
                        medicine_id=medicine_id,
                        batch_id=allocated_batches[0][0],
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        quantity=quantity
                    )
                    db.session.add(new_item)

                db.session.commit()
                flash('Gửi đơn thuốc đến dược sĩ thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating prescription: {str(e)}")
                flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('prescriptions'))

        try:
            patients = Patient.query.all()

            stock_subquery = db.session.query(
                MedicineBatchItem.medicine_id,
                func.coalesce(func.sum(MedicineBatchItem.quantity), 0).label('total_stock')
            ).join(
                MedicineBatch,
                MedicineBatchItem.batch_id == MedicineBatch.id
            ).filter(
                MedicineBatchItem.quantity > 0,
                MedicineBatch.is_active == True,
                MedicineBatchItem.expiration_date > datetime.now().date()
            ).group_by(MedicineBatchItem.medicine_id).subquery()

            available_medicines = db.session.query(
                Medicine.id,
                Medicine.name,
                Medicine.unit,
                stock_subquery.c.total_stock
            ).join(
                stock_subquery,
                Medicine.id == stock_subquery.c.medicine_id
            ).all()

            available_medicines = [
                {
                    'id': med.id,
                    'name': med.name or f'Thuốc ID {med.id}',
                    'unit': med.unit or 'N/A',
                    'total_stock': int(med.total_stock)
                } for med in available_medicines
            ]

            logger.debug(f"Available medicines: {available_medicines}")
            return render_template('add_prescription.html', patients=patients, available_medicines=available_medicines)
        except Exception as e:
            logger.error(f"Error loading add prescription form: {str(e)}")
            flash(f'Có lỗi khi tải form tạo đơn thuốc: {str(e)}', 'error')
            return render_template('add_prescription.html', patients=[], available_medicines=[])

    @app.route('/prescriptions/<int:prescription_id>/dispense', methods=['POST'])
    @login_required
    @role_required(['pharmacist', 'admin'])
    def dispense_prescription(prescription_id):
        try:
            prescription = Prescription.query.get_or_404(prescription_id)
            if prescription.status != 'pending':
                flash('Đơn thuốc đã được xử lý hoặc hủy!', 'error')
                return redirect(url_for('prescriptions'))

            for item in prescription.items:
                medicine = Medicine.query.get(item.medicine_id)
                if not medicine:
                    flash(f'Thuốc ID {item.medicine_id} không tồn tại!', 'error')
                    return redirect(url_for('prescriptions'))

                batch = MedicineBatch.query.get(item.batch_id)
                log = InventoryLog(
                    medicine_id=item.medicine_id,
                    batch_id=item.batch_id,
                    change_type='dispense',
                    quantity=0,
                    performed_by=session.get('user_id'),
                    note=f'Cấp phát thuốc {medicine.name or "ID " + str(item.medicine_id)} ({item.quantity} {medicine.unit or "N/A"}) cho {prescription.patient.full_name if prescription.patient else "N/A"} từ lô {batch.batch_number if batch else "N/A"}'
                )
                db.session.add(log)

            prescription.status = 'dispensed'
            db.session.commit()
            flash('Cấp phát thuốc thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error dispensing prescription: {str(e)}")
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('prescriptions'))

    @app.route('/prescriptions/<int:prescription_id>/undispense', methods=['POST'])
    @login_required
    @role_required(['pharmacist', 'admin'])
    def undispense_prescription(prescription_id):
        try:
            prescription = Prescription.query.get_or_404(prescription_id)
            if prescription.status != 'pending':
                flash('Chỉ có thể hủy cấp phát cho đơn thuốc đang chờ cấp phát!', 'error')
                return redirect(url_for('prescriptions'))

            for item in prescription.items:
                batch_item = MedicineBatchItem.query.filter_by(
                    batch_id=item.batch_id,
                    medicine_id=item.medicine_id
                ).first()
                if not batch_item:
                    flash(f'Lô thuốc cho thuốc ID {item.medicine_id} không tồn tại!', 'error')
                    db.session.rollback()
                    return redirect(url_for('prescriptions'))

                batch_item.quantity += item.quantity
                logger.debug(f"Restored Batch {item.batch_id}: Added {item.quantity}, now {batch_item.quantity}")

            prescription.status = 'cancelled'
            db.session.commit()
            flash('Hủy cấp phát thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling prescription: {str(e)}")
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('prescriptions'))

    @app.route('/prescriptions/<int:prescription_id>/details', methods=['GET'])
    @login_required
    @role_required(['doctor', 'pharmacist', 'admin'])
    def prescription_details(prescription_id):
        try:
            prescription = Prescription.query.options(
                joinedload(Prescription.patient),
                joinedload(Prescription.doctor),
                joinedload(Prescription.items).joinedload(PrescriptionItem.medicine),
                joinedload(Prescription.items).joinedload(PrescriptionItem.batch)
            ).get_or_404(prescription_id)
            if prescription.status == 'cancelled':
                flash('Đơn thuốc đã bị hủy và không thể xem chi tiết!', 'error')
                return redirect(url_for('patients'))
            return render_template('prescription_details.html', prescription=prescription)
        except Exception as e:
            logger.error(f"Error loading prescription details: {str(e)}")
            flash(f'Có lỗi khi tải chi tiết đơn thuốc: {str(e)}', 'error')
            return redirect(url_for('patients'))
