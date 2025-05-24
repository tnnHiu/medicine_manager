from flask import render_template, redirect, request, url_for, flash, session
from werkzeug.security import generate_password_hash
from controllers.auth_controller import login_required, role_required
from models import User
from extensions import db
from models.user import RoleEnum


def register_user_routes(app):
    @app.route('/users', endpoint='users')
    @login_required
    @role_required(['admin'])
    def users():
        users_list = User.query.all()
        return render_template('users.html',
                               users=users_list)

    @app.route('/user/add', methods=['POST'])
    @login_required
    @role_required(['admin'])
    def add_user():
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            full_name = request.form.get('full_name')
            role = request.form.get('role')

            if not username or not password or not role:
                flash('Tên tài khoản, mật khẩu và vai trò là bắt buộc!', 'error')
                return redirect(url_for('users'))
            if User.query.filter_by(username=username).first():
                flash('Tên tài khoản đã tồn tại!', 'error')
                return redirect(url_for('users'))
            if role not in [r.value for r in RoleEnum]:
                flash('Vai trò không hợp lệ!', 'error')
                return redirect(url_for('users'))
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                full_name=full_name,
                role=RoleEnum[role]
            )
            # Lưu vào cơ sở dữ liệu
            db.session.add(new_user)
            db.session.commit()
            flash('Thêm người dùng thành công!', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('users'))

    # ----------------------------------- edit -------------------------------------------
    @app.route('/users/edit/<int:user_id>', methods=['POST'])
    @login_required
    @role_required(['admin'])
    def edit_user(user_id):
        try:
            user = User.query.get_or_404(user_id)

            username = request.form.get('username')
            password = request.form.get('password')
            full_name = request.form.get('full_name')
            role = request.form.get('role')

            if not username or not role:
                flash('Tên tài khoản và vai trò là bắt buộc!', 'error')
                return redirect(url_for('users'))

            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                flash('Tên tài khoản đã tồn tại!', 'error')
                return redirect(url_for('users'))

            if role not in [r.value for r in RoleEnum]:
                flash('Vai trò không hợp lệ!', 'error')
                return redirect(url_for('users'))

            user.username = username
            if password:
                user.password_hash = generate_password_hash(password)
            user.full_name = full_name
            user.role = RoleEnum[role]

            # Lưu vào cơ sở dữ liệu
            db.session.commit()

            flash('Cập nhật người dùng thành công!', 'success')
            return redirect(url_for('users'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('users'))

    # ----------------------------------- delete -------------------------------------------

    @app.route('/users/delete/<int:user_id>', methods=['POST'])
    @login_required
    @role_required(['admin'])
    def delete_user(user_id):
        try:
            user = User.query.get_or_404(user_id)

            # Không cho phép xóa chính tài khoản đang đăng nhập
            if user.id == session.get('user_id'):
                flash('Không thể xóa tài khoản đang đăng nhập!', 'error')
                return redirect(url_for('users'))

            db.session.delete(user)
            db.session.commit()

            flash('Xóa người dùng thành công!', 'success')
            return redirect(url_for('users'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('users'))
