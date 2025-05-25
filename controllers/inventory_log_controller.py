from flask import render_template, redirect, url_for, flash
from controllers.auth_controller import login_required, role_required
from models import InventoryLog
from extensions import db


def register_inventory_log_routes(app):
    @app.route('/inventory-logs', methods=['GET'], endpoint='inventory_logs')
    @login_required
    @role_required(['admin', 'pharmacist'])
    def inventory_logs():
        logs_list = InventoryLog.query.order_by(InventoryLog.created_at.desc()).all()
        return render_template('inventory_logs.html',
                               logs=logs_list)
