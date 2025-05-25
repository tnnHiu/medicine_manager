from flask import render_template, redirect, request, url_for, flash, session
from controllers.auth_controller import login_required, role_required
from models import MedicineBatch, MedicineBatchItem, Medicine, InventoryLog
from extensions import db
from datetime import datetime
import uuid

def register_medicine_batch_routes(app):
    @app.route('/medicine-batches', methods=['GET'], endpoint='medicine_batches')
    @login_required
    @role_required(['admin', 'pharmacist'])
    def medicine_batches():
        batches_list = MedicineBatch.query.all()
        return render_template('medicine_batches.html',
                              batches=batches_list)

    @app.route('/medicine-batches/add', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_medicine_batch():
        try:
            # Lấy dữ liệu lô thuốc từ form
            batch_number = request.form.get('batch_number')
            supplier = request.form.get('supplier')
            purchase_date = request.form.get('purchase_date')
            purchase_price = request.form.get('purchase_price')
            is_active = request.form.get('is_active') == 'on'

            # Kiểm tra dữ liệu đầu vào
            if not batch_number:
                flash('Mã lô là bắt buộc!', 'error')
                return redirect(url_for('medicine_batches'))

            # Kiểm tra mã lô đã tồn tại chưa
            if MedicineBatch.query.filter_by(batch_number=batch_number).first():
                flash('Mã lô đã tồn tại!', 'error')
                return redirect(url_for('medicine_batches'))

            # Chuyển đổi purchase_date
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
            purchase_price = float(purchase_price) if purchase_price else None

            # Tạo lô thuốc mới
            new_batch = MedicineBatch(
                batch_number=batch_number,
                supplier=supplier,
                purchase_date=purchase_date,
                purchase_price=purchase_price,
                is_active=is_active
            )

            db.session.add(new_batch)
            db.session.flush()  # Lấy batch_id trước khi commit

            # Ghi log cho hành động thêm lô
            batch_log = InventoryLog(
                medicine_id=None,
                batch_id=new_batch.id,
                change_type='import',
                quantity=0,
                performed_by=session.get('user_id'),
                note=f'Thêm lô thuốc mới: {batch_number}'
            )
            db.session.add(batch_log)

            # Xử lý danh sách thuốc trong lô
            medicine_names = request.form.getlist('medicine_name')
            units = request.form.getlist('unit')
            quantities = request.form.getlist('quantity')
            expiration_dates = request.form.getlist('expiration_date')
            notes = request.form.getlist('note')

            for i in range(len(medicine_names)):
                if not medicine_names[i] or not units[i] or not quantities[i] or not expiration_dates[i]:
                    continue  # Bỏ qua nếu thiếu dữ liệu

                medicine_name = medicine_names[i].strip()
                unit = units[i].strip()
                quantity = int(quantities[i])
                expiration_date = datetime.strptime(expiration_dates[i], '%Y-%m-%d').date()

                if quantity <= 0:
                    continue  # Bỏ qua nếu số lượng không hợp lệ

                # Tìm hoặc tạo thuốc
                medicine = Medicine.query.filter_by(name=medicine_name).first()
                if not medicine:
                    # Tạo thuốc mới với mã tự động
                    medicine = Medicine(
                        name=medicine_name,
                        code=f'MED-{uuid.uuid4().hex[:8]}',
                        unit=unit
                    )
                    db.session.add(medicine)
                    db.session.flush()

                # Tạo MedicineBatchItem
                new_item = MedicineBatchItem(
                    medicine_id=medicine.id,
                    batch_id=new_batch.id,
                    quantity=quantity,
                    expiration_date=expiration_date
                )

                # Ghi log cho thuốc
                item_log = InventoryLog(
                    medicine_id=medicine.id,
                    batch_id=new_batch.id,
                    change_type='import',
                    quantity=quantity,
                    performed_by=session.get('user_id'),
                    note=notes[i] or f'Nhập thuốc {medicine.name} ({medicine.unit}) vào lô {batch_number}'
                )

                db.session.add(new_item)
                db.session.add(item_log)

            # Lưu tất cả vào cơ sở dữ liệu
            db.session.commit()

            flash('Thêm lô thuốc và thuốc trong lô thành công!', 'success')
            return redirect(url_for('medicine_batches'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/edit/<int:batch_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def edit_medicine_batch(batch_id):
        try:
            # Tìm lô thuốc
            batch = MedicineBatch.query.get_or_404(batch_id)

            # Lấy dữ liệu từ form
            batch_number = request.form.get('batch_number')
            supplier = request.form.get('supplier')
            purchase_date = request.form.get('purchase_date')
            purchase_price = request.form.get('purchase_price')
            is_active = request.form.get('is_active') == 'on'

            # Kiểm tra dữ liệu đầu vào
            if not batch_number:
                flash('Mã lô là bắt buộc!', 'error')
                return redirect(url_for('medicine_batches'))

            # Kiểm tra mã lô đã tồn tại chưa (trừ chính lô này)
            existing_batch = MedicineBatch.query.filter_by(batch_number=batch_number).first()
            if existing_batch and existing_batch.id != batch_id:
                flash('Mã lô đã tồn tại!', 'error')
                return redirect(url_for('medicine_batches'))

            # Ghi log trước khi chỉnh sửa
            log = InventoryLog(
                medicine_id=None,
                batch_id=batch_id,
                change_type='import',
                quantity=0,
                performed_by=session.get('user_id'),
                note=f'Sửa thông tin lô thuốc: {batch.batch_number} → {batch_number}'
            )
            db.session.add(log)

            # Cập nhật thông tin
            batch.batch_number = batch_number
            batch.supplier = supplier
            batch.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
            batch.purchase_price = float(purchase_price) if purchase_price else None
            batch.is_active = is_active

            db.session.commit()

            flash('Cập nhật lô thuốc thành công!', 'success')
            return redirect(url_for('medicine_batches'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/delete/<int:batch_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def delete_medicine_batch(batch_id):
        try:
            # Tìm lô thuốc
            batch = MedicineBatch.query.get_or_404(batch_id)

            # Ghi log trước khi xóa
            log = InventoryLog(
                medicine_id=None,
                batch_id=batch_id,
                change_type='import',
                quantity=0,
                performed_by=session.get('user_id'),
                note=f'Xóa lô thuốc: {batch.batch_number}'
            )
            db.session.add(log)

            # Xóa lô thuốc (và các MedicineBatchItem liên quan do cascade)
            db.session.delete(batch)
            db.session.commit()

            flash('Xóa lô thuốc thành công!', 'success')
            return redirect(url_for('medicine_batches'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/<int:batch_id>/items/add', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def add_batch_item(batch_id):
        try:
            # Tìm lô thuốc
            batch = MedicineBatch.query.get_or_404(batch_id)

            # Lấy dữ liệu từ form
            medicine_name = request.form.get('medicine_name')
            unit = request.form.get('unit')
            quantity = request.form.get('quantity')
            expiration_date = request.form.get('expiration_date')
            note = request.form.get('note')

            # Kiểm tra dữ liệu đầu vào
            if not medicine_name or not unit or not quantity or not expiration_date:
                flash('Tên thuốc, đơn vị, số lượng và ngày hết hạn là bắt buộc!', 'error')
                return redirect(url_for('medicine_batches'))

            # Tìm hoặc tạo thuốc
            medicine_name = medicine_name.strip()
            unit = unit.strip()
            medicine = Medicine.query.filter_by(name=medicine_name).first()
            if not medicine:
                medicine = Medicine(
                    name=medicine_name,
                    code=f'MED-{uuid.uuid4().hex[:8]}',
                    unit=unit
                )
                db.session.add(medicine)
                db.session.flush()

            # Chuyển đổi dữ liệu
            quantity = int(quantity)
            expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()

            # Kiểm tra số lượng hợp lệ
            if quantity <= 0:
                flash('Số lượng phải lớn hơn 0!', 'error')
                return redirect(url_for('medicine_batches'))

            # Tạo MedicineBatchItem mới
            new_item = MedicineBatchItem(
                medicine_id=medicine.id,
                batch_id=batch_id,
                quantity=quantity,
                expiration_date=expiration_date
            )

            # Tạo InventoryLog
            new_log = InventoryLog(
                medicine_id=medicine.id,
                batch_id=batch_id,
                change_type='import',
                quantity=quantity,
                performed_by=session.get('user_id'),
                note=note or f'Nhập thuốc {medicine.name} ({medicine.unit}) vào lô {batch.batch_number}'
            )

            db.session.add(new_item)
            db.session.add(new_log)
            db.session.commit()

            flash('Thêm thuốc vào lô và ghi log thành công!', 'success')
            return redirect(url_for('medicine_batches'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/<int:batch_id>/items/edit/<int:item_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def edit_batch_item(batch_id, item_id):
        try:
            # Tìm MedicineBatchItem
            item = MedicineBatchItem.query.get_or_404(item_id)

            # Kiểm tra batch_id
            if item.batch_id != batch_id:
                flash('Thuốc không thuộc lô này!', 'error')
                return redirect(url_for('medicine_batches'))

            # Lấy dữ liệu từ form
            quantity = request.form.get('quantity')
            expiration_date = request.form.get('expiration_date')

            # Kiểm tra dữ liệu đầu vào
            if not quantity or not expiration_date:
                flash('Số lượng và ngày hết hạn là bắt buộc!', 'error')
                return redirect(url_for('medicine_batches'))

            # Chuyển đổi dữ liệu
            quantity = int(quantity)
            expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()

            # Kiểm tra số lượng hợp lệ
            if quantity <= 0:
                flash('Số lượng phải lớn hơn 0!', 'error')
                return redirect(url_for('medicine_batches'))

            # Ghi log trước khi chỉnh sửa
            log = InventoryLog(
                medicine_id=item.medicine_id,
                batch_id=batch_id,
                change_type='import',
                quantity=quantity,
                performed_by=session.get('user_id'),
                note=f'Sửa thuốc {item.medicine.name} ({item.medicine.unit}) trong lô {item.batch.batch_number}: Số lượng {item.quantity} → {quantity}'
            )
            db.session.add(log)

            # Cập nhật thông tin
            item.quantity = quantity
            item.expiration_date = expiration_date

            db.session.commit()

            flash('Cập nhật thuốc trong lô thành công!', 'success')
            return redirect(url_for('medicine_batches'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicine_batches'))

    @app.route('/medicine-batches/<int:batch_id>/items/delete/<int:item_id>', methods=['POST'])
    @login_required
    @role_required(['admin', 'pharmacist'])
    def delete_batch_item(batch_id, item_id):
        try:
            # Tìm MedicineBatchItem
            item = MedicineBatchItem.query.get_or_404(item_id)

            # Kiểm tra batch_id
            if item.batch_id != batch_id:
                flash('Thuốc không thuộc lô này!', 'error')
                return redirect(url_for('medicine_batches'))

            # Ghi log trước khi xóa
            log = InventoryLog(
                medicine_id=item.medicine_id,
                batch_id=batch_id,
                change_type='import',
                quantity=0,
                performed_by=session.get('user_id'),
                note=f'Xóa thuốc {item.medicine.name} ({item.medicine.unit}) khỏi lô {item.batch.batch_number}'
            )
            db.session.add(log)

            # Xóa MedicineBatchItem
            db.session.delete(item)
            db.session.commit()

            flash('Xóa thuốc khỏi lô thành công!', 'success')
            return redirect(url_for('medicine_batches'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('medicine_batches'))