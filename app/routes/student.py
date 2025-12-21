from flask import Blueprint, request, render_template, redirect, url_for, flash
from app import db
from app.models import Student, Attendance, StandardResult, Assignment
from app.utils import calculate_student_rating
from datetime import datetime

bp = Blueprint('student', __name__, url_prefix='/student')


@bp.route('/search', methods=['GET', 'POST'])
def search():
    """Поиск студента (без авторизации)"""
    if request.method == 'GET':
        return render_template('student/search.html')
    
    # POST запрос - обработка поиска
    full_name = request.form.get('full_name', '').strip()
    student_number = request.form.get('student_number', '').strip()
    
    if not full_name and not student_number:
        flash('Укажите ФИО или номер студенческого билета.', 'warning')
        return redirect(url_for('student.search'))
    
    # Поиск по номеру студенческого билета (точное совпадение)
    if student_number:
        student = Student.query.filter_by(student_number=student_number).first()
        if student:
            return redirect(url_for('student.profile', student_id=student.id))
        else:
            flash(f'Студент с номером "{student_number}" не найден.', 'danger')
            return redirect(url_for('student.search'))
    
    # Поиск по ФИО (частичное совпадение)
    if full_name:
        students = Student.query.filter(Student.full_name.ilike(f'%{full_name}%')).all()
        
        if not students:
            flash(f'Студенты с ФИО "{full_name}" не найдены.', 'danger')
            return redirect(url_for('student.search'))
        
        # Если найден один студент - сразу перенаправляем на профиль
        if len(students) == 1:
            return redirect(url_for('student.profile', student_id=students[0].id))
        
        # Если найдено несколько - показываем список для выбора
        return render_template('student/search_results.html',
                             students=students,
                             search_query=full_name)


@bp.route('/<int:student_id>')
def profile(student_id):
    """Полный профиль студента (без авторизации)"""
    student = Student.query.get_or_404(student_id)
    
    # Рейтинг студента
    rating = calculate_student_rating(student_id)
    attendance_pct = student.get_attendance_percentage()
    
    # Последние 10 записей посещаемости
    recent_attendance = student.attendances.order_by(
        Attendance.date.desc()
    ).limit(10).all()
    
    # Все результаты нормативов
    results = StandardResult.query.filter_by(student_id=student_id).order_by(
        StandardResult.date.desc()
    ).all()
    
    # Группировка результатов по темам
    results_by_theme = {}
    for result in results:
        theme_name = result.standard.theme.name
        if theme_name not in results_by_theme:
            results_by_theme[theme_name] = []
        results_by_theme[theme_name].append(result)
    
    # Активные индивидуальные задания
    active_assignments = Assignment.query.filter_by(
        student_id=student_id,
        status='назначено'
    ).order_by(Assignment.deadline.asc()).all()
    
    # Выполненные задания
    completed_assignments = Assignment.query.filter_by(
        student_id=student_id,
        status='выполнено'
    ).order_by(Assignment.completion_date.desc()).limit(5).all()
    
    # Просроченные задания
    overdue_assignments = Assignment.query.filter_by(
        student_id=student_id,
        status='просрочено'
    ).order_by(Assignment.deadline.desc()).all()
    
    return render_template('student/profile.html',
                         student=student,
                         rating=rating,
                         attendance_pct=attendance_pct,
                         recent_attendance=recent_attendance,
                         results_by_theme=results_by_theme,
                         active_assignments=active_assignments,
                         completed_assignments=completed_assignments,
                         overdue_assignments=overdue_assignments)


@bp.route('/<int:student_id>/attendance')
def attendance(student_id):
    """Посещаемость студента (без авторизации)"""
    student = Student.query.get_or_404(student_id)
    
    # Фильтры по датам
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = student.attendances
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= from_date)
        except ValueError:
            flash('Неверный формат даты "от".', 'warning')
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= to_date)
        except ValueError:
            flash('Неверный формат даты "до".', 'warning')
    
    records = query.order_by(Attendance.date.desc()).all()
    
    # Статистика
    total_classes = len(records)
    present = sum(1 for r in records if r.status == 'присутствовал')
    absent = sum(1 for r in records if r.status == 'отсутствовал')
    excused = sum(1 for r in records if r.status == 'уважительная')
    
    stats = {
        'total': total_classes,
        'present': present,
        'absent': absent,
        'excused': excused,
        'percentage': student.get_attendance_percentage()
    }
    
    return render_template('student/attendance.html',
                         student=student,
                         records=records,
                         stats=stats,
                         date_from=date_from,
                         date_to=date_to)


