from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from app import db
from app.models import (Group, Student, Attendance, StandardResult, Assignment, 
                        Standard, Module, Theme, Statement)
from app.utils import calculate_student_rating, calculate_points_from_result
from sqlalchemy import func, and_

from app.forms import StatementForm  
from werkzeug.utils import secure_filename  
from app.utils import get_upload_path  

bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def teacher_required(f):
    """Декоратор для проверки прав преподавателя"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['teacher', 'admin']:
            flash('Доступ запрещен. Требуются права преподавателя.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ===================== ГЛАВНАЯ ПАНЕЛЬ =====================

@bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Главная панель преподавателя"""
    # Получить группы преподавателя
    if current_user.role == 'admin':
        groups = Group.query.all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).all()
    
    # Статистика
    total_students = 0
    total_groups = len(groups)
    avg_attendance = 0
    passed_count = 0
    
    for group in groups:
        students = Student.query.filter_by(group_id=group.id).all()
        total_students += len(students)
        
        for student in students:
            avg_attendance += student.get_attendance_percentage()
            rating = calculate_student_rating(student.id)
            if rating['passed']:
                passed_count += 1
    
    if total_students > 0:
        avg_attendance = round(avg_attendance / total_students, 1)
        pass_rate = round((passed_count / total_students * 100), 1)
    else:
        pass_rate = 0
    
    # Последние задания
    recent_assignments = Assignment.query.filter_by(
        created_by=current_user.id,
        status='назначено'
    ).order_by(Assignment.deadline.asc()).limit(5).all()
    
    stats = {
        'total_students': total_students,
        'total_groups': total_groups,
        'avg_attendance': avg_attendance,
        'pass_rate': pass_rate,
        'passed_count': passed_count,
        'failed_count': total_students - passed_count
    }
    
    return render_template('teacher/dashboard.html',
                         groups=groups,
                         stats=stats,
                         recent_assignments=recent_assignments)


# ===================== ГРУППЫ =====================

@bp.route('/groups')
@login_required
@teacher_required
def groups():
    """Список групп преподавателя"""
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    # Добавить статистику для каждой группы
    groups_data = []
    for group in groups:
        students = Student.query.filter_by(group_id=group.id).all()
        
        total_attendance = 0
        total_rating = 0
        passed = 0
        
        for student in students:
            total_attendance += student.get_attendance_percentage()
            rating = calculate_student_rating(student.id)
            total_rating += rating['total']
            if rating['passed']:
                passed += 1
        
        students_count = len(students)
        avg_attendance = round(total_attendance / students_count, 1) if students_count > 0 else 0
        avg_rating = round(total_rating / students_count, 1) if students_count > 0 else 0
        pass_rate = round((passed / students_count * 100), 1) if students_count > 0 else 0
        
        groups_data.append({
            'group': group,
            'students_count': students_count,
            'avg_attendance': avg_attendance,
            'avg_rating': avg_rating,
            'pass_rate': pass_rate
        })
    
    return render_template('teacher/groups.html', groups_data=groups_data)


