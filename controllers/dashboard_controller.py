from flask import render_template, flash, redirect, url_for
from controllers.auth_controller import login_required, role_required
from models import Prescription, PrescriptionItem, MedicineBatch, Medicine, MedicineBatchItem, Patient
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64


# Chuyển biểu đồ Matplotlib thành hình ảnh
def generate_base64_plot(fig):
    try:
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        plt.close(fig)
        return ""


# Số đơn thuốc theo ngày (7 ngày gần nhất)
def generate_prescription_trend():
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        data = db.session.query(
            func.date(Prescription.created_at).label('date'),
            func.count().label('count')
        ).filter(
            Prescription.created_at >= start_date
        ).group_by(
            func.date(Prescription.created_at)
        ).all()

        dates = [start_date + timedelta(days=i) for i in range(7)]
        counts = [0] * 7
        for d in data:
            if d.date:
                date_index = (d.date - start_date).days
                if 0 <= date_index < 7:
                    counts[date_index] = d.count

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar([d.strftime('%d/%m') for d in dates], counts, color='#1e88e5')
        ax.set_title('Số đơn thuốc theo ngày', fontsize=14, pad=15)
        ax.set_xlabel('Ngày', fontsize=12)
        ax.set_ylabel('Số đơn', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        return generate_base64_plot(fig)
    except Exception as e:
        return ""


# Biểu đồ tròn: Tỷ lệ đơn chưa hoàn thành
def generate_pending_ratio():
    try:
        total = db.session.query(func.count(Prescription.id)).scalar() or 0
        pending = db.session.query(func.count(Prescription.id)).filter_by(status='pending').scalar() or 0

        labels = ['Chưa hoàn thành', 'Đã xử lý']
        sizes = [pending, total - pending] if total > 0 else [0, 1]
        colors = ['#1e88e5', '#90caf9']

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Tỷ lệ đơn chưa hoàn thành', fontsize=14, pad=15)
        ax.axis('equal')
        return generate_base64_plot(fig)
    except Exception as e:
        return ""


# Số thuốc tồn kho nhiều nhất
def generate_stock_levels():
    try:
        top_medicines = db.session.query(
            Medicine.id,
            Medicine.name,
            func.coalesce(func.sum(MedicineBatchItem.quantity), 0).label('total_stock')
        ).outerjoin(
            MedicineBatchItem, Medicine.id == MedicineBatchItem.medicine_id
        ).outerjoin(
            MedicineBatch, MedicineBatchItem.batch_id == MedicineBatch.id
        ).filter(
            (MedicineBatch.is_active == True) | (MedicineBatch.is_active.is_(None)),
            (MedicineBatchItem.expiration_date > datetime.now().date()) | (MedicineBatchItem.expiration_date.is_(None))
        ).group_by(
            Medicine.id
        ).order_by(
            func.sum(MedicineBatchItem.quantity).desc()
        ).limit(5).all()

        names = [m.name or f"ID {m.id}" for m in top_medicines]
        stocks = [m.total_stock for m in top_medicines]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(names, stocks, color='#1e88e5')
        ax.set_title('Số thuốc tồn kho nhiều nhất', fontsize=14, pad=15)
        ax.set_xlabel('Thuốc', fontsize=12)
        ax.set_ylabel('Tồn kho', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        return generate_base64_plot(fig)
    except Exception as e:
        return ""


# Số thuốc được kê đơn nhiều nhất
def generate_top_medicines():
    try:
        top_meds = db.session.query(
            Medicine.name,
            func.count(PrescriptionItem.id).label('count')
        ).outerjoin(
            PrescriptionItem, Medicine.id == PrescriptionItem.medicine_id
        ).group_by(
            Medicine.id
        ).order_by(
            func.count(PrescriptionItem.id).desc()
        ).limit(5).all()

        names = [m.name or "Không xác định" for m in top_meds]
        counts = [m.count for m in top_meds]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(names, counts, color='#1e88e5')
        ax.set_title('Số thuốc được kê đơn nhiều nhất', fontsize=14, pad=15)
        ax.set_xlabel('Số lần kê', fontsize=12)
        ax.set_ylabel('Thuốc', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.invert_yaxis()
        return generate_base64_plot(fig)
    except Exception as e:
        return ""


# Trạng thái đơn thuốc
def generate_status_distribution():
    try:
        status_counts = db.session.query(
            Prescription.status,
            func.count().label('count')
        ).group_by(
            Prescription.status
        ).all()
        labels = [s.status.capitalize() for s in status_counts] if status_counts else ['No Data']
        sizes = [s.count for s in status_counts] if status_counts else [1]
        colors = ['#1e88e5', '#90caf9', '#ffcc80']

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Trạng thái đơn thuốc', fontsize=14, pad=15)
        ax.axis('equal')
        return generate_base64_plot(fig)
    except Exception as e:
        return ""


# Số lượng thuốc sắp hết hạn trong 30 ngày
def generate_expiring_medicines():
    try:
        end_date = datetime.now().date() + timedelta(days=30)
        expiring_meds = db.session.query(
            Medicine.name,
            func.sum(MedicineBatchItem.quantity).label('total_quantity')
        ).join(
            MedicineBatchItem, Medicine.id == MedicineBatchItem.medicine_id
        ).join(
            MedicineBatch, MedicineBatchItem.batch_id == MedicineBatch.id
        ).filter(
            MedicineBatch.is_active == True,
            MedicineBatchItem.expiration_date <= end_date,
            MedicineBatchItem.expiration_date > datetime.now().date()
        ).group_by(
            Medicine.id
        ).order_by(
            func.sum(MedicineBatchItem.quantity).desc()
        ).limit(5).all()

        names = [m.name or "Không xác định" for m in expiring_meds]
        quantities = [m.total_quantity for m in expiring_meds]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(names, quantities, color='#e53935')
        ax.set_title('Số lượng thuốc sắp hết hạn trong 30 ngày', fontsize=14, pad=15)
        ax.set_xlabel('Thuốc', fontsize=12)
        ax.set_ylabel('Số lượng', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        return generate_base64_plot(fig)
    except Exception as e:
        return ""


def register_dashboard_routes(app):
    @app.route('/')
    def index():
        return redirect(url_for('dashboard'))

    @app.route('/dashboard')
    @login_required
    @role_required(['doctor', 'pharmacist', 'admin'])
    def dashboard():
        try:
            total_patients = db.session.query(func.count()).select_from(Patient).scalar() or 0
            total_medicines = db.session.query(
                func.coalesce(func.sum(MedicineBatchItem.quantity), 0)
            ).join(
                MedicineBatch
            ).filter(
                MedicineBatch.is_active == True,
                MedicineBatchItem.expiration_date > datetime.now().date()
            ).scalar() or 0
            today_prescriptions = Prescription.query.filter(
                func.date(Prescription.created_at) == datetime.now().date()
            ).count() or 0

            prescription_trend = generate_prescription_trend()
            pending_ratio = generate_pending_ratio()
            stock_levels = generate_stock_levels()
            top_medicines_chart = generate_top_medicines()
            status_distribution = generate_status_distribution()
            expiring_medicines = generate_expiring_medicines()

            if not all([prescription_trend, pending_ratio, stock_levels, top_medicines_chart, status_distribution,
                        expiring_medicines]):
                flash('Không thể tải một số biểu đồ do lỗi dữ liệu', 'warning')

            return render_template(
                'dashboard.html',
                total_patients=total_patients,
                total_medicines=total_medicines,
                today_prescriptions=today_prescriptions,
                prescription_trend=prescription_trend,
                pending_ratio=pending_ratio,
                stock_levels=stock_levels,
                top_medicines_chart=top_medicines_chart,
                status_distribution=status_distribution,
                expiring_medicines=expiring_medicines
            )
        except Exception as e:
            flash(f'Có lỗi khi tải dashboard: {str(e)}', 'error')
            return render_template(
                'dashboard.html',
                total_patients=0,
                total_medicines=0,
                today_prescriptions=0,
                prescription_trend="",
                pending_ratio="",
                stock_levels="",
                top_medicines_chart="",
                status_distribution="",
                expiring_medicines=""
            )
