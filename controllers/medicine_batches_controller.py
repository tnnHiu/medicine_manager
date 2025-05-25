from flask import render_template, redirect, request, url_for, flash, session, jsonify
from controllers.auth_controller import login_required, role_required
from models import MedicineBatch, MedicineBatchItem, Medicine, InventoryLog
from extensions import db
from datetime import datetime, date
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_medicine_batch_routes(app):
    @app.route('/medicine/search', methods=['GET'])
    @login_required
    def search_medicines():
        query = request.args.get('q', '')
        logger.debug(f"Search query: {query}")
        medicines = Medicine.query.filter(Medicine.name.ilike(f'%{query}%')).limit(10).all()
        result = {
            'results': [{'id': m.id, 'text': m.name, 'unit': m.unit or 'N/A'} for m in medicines],
            'status': 'success'
        }
        logger.debug(f"Search results: {result}")
        return jsonify(result), 200

    @app.route('/medicine-batches', methods=['GET'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def medicine_batches():
        batches = MedicineBatch.query.order_by(MedicineBatch.created_at.desc()).all()
        return render_template('medicine_batches.html', batches=batches)

    @app.route('/medicine-batches/add', methods=['GET', 'POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_medicine_batch():
        if request.method == 'POST':
            try:
                batch_number = request.form.get('batch_number', '').strip()
                supplier = request.form.get('supplier', '').strip() or None
                purchase_date = request.form.get('purchase_date')
                purchase_price = request.form.get('purchase_price')
                is_active = request.form.get('is_active') == 'on'

                if not batch_number:
                    flash('Mã lô là bắt buộc!', 'error')
                    return redirect(url_for('add_medicine_batch'))

                if MedicineBatch.query.filter_by(batch_number=batch_number).first():
                    flash('Mã lô đã tồn tại!', 'error')
                    return redirect(url_for('add_medicine_batch'))

                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
                purchase_price = float(purchase_price) if purchase_price else None

                new_batch = MedicineBatch(
                    batch_number=batch_number,
                    supplier=supplier,
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    is_active=is_active,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_batch)
                db.session.flush()

                medicine_ids = request.form.getlist('medicine_id[]')
                quantities = request.form.getlist('quantity[]')
                expiration_dates = request.form.getlist('expiration_date[]')
                notes = request.form.getlist('note[]')

                for i in range(len(medicine_ids)):
                    if not quantities[i] or not expiration_dates[i]:
                        continue

                    quantity = int(quantities[i])
                    if quantity <= 0:
                        continue

                    try:
                        expiration_date = datetime.strptime(expiration_dates[i], '%Y-%m-%d').date()
                    except ValueError:
                        continue

                    medicine = None
                    if medicine_ids[i]:
                        medicine = Medicine.query.get(int(medicine_ids[i]))

                    if not medicine:
                        continue

                    new_item = MedicineBatchItem(
                        medicine_id=medicine.id,
                        batch_id=new_batch.id,
                        quantity=quantity,
                        expiration_date=expiration_date
                    )
                    db.session.add(new_item)

                    item_log = InventoryLog(
                        medicine_id=medicine.id,
                        batch_id=new_batch.id,
                        change_type='import',
                        quantity=quantity,
                        performed_by=session.get('user_id'),
                        note=notes[
                                 i] or f'Nhập thuốc {medicine.name} ({quantity} {medicine.unit}) vào lô {batch_number}'
                    )
                    db.session.add(item_log)

                db.session.commit()
                flash('Thêm lô thuốc thành công!', 'success')
                return redirect(url_for('medicine_batches'))
            except Exception as e:
                db.session.rollback()
                flash(f'Có lỗi xảy ra: {str(e)}', 'error')
                return redirect(url_for('add_medicine_batch'))

        medicines = Medicine.query.order_by(Medicine.name).all()
        return render_template('add_medicine_batch.html', medicines=medicines)

    @app.route('/medicine-batches/<int:batch_id>/edit', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def edit_medicine_batch(batch_id):
        try:
            batch = MedicineBatch.query.get_or_404(batch_id)
            batch_number = request.form.get('batch_number', '').strip()
            supplier = request.form.get('supplier', '').strip() or None
            purchase_date = request.form.get('purchase_date')
            purchase_price = request.form.get('purchase_price')
            is_active = request.form.get('is_active') == 'on'

            if not batch_number:
                flash('Mã lô là bắt buộc!', 'error')
                return redirect(url_for('medicine_batches'))

            existing_batch = MedicineBatch.query.filter_by(batch_number=batch_number).first()
            if existing_batch and existing_batch.id != batch_id:
                flash('Mã lô đã tồn tại!', 'error')
                return redirect(url_for('medicine_batches'))

            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
            purchase_price = float(purchase_price) if purchase_price else None

            batch.batch_number = batch_number
            batch.supplier = supplier
            batch.purchase_date = purchase_date
            batch.purchase_price = purchase_price
            batch.is_active = is_active
            db.session.commit()
            flash('Cập nhật lô thuốc thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/<int:batch_id>/delete', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def delete_medicine_batch(batch_id):
        try:
            batch = MedicineBatch.query.get_or_404(batch_id)
            if batch.batch_items:
                flash('Không thể xóa lô có chứa thuốc!', 'error')
                return redirect(url_for('medicine_batches'))

            db.session.delete(batch)
            db.session.commit()
            flash('Xóa lô thuốc thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/<int:batch_id>/items', methods=['GET'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def medicine_batch_items(batch_id):
        batch = MedicineBatch.query.get_or_404(batch_id)
        medicines = Medicine.query.all()
        current_date = date.today().strftime('%Y-%m-%d')
        return render_template('medicine_batch_items.html', batch=batch, medicines=medicines, current_date=current_date)

    @app.route('/medicine-batches/<int:batch_id>/items/add', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_batch_item(batch_id):
        try:
            batch = MedicineBatch.query.get_or_404(batch_id)
            medicine_id = request.form.get('medicine_id', '').strip()
            quantity = request.form.get('quantity', '').strip()
            expiration_date = request.form.get('expiration_date', '').strip()
            note = request.form.get('note', '').strip()

            logger.debug(
                f"Form data: medicine_id={medicine_id}, quantity={quantity}, expiration_date={expiration_date}, note={note}")

            if not medicine_id or not quantity or not expiration_date:
                flash('Thuốc, số lượng và ngày hết hạn là bắt buộc!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    flash('Số lượng phải lớn hơn 0!', 'error')
                    return redirect(url_for('medicine_batch_items', batch_id=batch_id))
            except ValueError:
                flash('Số lượng không hợp lệ!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            try:
                expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Ngày hết hạn không hợp lệ!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            medicine = Medicine.query.get(int(medicine_id))
            if not medicine:
                flash('Thuốc không hợp lệ!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            new_item = MedicineBatchItem(
                medicine_id=medicine.id,
                batch_id=batch_id,
                quantity=quantity,
                expiration_date=expiration_date
            )
            db.session.add(new_item)

            item_log = InventoryLog(
                medicine_id=medicine.id,
                batch_id=batch_id,
                change_type='import',
                quantity=quantity,
                performed_by=session.get('user_id'),
                note=note or f'Nhập thuốc {medicine.name} ({quantity} {medicine.unit}) vào lô {batch.batch_number}'
            )
            db.session.add(item_log)

            db.session.commit()
            flash('Thêm thuốc vào lô thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in add_batch_item: {str(e)}")
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('medicine_batch_items', batch_id=batch_id))

    @app.route('/medicine-batches/<int:batch_id>/items/<int:item_id>/edit', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def edit_batch_item(batch_id, item_id):
        try:
            item = MedicineBatchItem.query.get_or_404(item_id)
            if item.batch_id != batch_id:
                flash('Mục không thuộc lô này!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            quantity = request.form.get('quantity')
            expiration_date = request.form.get('expiration_date')

            if not quantity or not expiration_date:
                flash('Số lượng và ngày hết hạn là bắt buộc!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            quantity = int(quantity)
            expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()

            if quantity <= 0:
                flash('Số lượng phải lớn hơn 0!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            change_quantity = quantity - item.quantity
            if change_quantity != 0:
                change_type = 'import' if change_quantity > 0 else 'dispense'
                log = InventoryLog(
                    medicine_id=item.medicine_id,
                    batch_id=batch_id,
                    change_type=change_type,
                    quantity=change_quantity,
                    performed_by=session.get('user_id'),
                    note=f'Sửa thuốc {item.medicine.name}: {item.quantity} → {quantity}, ngày hết hạn {item.expiration_date} → {expiration_date}'
                )
                db.session.add(log)

            item.quantity = quantity
            item.expiration_date = expiration_date
            db.session.commit()
            flash('Cập nhật thuốc trong lô thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('medicine_batch_items', batch_id=batch_id))

    @app.route('/medicine-batches/<int:batch_id>/items/<int:item_id>/delete', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def delete_batch_item(batch_id, item_id):
        try:
            item = MedicineBatchItem.query.get_or_404(item_id)
            if item.batch_id != batch_id:
                flash('Mục không thuộc lô này!', 'error')
                return redirect(url_for('medicine_batch_items', batch_id=batch_id))

            log = InventoryLog(
                medicine_id=item.medicine_id,
                batch_id=batch_id,
                change_type='dispense',
                quantity=-item.quantity,
                performed_by=session.get('user_id'),
                note=f'Xóa thuốc {item.medicine.name} ({item.quantity} {item.medicine.unit}) khỏi lô'
            )
            db.session.add(log)

            db.session.delete(item)
            db.session.commit()
            flash('Xóa thuốc khỏi lô thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('medicine_batch_items', batch_id=batch_id))