@bp.route('/groups/<int:group_id>')
@login_required
@teacher_required
def group_details(group_id):
    """Детали группы со списком студентов"""
    group = Group.query.get_or_404(group_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and group.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.groups'))
    
    students = Student.query.filter_by(group_id=group_id).order_by(Student.full_name).all()
    
    students_data = []
    for student in students:
        rating = calculate_student_rating(student.id)
        attendance_pct = student.get_attendance_percentage()
        
        students_data.append({
            'student': student,
            'rating': rating,
            'attendance_percentage': attendance_pct
        })
    
    # Сортировка
    sort_by = request.args.get('sort', 'name')
    if sort_by == 'rating':
        students_data.sort(key=lambda x: x['rating']['total'], reverse=True)
    elif sort_by == 'attendance':
        students_data.sort(key=lambda x: x['attendance_percentage'], reverse=True)
    
    return render_template('teacher/group_details.html',
                         group=group,
                         students_data=students_data,
                         sort_by=sort_by)


# ===================== ПОСЕЩАЕМОСТЬ =====================

@bp.route('/attendance')
@login_required
@teacher_required
def attendance():
    """Страница отметки посещаемости"""
    # Получить группы
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    # Выбранная группа
    selected_group_id = request.args.get('group_id', type=int)
    selected_date = request.args.get('date', date.today().isoformat())
    
    students_data = []
    selected_group = None
    
    if selected_group_id:
        selected_group = Group.query.get(selected_group_id)
        if selected_group:
            # Проверка доступа
            if current_user.role == 'teacher' and selected_group.teacher_id != current_user.id:
                flash('Доступ запрещен.', 'danger')
                return redirect(url_for('teacher.attendance'))
            
            try:
                attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except ValueError:
                attendance_date = date.today()
            
            students = Student.query.filter_by(group_id=selected_group_id).order_by(Student.full_name).all()
            
            for student in students:
                # Найти существующую запись посещаемости
                attendance_record = Attendance.query.filter_by(
                    student_id=student.id,
                    date=attendance_date
                ).first()
                
                students_data.append({
                    'student': student,
                    'attendance': attendance_record
                })
    
    return render_template('teacher/attendance.html',
                         groups=groups,
                         selected_group=selected_group,
                         selected_date=selected_date,
                         students_data=students_data)


@bp.route('/attendance/mark', methods=['POST'])
@login_required
@teacher_required
def mark_attendance():
    """Отметить посещаемость (AJAX)"""
    data = request.get_json()
    
    if not data.get('student_id') or not data.get('date') or not data.get('status'):
        return jsonify({'error': 'Отсутствуют обязательные поля'}), 400
    
    if data['status'] not in ['присутствовал', 'отсутствовал', 'уважительная']:
        return jsonify({'error': 'Неверный статус'}), 400
    
    student = Student.query.get_or_404(data['student_id'])
    
    # Проверка доступа
    if current_user.role == 'teacher' and student.group.teacher_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400
    
    # Проверить существующую запись
    existing = Attendance.query.filter_by(
        student_id=data['student_id'],
        date=attendance_date
    ).first()
    
    if existing:
        existing.status = data['status']
        existing.comment = data.get('comment')
        existing.updated_at = datetime.utcnow()
        message = 'Обновлено'
    else:
        attendance = Attendance(
            student_id=data['student_id'],
            date=attendance_date,
            status=data['status'],
            comment=data.get('comment'),
            created_by=current_user.id
        )
        db.session.add(attendance)
        message = 'Отмечено'
    
    db.session.commit()
    
    return jsonify({'message': message}), 200


@bp.route('/attendance/history/<int:group_id>')
@login_required
@teacher_required
def attendance_history(group_id):
    """История посещаемости группы"""
    group = Group.query.get_or_404(group_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and group.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.groups'))
    
    # Фильтры
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # По умолчанию - последние 30 дней
    if not date_from:
        date_from = (date.today() - timedelta(days=30)).isoformat()
    if not date_to:
        date_to = date.today().isoformat()
    
    students = Student.query.filter_by(group_id=group_id).order_by(Student.full_name).all()
    
    students_stats = []
    for student in students:
        query = student.attendance_records
        
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= from_date)
        except ValueError:
            pass
        
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= to_date)
        except ValueError:
            pass
        
        records = query.order_by(Attendance.date.desc()).all()
        
        total = len(records)
        present = sum(1 for r in records if r.status == 'присутствовал')
        absent = sum(1 for r in records if r.status == 'отсутствовал')
        excused = sum(1 for r in records if r.status == 'уважительная')
        
        percentage = round((present / total * 100), 1) if total > 0 else 0
        
        students_stats.append({
            'student': student,
            'total': total,
            'present': present,
            'absent': absent,
            'excused': excused,
            'percentage': percentage
        })
    
    return render_template('teacher/attendance_history.html',
                         group=group,
                         students_stats=students_stats,
                         date_from=date_from,
                         date_to=date_to)


# ===================== НОРМАТИВЫ =====================

@bp.route('/standards')
@login_required
@teacher_required
def standards():
    """Страница работы с нормативами"""
    # Получить группы
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    # Модули и темы
    modules = Module.query.order_by(Module.number).all()
    
    # Выбранная группа и тема
    selected_group_id = request.args.get('group_id', type=int)
    selected_theme_id = request.args.get('theme_id', type=int)
    
    students_data = []
    selected_group = None
    selected_theme = None
    standards = []
    
    if selected_group_id and selected_theme_id:
        selected_group = Group.query.get(selected_group_id)
        selected_theme = Theme.query.get(selected_theme_id)
        
        if selected_group and selected_theme:
            # Проверка доступа
            if current_user.role == 'teacher' and selected_group.teacher_id != current_user.id:
                flash('Доступ запрещен.', 'danger')
                return redirect(url_for('teacher.standards'))
            
            standards = Standard.query.filter_by(
                theme_id=selected_theme_id,
                is_active=True
            ).all()
            
            students = Student.query.filter_by(group_id=selected_group_id).order_by(Student.full_name).all()
            
            for student in students:
                student_results = {}
                
                for standard in standards:
                    # Лучший результат
                    best_result = StandardResult.query.filter_by(
                        student_id=student.id,
                        standard_id=standard.id
                    ).order_by(StandardResult.points.desc()).first()
                    
                    student_results[standard.id] = best_result
                
                students_data.append({
                    'student': student,
                    'results': student_results
                })
    
    return render_template('teacher/standards.html',
                         groups=groups,
                         modules=modules,
                         selected_group=selected_group,
                         selected_theme=selected_theme,
                         standards=standards,
                         students_data=students_data)