@bp.route('/<int:student_id>/results')
def results(student_id):
    """Результаты нормативов студента (без авторизации)"""
    student = Student.query.get_or_404(student_id)
    
    # Все результаты
    all_results = StandardResult.query.filter_by(student_id=student_id).order_by(
        StandardResult.date.desc()
    ).all()
    
    # Группировка по модулям и темам
    results_by_module = {}
    
    for result in all_results:
        theme = result.standard.theme
        module = theme.module
        
        module_name = f"Модуль {module.number}: {module.name}"
        theme_name = theme.name
        
        if module_name not in results_by_module:
            results_by_module[module_name] = {}
        
        if theme_name not in results_by_module[module_name]:
            results_by_module[module_name][theme_name] = []
        
        results_by_module[module_name][theme_name].append(result)
    
    # Статистика
    total_results = len(all_results)
    avg_points = round(sum(r.points for r in all_results) / total_results, 2) if total_results > 0 else 0
    
    # Лучшие результаты
    best_results = sorted(all_results, key=lambda x: x.points, reverse=True)[:5]
    
    stats = {
        'total': total_results,
        'avg_points': avg_points,
        'best_results': best_results
    }
    
    return render_template('student/results.html',
                         student=student,
                         results_by_module=results_by_module,
                         stats=stats)


@bp.route('/<int:student_id>/assignments')
def assignments(student_id):
    """Индивидуальные задания студента (без авторизации)"""
    student = Student.query.get_or_404(student_id)
    
    # Фильтр по статусу
    status_filter = request.args.get('status')
    
    query = Assignment.query.filter_by(student_id=student_id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    all_assignments = query.order_by(Assignment.deadline.desc()).all()
    
    # Группировка по статусу
    active = [a for a in all_assignments if a.status == 'назначено']
    completed = [a for a in all_assignments if a.status == 'выполнено']
    overdue = [a for a in all_assignments if a.status == 'просрочено']
    
    # Статистика
    total_bonus = sum(a.bonus_points for a in completed)
    
    stats = {
        'total': len(all_assignments),
        'active': len(active),
        'completed': len(completed),
        'overdue': len(overdue),
        'total_bonus': total_bonus
    }
    
    return render_template('student/assignments.html',
                         student=student,
                         active_assignments=active,
                         completed_assignments=completed,
                         overdue_assignments=overdue,
                         stats=stats,
                         status_filter=status_filter)


@bp.route('/<int:student_id>/rating')
def rating_details(student_id):
    """Детальный расчет рейтинга студента (без авторизации)"""
    student = Student.query.get_or_404(student_id)
    
    rating = calculate_student_rating(student_id)
    
    # Получить детализацию по модулям
    from app.models import Module, Theme, Standard
    
    modules_data = []
    
    modules = Module.query.order_by(Module.number).all()
    for module in modules:
        themes_data = []
        
        for theme in module.themes:
            # Результаты по теме
            standards = theme.standards.filter_by(is_active=True).all()
            
            theme_results = []
            theme_total_points = 0
            
            for standard in standards:
                # Лучший результат студента по этому нормативу
                best_result = StandardResult.query.filter_by(
                    student_id=student_id,
                    standard_id=standard.id
                ).order_by(StandardResult.points.desc()).first()
                
                if best_result:
                    theme_results.append({
                        'standard': standard,
                        'result': best_result
                    })
                    theme_total_points += best_result.points
            
            themes_data.append({
                'theme': theme,
                'results': theme_results,
                'total_points': theme_total_points
            })
        
        modules_data.append({
            'module': module,
            'themes': themes_data
        })
    
    return render_template('student/rating_details.html',
                         student=student,
                         rating=rating,
                         modules_data=modules_data)


@bp.route('/<int:student_id>/print')
def print_profile(student_id):
    """Версия профиля для печати (без авторизации)"""
    student = Student.query.get_or_404(student_id)
    
    rating = calculate_student_rating(student_id)
    attendance_pct = student.get_attendance_percentage()
    
    # Все результаты
    results = StandardResult.query.filter_by(student_id=student_id).order_by(
        StandardResult.date.desc()
    ).all()
    
    # Группировка по темам
    results_by_theme = {}
    for result in results:
        theme_name = result.standard.theme.name
        if theme_name not in results_by_theme:
            results_by_theme[theme_name] = []
        results_by_theme[theme_name].append(result)
    
    # Все задания
    assignments = Assignment.query.filter_by(student_id=student_id).order_by(
        Assignment.deadline.desc()
    ).all()
    
    return render_template('student/print_profile.html',
                         student=student,
                         rating=rating,
                         attendance_pct=attendance_pct,
                         results_by_theme=results_by_theme,
                         assignments=assignments,
                         now=datetime.now()) 