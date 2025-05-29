from flask import render_template, redirect, request, url_for, flash, session, make_response
from controllers.auth_controller import login_required, role_required
from models import Prescription, PrescriptionItem, Patient, MedicineBatch, Medicine, InventoryLog, MedicineBatchItem
from extensions import db
from datetime import datetime
import logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from io import BytesIO
from unidecode import unidecode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

VALID_CHANGE_TYPES = {'import', 'dispense'}


def register_prescription_routes(app):
    font_path = Path("C:/Windows/Fonts/times.ttf")
    if not font_path.exists():
        logger.error(f"Font file not found at {font_path}")
        raise FileNotFoundError(f"Font file not found at {font_path}")
    pdfmetrics.registerFont(TTFont("TimesNewRoman", font_path))

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
            flash(f'Co loi xay ra khi tai danh sach don thuoc: {str(e)}', 'error')
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
                    flash('Thong tin don thuoc khong hop le!', 'error')
                    return redirect(url_for('add_prescription'))

                patient = Patient.query.get(patient_id)
                if not patient:
                    flash('Benh nhan khong ton tai!', 'error')
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
                        flash(f'So luong thuoc thu {i + 1} khong hop le!', 'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    if not dosage or not frequency or not duration or quantity <= 0:
                        flash(f'Thong tin thuoc thu {i + 1} khong hop le!', 'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    medicine = Medicine.query.get(medicine_id)
                    if not medicine:
                        flash(f'Thuoc ID {medicine_id} khong ton tai!', 'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

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
                            f'Thuoc {medicine.name or "ID " + str(medicine_id)} khong co trong kho hoac khong co lo hoat dong/chua het han!',
                            'error')
                        db.session.rollback()
                        return redirect(url_for('add_prescription'))

                    if quantity > total_stock:
                        flash(
                            f'So luong yeu cau cho {medicine.name or "ID " + str(medicine_id)} ({quantity}) vuot qua ton kho ({total_stock})!',
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
                            f'Thuoc {medicine.name or "ID " + str(medicine_id)} khong co lo nao kha dung voi so luong lon hon 0!',
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
                            note=f'Tao don thuoc ID {new_prescription.id} cho {patient.full_name}: {medicine.name or "ID " + str(medicine_id)} ({available_quantity} {medicine.unit or "N/A"}) tu lo {batch_item.batch.batch_number}'
                        )
                        db.session.add(log)

                    if remaining_quantity > 0:
                        flash(
                            f'Khong du so luong thuoc {medicine.name or "ID " + str(medicine_id)} trong kho! Con thieu {remaining_quantity} {medicine.unit or "N/A"}.',
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
                flash('Gui don thuoc den duoc si thanh cong!', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating prescription: {str(e)}")
                flash(f'Co loi xay ra: {str(e)}', 'error')
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
                    'name': med.name or f'Thuoc ID {med.id}',
                    'unit': med.unit or 'N/A',
                    'total_stock': int(med.total_stock)
                } for med in available_medicines
            ]

            logger.debug(f"Available medicines: {available_medicines}")
            return render_template('add_prescription.html', patients=patients, available_medicines=available_medicines)
        except Exception as e:
            logger.error(f"Error loading add prescription form: {str(e)}")
            flash(f'Co loi khi tai form tao don thuoc: {str(e)}', 'error')
            return render_template('add_prescription.html', patients=[], available_medicines=[])

    @app.route('/prescriptions/<int:prescription_id>/dispense', methods=['POST'])
    @login_required
    @role_required(['pharmacist', 'admin'])
    def dispense_prescription(prescription_id):
        try:
            prescription = Prescription.query.get_or_404(prescription_id)
            if prescription.status != 'pending':
                flash('Don thuoc da duoc xu ly hoac huy!', 'error')
                return redirect(url_for('prescriptions'))

            for item in prescription.items:
                medicine = Medicine.query.get(item.medicine_id)
                if not medicine:
                    flash(f'Thuoc ID {item.medicine_id} khong ton tai!', 'error')
                    return redirect(url_for('prescriptions'))

                batch = MedicineBatch.query.get(item.batch_id)
                log = InventoryLog(
                    medicine_id=item.medicine_id,
                    batch_id=item.batch_id,
                    change_type='dispense',
                    quantity=0,
                    performed_by=session.get('user_id'),
                    note=f'Cap phat thuoc {medicine.name or "ID " + str(item.medicine_id)} ({item.quantity} {medicine.unit or "N/A"}) cho {prescription.patient.full_name if prescription.patient else "N/A"} tu lo {batch.batch_number if batch else "N/A"}'
                )
                db.session.add(log)

            prescription.status = 'dispensed'
            db.session.commit()
            flash('Cap phat thuoc thanh cong!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error dispensing prescription: {str(e)}")
            flash(f'Co loi xay ra: {str(e)}', 'error')
        return redirect(url_for('prescriptions'))

    @app.route('/prescriptions/<int:prescription_id>/undispense', methods=['POST'])
    @login_required
    @role_required(['pharmacist', 'admin'])
    def undispense_prescription(prescription_id):
        try:
            prescription = Prescription.query.get_or_404(prescription_id)
            if prescription.status != 'pending':
                flash('Chi co the huy cap phat cho don thuoc dang cho cap phat!', 'error')
                return redirect(url_for('prescriptions'))

            for item in prescription.items:
                batch_item = MedicineBatchItem.query.filter_by(
                    batch_id=item.batch_id,
                    medicine_id=item.medicine_id
                ).first()
                if not batch_item:
                    flash(f'Lo thuoc cho thuoc ID {item.medicine_id} khong ton tai!', 'error')
                    db.session.rollback()
                    return redirect(url_for('prescriptions'))

                batch_item.quantity += item.quantity
                logger.debug(f"Restored Batch {item.batch_id}: Added {item.quantity}, now {batch_item.quantity}")

            prescription.status = 'cancelled'
            db.session.commit()
            flash('Huy cap phat thanh cong!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling prescription: {str(e)}")
            flash(f'Co loi xay ra: {str(e)}', 'error')
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
                flash('Don thuoc da bi huy va khong the xem chi tiet!', 'error')
                return redirect(url_for('patients'))
            return render_template('prescription_details.html', prescription=prescription)
        except Exception as e:
            logger.error(f"Error loading prescription details: {str(e)}")
            flash(f'Co loi khi tai chi tiet don thuoc: {str(e)}', 'error')
            return redirect(url_for('patients'))

    @app.route('/prescriptions/<int:prescription_id>/export_pdf', methods=['GET'])
    @login_required
    @role_required(['doctor', 'pharmacist', 'admin'])
    def export_prescription_pdf(prescription_id):
        try:
            prescription = Prescription.query.options(
                joinedload(Prescription.patient),
                joinedload(Prescription.doctor),
                joinedload(Prescription.items).joinedload(PrescriptionItem.medicine),
                joinedload(Prescription.items).joinedload(PrescriptionItem.batch)
            ).get_or_404(prescription_id)

            if prescription.status == 'cancelled':
                flash('Don thuoc da bi huy va khong the xuat PDF!', 'error')
                return redirect(url_for('prescription_details', prescription_id=prescription_id))

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            margin = 20 * mm
            y_position = height - margin

            p.setFont("TimesNewRoman", 18)
            p.drawCentredString(width / 2, y_position, unidecode(f"Don thuoc #{prescription.id}"))
            y_position -= 10 * mm
            p.setFont("TimesNewRoman", 12)
            p.drawCentredString(width / 2, y_position,
                                unidecode(f"Ngay xuat: {prescription.created_at.strftime('%d/%m/%Y')}"))
            y_position -= 10 * mm

            p.setFont("TimesNewRoman", 14)
            p.drawString(margin, y_position, unidecode("Thong tin don thuoc"))
            y_position -= 7 * mm
            p.setFont("TimesNewRoman", 10)
            p.drawString(margin, y_position, unidecode(f"Benh nhan: {prescription.patient.full_name or 'N/A'}"))
            y_position -= 5 * mm
            p.drawString(margin, y_position, unidecode(f"CCCD: {prescription.patient.id_card or 'N/A'}"))
            y_position -= 5 * mm
            p.drawString(margin, y_position,
                         unidecode(f"Bac si: {prescription.doctor.full_name if prescription.doctor else 'N/A'}"))
            y_position -= 5 * mm
            p.drawString(margin, y_position,
                         unidecode(f"Ngay tao: {prescription.created_at.strftime('%d/%m/%Y %H:%M')}"))
            y_position -= 5 * mm
            status = "Cho cap phat" if prescription.status == "pending" else "Da cap phat"
            p.drawString(margin, y_position, unidecode(f"Trang thai: {status}"))
            y_position -= 10 * mm

            p.setFont("TimesNewRoman", 14)
            p.drawString(margin, y_position, unidecode("Danh sach thuoc"))
            y_position -= 7 * mm

            # Table data
            data = [[unidecode("Ten thuoc"), unidecode("Lo thuoc"), unidecode("So luong")]]
            if prescription.items:
                for item in prescription.items:
                    medicine_name = unidecode(f"{item.medicine.name or 'N/A'} ({item.medicine.unit or 'N/A'})")
                    batch_number = unidecode(item.batch.batch_number if item.batch else 'N/A')
                    quantity = str(item.quantity) if item.quantity is not None else 'N/A'
                    data.append([medicine_name, batch_number, quantity])
            else:
                data.append([unidecode("Khong co thuoc trong don"), '', '', '', '', ''])

            # Table style
            table = Table(data, colWidths=[100 * mm, 60 * mm, 30 * mm, 60 * mm, 60 * mm, 30 * mm])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'TimesNewRoman', 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))

            table_height = len(data) * 15 * mm
            if y_position - table_height < margin:
                p.showPage()
                y_position = height - margin
                p.setFont("TimesNewRoman", 14)
                p.drawString(margin, y_position, unidecode("Danh sach thuoc (tiep theo)"))
                y_position -= 7 * mm

            table.wrapOn(p, width - 2 * margin, height)
            table.drawOn(p, margin, y_position - table_height)
            y_position -= table_height + 10 * mm

            p.setFont("TimesNewRoman", 10)
            p.drawCentredString(width / 2, margin, unidecode(
                f"He thong Quan ly Thuoc - Xuat ngay {prescription.created_at.strftime('%d/%m/%Y')}"))

            p.showPage()
            p.save()
            buffer.seek(0)

            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=prescription_{prescription_id}.pdf'

            logger.debug(f"Exported PDF for prescription ID {prescription_id}")
            return response
        except Exception as e:
            logger.error(f"Error exporting PDF for prescription {prescription_id}: {str(e)}")
            flash(f'Co loi khi xuat PDF: {str(e)}', 'error')
            return redirect(url_for('prescription_details', prescription_id=prescription_id))