@bp.route('/standards/add-result', methods=['POST'])
@login_required
@teacher_required
def add_result():
    """Добавить результат норматива (AJAX)"""
    data = request.get_json()
    
    required_fields = ['student_id', 'standard_id', 'result_value', 'date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Поле {field} обязательно'}), 400
    
    student = Student.query.get_or_404(data['student_id'])
    standard = Standard.query.get_or_404(data['standard_id'])
    
    # Проверка доступа
    if current_user.role == 'teacher' and student.group.teacher_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        result_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400
    
    # Автоматический расчет баллов
    points = calculate_points_from_result(
        data['standard_id'],
        student.gender,
        data['result_value']
    )
    
    # Номер попытки
    attempt_number = StandardResult.query.filter_by(
        student_id=data['student_id'],
        standard_id=data['standard_id']
    ).count() + 1
    
    result = StandardResult(
        student_id=data['student_id'],
        standard_id=data['standard_id'],
        result_value=data['result_value'],
        points=points,
        date=result_date,
        attempt_number=attempt_number,
        created_by=current_user.id
    )
    
    db.session.add(result)
    db.session.commit()
    
    return jsonify({
        'message': 'Результат добавлен',
        'points': points,
        'attempt': attempt_number
    }), 201

@bp.route('/standards/edit-result/<int:result_id>', methods=['POST'])
@login_required
@teacher_required
def edit_result(result_id):
    """Редактировать результат норматива (AJAX)"""
    result = StandardResult.query.get_or_404(result_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and result.student.group.teacher_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    
    if 'result_value' not in data or 'date' not in data:
        return jsonify({'error': 'Отсутствуют обязательные поля'}), 400
    
    try:
        result_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400
    
    # Обновить результат
    result.result_value = data['result_value']
    result.date = result_date
    
    # Пересчитать баллы
    result.points = calculate_points_from_result(
        result.standard_id,
        result.student.gender,
        data['result_value']
    )
    
    result.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Результат обновлен',
        'points': result.points
    }), 200


