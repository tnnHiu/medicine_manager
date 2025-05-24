from flask import render_template, redirect, request, url_for, flash, session
from werkzeug.security import check_password_hash
from functools import wraps
from urllib.parse import urlparse, urljoin
from models.user import User


# --------- Tiện ích bảo mật ---------
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# --------- Decorators ---------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'warning')
            session['next_url'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Bạn không có quyền truy cập trang này', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# --------- Routes ---------
def register_auth_routes(app):
    @app.route('/login', methods=['GET', 'POST'], endpoint='login')
    def login():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Vui lòng nhập đầy đủ thông tin đăng nhập', 'danger')
                return render_template('login.html')

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session.update({
                    'user_id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role.name,
                })
                flash(f'Chào mừng, {user.full_name}!', 'success')

                next_page = session.pop('next_url', None)
                return redirect(next_page) if next_page and is_safe_url(next_page) else redirect(url_for('dashboard'))

            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'danger')

        return render_template('login.html')

    @app.route('/logout', endpoint="logout")
    def logout():
        session.clear()
        flash('Bạn đã đăng xuất thành công', 'success')
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
