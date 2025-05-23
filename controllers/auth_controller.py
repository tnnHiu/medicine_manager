from flask import render_template, redirect, request, url_for, flash, session, abort
from app import app, db
from models.user import User
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from urllib.parse import urlparse, urljoin


# Hàm kiểm tra URL an toàn (nội bộ)
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


# Decorator để kiểm tra người dùng đã đăng nhập hay chưa
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'warning')
            # Thay vì sử dụng tham số next trong URL, lưu đường dẫn vào session
            session['next_url'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Decorator kiểm tra vai trò người dùng
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


@app.route('/login', methods=['GET', 'POST'])
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
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role.name

            flash(f'Chào mừng, {user.full_name}!', 'success')

            # Lấy đường dẫn tiếp theo từ session thay vì từ tham số URL
            next_page = session.pop('next_url', None)

            # Kiểm tra URL an toàn
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            return redirect(url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Bạn đã đăng xuất thành công', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')