@bp.route('/standards/delete-result/<int:result_id>', methods=['POST'])
@login_required
@teacher_required
def delete_result(result_id):
    """Удалить результат норматива (AJAX)"""
    result = StandardResult.query.get_or_404(result_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and result.student.group.teacher_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    db.session.delete(result)
    db.session.commit()
    
    return jsonify({'message': 'Результат удален'}), 200

@bp.route('/standards/student/<int:student_id>')
@login_required
@teacher_required
def student_results(student_id):
    """Все результаты студента"""
    student = Student.query.get_or_404(student_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and student.group.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.groups'))
    
    results = StandardResult.query.filter_by(student_id=student_id).order_by(
        StandardResult.date.desc()
    ).all()
    
    # Группировка по модулям и темам
    results_by_module = {}
    
    for result in results:
        theme = result.standard.theme
        module = theme.module
        
        module_name = f"Модуль {module.number}"
        theme_name = theme.name
        
        if module_name not in results_by_module:
            results_by_module[module_name] = {}
        
        if theme_name not in results_by_module[module_name]:
            results_by_module[module_name][theme_name] = []
        
        results_by_module[module_name][theme_name].append(result)
    
    return render_template('teacher/student_results.html',
                         student=student,
                         results_by_module=results_by_module)


# ===================== РЕЙТИНГ =====================

@bp.route('/rating/<int:group_id>')
@login_required
@teacher_required
def rating(group_id):
    """Рейтинг группы"""
    group = Group.query.get_or_404(group_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and group.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.groups'))
    
    students = Student.query.filter_by(group_id=group_id).all()
    
    ratings = []
    for student in students:
        rating = calculate_student_rating(student.id)
        ratings.append({
            'student': student,
            'rating': rating
        })
    
    # Сортировка
    sort_by = request.args.get('sort', 'total')
    if sort_by == 'total':
        ratings.sort(key=lambda x: x['rating']['total'], reverse=True)
    elif sort_by == 'attendance':
        ratings.sort(key=lambda x: x['rating']['attendance'], reverse=True)
    elif sort_by == 'module1':
        ratings.sort(key=lambda x: x['rating']['module1'], reverse=True)
    elif sort_by == 'module2':
        ratings.sort(key=lambda x: x['rating']['module2'], reverse=True)
    elif sort_by == 'name':
        ratings.sort(key=lambda x: x['student'].full_name)
    
    return render_template('teacher/rating.html',
                         group=group,
                         ratings=ratings,
                         sort_by=sort_by)


# ===================== ИНДИВИДУАЛЬНЫЕ ЗАДАНИЯ =====================

@bp.route('/assignments')
@login_required
@teacher_required
def assignments():
    """Список индивидуальных заданий"""
    group_id = request.args.get('group_id', type=int)
    status = request.args.get('status')
    
    query = Assignment.query.filter_by(created_by=current_user.id)
    
    if group_id:
        student_ids = [s.id for s in Student.query.filter_by(group_id=group_id).all()]
        query = query.filter(Assignment.student_id.in_(student_ids))
    
    if status:
        query = query.filter_by(status=status)
    
    assignments = query.order_by(Assignment.deadline.asc()).all()
    
    # Группы для фильтра
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    return render_template('teacher/assignments.html',
                         assignments=assignments,
                         groups=groups,
                         selected_group_id=group_id,
                         selected_status=status)


@bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_assignment():
    """Создать индивидуальное задание"""
    # Получить группы и студентов
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    if request.method == 'GET':
        return render_template('teacher/assignment_form.html',
                             assignment=None,
                             groups=groups)
    
    # POST - создание задания
    student_id = request.form.get('student_id', type=int)
    assignment_type = request.form.get('type')
    title = request.form.get('title')
    description = request.form.get('description')
    deadline = request.form.get('deadline')
    bonus_points = request.form.get('bonus_points', type=int, default=0)
    
    if not all([student_id, assignment_type, title, deadline]):
        flash('Все обязательные поля должны быть заполнены.', 'danger')
        return redirect(url_for('teacher.create_assignment'))
    
    student = Student.query.get_or_404(student_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and student.group.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.assignments'))
    
    try:
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
    except ValueError:
        flash('Неверный формат даты.', 'danger')
        return redirect(url_for('teacher.create_assignment'))
    
    assignment = Assignment(
        student_id=student_id,
        type=assignment_type,
        title=title,
        description=description,
        deadline=deadline_date,
        bonus_points=bonus_points,
        created_by=current_user.id
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'Задание "{title}" успешно создано для студента {student.full_name}.', 'success')
    return redirect(url_for('teacher.assignments'))


@bp.route('/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_assignment(assignment_id):
    """Редактировать задание"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Проверка доступа
    if assignment.created_by != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.assignments'))
    
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    if request.method == 'GET':
        return render_template('teacher/assignment_form.html',
                             assignment=assignment,
                             groups=groups)
    
    # POST - обновление
    title = request.form.get('title')
    description = request.form.get('description')
    deadline = request.form.get('deadline')
    status = request.form.get('status')
    bonus_points = request.form.get('bonus_points', type=int)
    
    if title:
        assignment.title = title
    if description:
        assignment.description = description
    if deadline:
        try:
            assignment.deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты.', 'danger')
            return redirect(url_for('teacher.edit_assignment', assignment_id=assignment_id))
    if status:
        assignment.status = status
    if bonus_points is not None:
        assignment.bonus_points = bonus_points
    
    db.session.commit()
    
    flash('Задание успешно обновлено.', 'success')
    return redirect(url_for('teacher.assignments'))


@bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_assignment(assignment_id):
    """Удалить задание"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Проверка доступа
    if assignment.created_by != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.assignments'))
    
    title = assignment.title
    db.session.delete(assignment)
    db.session.commit()
    
    flash(f'Задание "{title}" успешно удалено.', 'success')
    return redirect(url_for('teacher.assignments'))


# ===================== ВЕДОМОСТИ =====================

@bp.route('/statements')
@login_required
@teacher_required
def statements():
    """Список ведомостей"""
    if current_user.role == 'admin':
        statements = Statement.query.order_by(Statement.date.desc()).all()
    else:
        statements = Statement.query.filter_by(
            teacher_id=current_user.id
        ).order_by(Statement.date.desc()).all()
    
    return render_template('teacher/statements.html', statements=statements)


@bp.route('/statements/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_statement():
    """Создать новую ведомость"""
    
    # Получить группы преподавателя
    groups = Group.query.filter_by(teacher_id=current_user.id).all()
    
    # Создать форму
    form = StatementForm()
    
    # Заполнить choices для группы
    form.group_id.choices = [(0, 'Выберите группу...')] + [
        (group.id, f"{group.name} (курс {group.course}, семестр {group.semester})")
        for group in groups
    ]
    
    if form.validate_on_submit():
        try:
            # Проверить что группа принадлежит преподавателю
            group = Group.query.get(form.group_id.data)
            if not group or group.teacher_id != current_user.id:
                flash('Недопустимая группа', 'danger')
                return redirect(url_for('teacher.create_statement'))
            
            # Обработать файл если загружен
            file_path = None
            if form.file.data:
                file = form.file.data
                filename = secure_filename(file.filename)
                file_path = get_upload_path(filename, subfolder='statements')
                file.save(file_path)
            
            # Генерировать номер ведомости
            year = date.today().year
            last_statement = Statement.query.filter(
                Statement.number.like(f'ФК-{year}-%')
            ).order_by(Statement.number.desc()).first()
            
            if last_statement:
                last_num = int(last_statement.number.split('-')[-1])
                statement_number = f'ФК-{year}-{last_num + 1:03d}'
            else:
                statement_number = f'ФК-{year}-001'
            
            # Создать ведомость
            statement = Statement(
                number=statement_number,
                group_id=form.group_id.data,
                semester=form.semester.data,
                type=form.type.data,
                date=form.date.data,
                teacher_id=current_user.id,
                dean_name=form.dean_name.data,
                file_path=file_path
            )
            
            db.session.add(statement)
            db.session.commit()
            
            flash(f'Ведомость №{statement_number} успешно создана', 'success')
            return redirect(url_for('teacher.view_statement', statement_id=statement.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании ведомости: {str(e)}', 'danger')
            return redirect(url_for('teacher.create_statement'))
    
    # GET запрос или ошибки валидации
    return render_template('teacher/statement_form.html', form=form, groups=groups)


@bp.route('/statements/<int:statement_id>')
@login_required
@teacher_required
def statement_details(statement_id):
    """Детали ведомости с результатами студентов"""
    statement = Statement.query.get_or_404(statement_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and statement.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.statements'))
    
    # Получить студентов с рейтингами
    students = Student.query.filter_by(group_id=statement.group_id).order_by(Student.full_name).all()
    
    students_data = []
    for student in students:
        rating = calculate_student_rating(student.id)
        students_data.append({
            'student': student,
            'rating': rating,
            'result': 'Зачтено' if rating['passed'] else 'Не зачтено'
        })
    
    return render_template('teacher/statement_details.html',
                         statement=statement,
                         students_data=students_data)


# ===================== ОТЧЕТЫ =====================

@bp.route('/reports')
@login_required
@teacher_required
def reports():
    """Главная страница отчетов"""
    # Получить группы для выбора
    if current_user.role == 'admin':
        groups = Group.query.order_by(Group.name).all()
    else:
        groups = Group.query.filter_by(teacher_id=current_user.id).order_by(Group.name).all()
    
    return render_template('teacher/reports.html', groups=groups)


@bp.route('/reports/summary/<int:group_id>')
@login_required
@teacher_required
def summary_report(group_id):
    """Сводный отчет по группе"""
    group = Group.query.get_or_404(group_id)
    
    # Проверка доступа
    if current_user.role == 'teacher' and group.teacher_id != current_user.id:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('teacher.reports'))
    
    students = Student.query.filter_by(group_id=group_id).all()
    
    total_students = len(students)
    passed = 0
    failed = 0
    total_attendance = 0
    total_rating = 0
    
    students_data = []
    
    for student in students:
        rating = calculate_student_rating(student.id)
        attendance_pct = student.get_attendance_percentage()
        
        if rating['passed']:
            passed += 1
        else:
            failed += 1
        
        total_attendance += attendance_pct
        total_rating += rating['total']
        
        students_data.append({
            'student': student,
            'rating': rating,
            'attendance_percentage': attendance_pct
        })
    
    avg_attendance = round(total_attendance / total_students, 1) if total_students > 0 else 0
    avg_rating = round(total_rating / total_students, 1) if total_students > 0 else 0
    pass_rate = round((passed / total_students * 100), 1) if total_students > 0 else 0
    
    summary = {
        'total_students': total_students,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'avg_attendance': avg_attendance,
        'avg_rating': avg_rating
    }
    
    return render_template('teacher/summary_report.html',
                         group=group,
                         summary=summary,
                         students_data=students_data)