from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if current_user.is_authenticated:
        # Перенаправление в зависимости от роли
        if current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'department_head':
            return redirect(url_for('department.dashboard'))
        return redirect(url_for('main.index'))
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # POST запрос - обработка формы
    email = request.form.get('email')
    password = request.form.get('password')
    remember = request.form.get('remember') == 'on'
    
    if not email or not password:
        flash('Email и пароль обязательны.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        flash('Неверный email или пароль.', 'danger')
        return redirect(url_for('auth.login'))
    
    if not user.is_active:
        flash('Ваш аккаунт заблокирован. Обратитесь к администратору.', 'danger')
        return redirect(url_for('auth.login'))
    
    login_user(user, remember=remember)
    flash(f'Добро пожаловать, {user.full_name}!', 'success')
    
    # Перенаправление после входа
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)
    
    # Перенаправление в зависимости от роли
    if user.role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'department_head':
        return redirect(url_for('department.dashboard'))
    
    return redirect(url_for('main.index'))


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """Профиль пользователя"""
    return render_template('auth/profile.html', user=current_user)


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Изменить пароль"""
    if request.method == 'GET':
        return render_template('auth/change_password.html')
    
    # POST запрос - обработка формы
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Валидация
    if not old_password or not new_password or not confirm_password:
        flash('Все поля обязательны для заполнения.', 'danger')
        return redirect(url_for('auth.change_password'))
    
    if not current_user.check_password(old_password):
        flash('Неверный текущий пароль.', 'danger')
        return redirect(url_for('auth.change_password'))
    
    if len(new_password) < 6:
        flash('Новый пароль должен быть не менее 6 символов.', 'warning')
        return redirect(url_for('auth.change_password'))
    
    if new_password != confirm_password:
        flash('Новый пароль и подтверждение не совпадают.', 'danger')
        return redirect(url_for('auth.change_password'))
    
    if old_password == new_password:
        flash('Новый пароль должен отличаться от текущего.', 'warning')
        return redirect(url_for('auth.change_password'))
    
    # Изменить пароль
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Пароль успешно изменен.', 'success')
    return redirect(url_for('auth.profile'))


@bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактировать профиль"""
    if request.method == 'GET':
        return render_template('auth/edit_profile.html', user=current_user)
    
    # POST запрос - обработка формы
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    
    # Валидация
    if not full_name or not email:
        flash('ФИО и email обязательны.', 'danger')
        return redirect(url_for('auth.edit_profile'))
    
    # Проверка email на уникальность
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != current_user.id:
        flash('Email уже используется другим пользователем.', 'danger')
        return redirect(url_for('auth.edit_profile'))
    
    # Обновить данные
    current_user.full_name = full_name
    current_user.email = email
    db.session.commit()
    
    flash('Профиль успешно обновлен.', 'success')
    return redirect(url_for('auth.profile'))