from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import (User, Group, Student, Attendance, StandardResult, 
                        Statement, Standard, Assignment)
from app.utils import calculate_student_rating

bp = Blueprint('department', __name__, url_prefix='/department')


def department_head_required(f):
    """Декоратор для проверки прав заведующего кафедрой"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['department_head', 'admin']:
            flash('Доступ запрещен. Требуются права заведующего кафедрой.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ===================== ПАНЕЛЬ ЗАВЕДУЮЩЕГО КАФЕДРОЙ =====================

@bp.route('/')
@login_required
@department_head_required
def dashboard():
    """Главная панель заведующего кафедрой"""
    
    # Общая статистика
    total_students = Student.query.count()
    total_groups = Group.query.count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    
    # Средняя посещаемость
    total_attendance = db.session.query(func.count(Attendance.id)).scalar() or 0
    present_attendance = db.session.query(func.count(Attendance.id)).filter(
        Attendance.status == 'присутствовал'
    ).scalar() or 0
    
    avg_attendance = round((present_attendance / total_attendance * 100) if total_attendance > 0 else 0, 2)
    
    # Средний рейтинг и процент сдачи
    students = Student.query.all()
    total_rating = 0
    passed_count = 0
    failed_count = 0
    
    for student in students:
        rating = calculate_student_rating(student.id)
        total_rating += rating['total']
        if rating['passed']:
            passed_count += 1
        else:
            failed_count += 1
    
    avg_rating = round(total_rating / total_students if total_students > 0 else 0, 2)
    pass_rate = round((passed_count / total_students * 100) if total_students > 0 else 0, 2)
    
    # Последние ведомости
    recent_statements = Statement.query.order_by(Statement.date.desc()).limit(5).all()
    
    # Преподаватели с низкой успеваемостью
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    teachers_performance = []
    
    for teacher in teachers:
        groups = Group.query.filter_by(teacher_id=teacher.id).all()
        if not groups:
            continue
        
        teacher_passed = 0
        teacher_total = 0
        
        for group in groups:
            students = Student.query.filter_by(group_id=group.id).all()
            for student in students:
                rating = calculate_student_rating(student.id)
                teacher_total += 1
                if rating['passed']:
                    teacher_passed += 1
        
        if teacher_total > 0:
            pass_rate = round((teacher_passed / teacher_total * 100), 2)
            teachers_performance.append({
                'teacher': teacher,
                'groups_count': len(groups),
                'students_count': teacher_total,
                'pass_rate': pass_rate
            })
    
    # Сортировка по проценту сдачи (худшие первыми)
    teachers_performance.sort(key=lambda x: x['pass_rate'])
    low_performance_teachers = teachers_performance[:5]
    
    stats = {
        'total_students': total_students,
        'total_groups': total_groups,
        'total_teachers': total_teachers,
        'avg_attendance': avg_attendance,
        'avg_rating': avg_rating,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'pass_rate': pass_rate
    }
    
    return render_template('department/dashboard.html',
                         stats=stats,
                         recent_statements=recent_statements,
                         low_performance_teachers=low_performance_teachers)


# ===================== ПРЕПОДАВАТЕЛИ =====================

@bp.route('/teachers')
@login_required
@department_head_required
def teachers():
    """Статистика по преподавателям"""
    
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    
    teachers_data = []
    for teacher in teachers:
        groups = Group.query.filter_by(teacher_id=teacher.id).all()
        
        total_students = 0
        total_rating = 0
        total_attendance = 0
        passed = 0
        failed = 0
        
        for group in groups:
            students = Student.query.filter_by(group_id=group.id).all()
            total_students += len(students)
            
            for student in students:
                rating = calculate_student_rating(student.id)
                attendance_pct = student.get_attendance_percentage()
                
                total_rating += rating['total']
                total_attendance += attendance_pct
                
                if rating['passed']:
                    passed += 1
                else:
                    failed += 1
        
        avg_rating = round(total_rating / total_students, 2) if total_students > 0 else 0
        avg_attendance = round(total_attendance / total_students, 2) if total_students > 0 else 0
        pass_rate = round((passed / total_students * 100), 2) if total_students > 0 else 0
        
        teachers_data.append({
            'teacher': teacher,
            'groups_count': len(groups),
            'students_count': total_students,
            'avg_rating': avg_rating,
            'avg_attendance': avg_attendance,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate
        })
    
    # Сортировка по рейтингу
    sort_by = request.args.get('sort', 'rating')
    if sort_by == 'rating':
        teachers_data.sort(key=lambda x: x['avg_rating'], reverse=True)
    elif sort_by == 'attendance':
        teachers_data.sort(key=lambda x: x['avg_attendance'], reverse=True)
    elif sort_by == 'pass_rate':
        teachers_data.sort(key=lambda x: x['pass_rate'], reverse=True)
    elif sort_by == 'students':
        teachers_data.sort(key=lambda x: x['students_count'], reverse=True)
    
    return render_template('department/teachers.html',
                         teachers_data=teachers_data,
                         sort_by=sort_by)


@bp.route('/teachers/<int:teacher_id>')
@login_required
@department_head_required
def teacher_details(teacher_id):
    """Детальная статистика по преподавателю"""
    
    teacher = User.query.get_or_404(teacher_id)
    
    if teacher.role != 'teacher':
        flash('Пользователь не является преподавателем.', 'danger')
        return redirect(url_for('department.teachers'))
    
    groups = Group.query.filter_by(teacher_id=teacher_id).all()
    
    groups_data = []
    for group in groups:
        students = Student.query.filter_by(group_id=group.id).all()
        
        group_total_rating = 0
        group_total_attendance = 0
        group_passed = 0
        group_failed = 0
        
        for student in students:
            rating = calculate_student_rating(student.id)
            attendance_pct = student.get_attendance_percentage()
            
            group_total_rating += rating['total']
            group_total_attendance += attendance_pct
            
            if rating['passed']:
                group_passed += 1
            else:
                group_failed += 1
        
        students_count = len(students)
        group_avg_rating = round(group_total_rating / students_count, 2) if students_count > 0 else 0
        group_avg_attendance = round(group_total_attendance / students_count, 2) if students_count > 0 else 0
        group_pass_rate = round((group_passed / students_count * 100), 2) if students_count > 0 else 0
        
        groups_data.append({
            'group': group,
            'students_count': students_count,
            'avg_rating': group_avg_rating,
            'avg_attendance': group_avg_attendance,
            'passed': group_passed,
            'failed': group_failed,
            'pass_rate': group_pass_rate
        })
    
    return render_template('department/teacher_details.html',
                         teacher=teacher,
                         groups_data=groups_data)


# ===================== СРАВНЕНИЕ ГРУПП =====================

@bp.route('/groups/compare')
@login_required
@department_head_required
def compare_groups():
    """Сравнительный анализ групп"""
    
    course = request.args.get('course', type=int)
    semester = request.args.get('semester', type=int)
    
    query = Group.query
    if course:
        query = query.filter_by(course=course)
    if semester:
        query = query.filter_by(semester=semester)
    
    groups = query.order_by(Group.name).all()
    
    comparison = []
    for group in groups:
        students = Student.query.filter_by(group_id=group.id).all()
        
        total_rating = 0
        total_attendance = 0
        passed = 0
        failed = 0
        
        for student in students:
            rating = calculate_student_rating(student.id)
            attendance_pct = student.get_attendance_percentage()
            
            total_rating += rating['total']
            total_attendance += attendance_pct
            
            if rating['passed']:
                passed += 1
            else:
                failed += 1
        
        students_count = len(students)
        avg_rating = round(total_rating / students_count, 2) if students_count > 0 else 0
        avg_attendance = round(total_attendance / students_count, 2) if students_count > 0 else 0
        pass_rate = round((passed / students_count * 100), 2) if students_count > 0 else 0
        
        comparison.append({
            'group': group,
            'students_count': students_count,
            'avg_rating': avg_rating,
            'avg_attendance': avg_attendance,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate
        })
    
    # Сортировка по среднему рейтингу
    sort_by = request.args.get('sort', 'rating')
    if sort_by == 'rating':
        comparison.sort(key=lambda x: x['avg_rating'], reverse=True)
    elif sort_by == 'attendance':
        comparison.sort(key=lambda x: x['avg_attendance'], reverse=True)
    elif sort_by == 'pass_rate':
        comparison.sort(key=lambda x: x['pass_rate'], reverse=True)
    
    # Все курсы и семестры для фильтров
    all_courses = db.session.query(Group.course.distinct()).order_by(Group.course).all()
    all_semesters = db.session.query(Group.semester.distinct()).order_by(Group.semester).all()
    
    return render_template('department/compare_groups.html',
                         comparison=comparison,
                         selected_course=course,
                         selected_semester=semester,
                         all_courses=[c[0] for c in all_courses],
                         all_semesters=[s[0] for s in all_semesters],
                         sort_by=sort_by)


# ===================== ВЕДОМОСТИ =====================

@bp.route('/statements')
@login_required
@department_head_required
def statements():
    """Список всех ведомостей"""
    
    teacher_id = request.args.get('teacher_id', type=int)
    semester = request.args.get('semester', type=int)
    
    query = Statement.query
    
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if semester:
        query = query.filter_by(semester=semester)
    
    statements = query.order_by(Statement.date.desc()).all()
    
    # Список преподавателей для фильтра
    teachers = User.query.filter_by(role='teacher', is_active=True).order_by(User.full_name).all()
    
    # Все семестры для фильтра
    all_semesters = db.session.query(Statement.semester.distinct()).order_by(Statement.semester).all()
    
    return render_template('department/statements.html',
                         statements=statements,
                         teachers=teachers,
                         selected_teacher_id=teacher_id,
                         selected_semester=semester,
                         all_semesters=[s[0] for s in all_semesters])


@bp.route('/statements/<int:statement_id>')
@login_required
@department_head_required
def statement_details(statement_id):
    """Детали ведомости"""
    
    statement = Statement.query.get_or_404(statement_id)
    
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
    
    return render_template('department/statement_details.html',
                         statement=statement,
                         students_data=students_data)


# ===================== ОТЧЕТЫ =====================

@bp.route('/reports')
@login_required
@department_head_required
def reports():
    """Главная страница отчетов"""
    return render_template('department/reports.html')


@bp.route('/reports/attendance-dynamics')
@login_required
@department_head_required
def attendance_dynamics():
    """Динамика посещаемости"""
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # По умолчанию - последние 30 дней
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    query = db.session.query(
        func.date(Attendance.date).label('date'),
        func.count(Attendance.id).label('total'),
        func.sum(db.case((Attendance.status == 'присутствовал', 1), else_=0)).label('present')
    )
    
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
    
    results = query.group_by(func.date(Attendance.date)).order_by(
        func.date(Attendance.date)
    ).all()
    
    dynamics = []
    for result in results:
        percentage = round((result.present / result.total * 100) if result.total > 0 else 0, 2)
        dynamics.append({
            'date': result.date,
            'total': result.total,
            'present': result.present,
            'percentage': percentage
        })
    
    return render_template('department/attendance_dynamics.html',
                         dynamics=dynamics,
                         date_from=date_from,
                         date_to=date_to)


@bp.route('/reports/standards-completion')
@login_required
@department_head_required
def standards_completion():
    """Отчет по выполнению нормативов"""
    
    standards = Standard.query.filter_by(is_active=True).all()
    total_students = Student.query.count()
    
    completion = []
    for standard in standards:
        # Количество студентов, выполнивших норматив
        completed = db.session.query(func.count(func.distinct(StandardResult.student_id))).filter(
            StandardResult.standard_id == standard.id
        ).scalar() or 0
        
        completion_rate = round((completed / total_students * 100), 2) if total_students > 0 else 0
        
        # Средний балл
        avg_points = db.session.query(func.avg(StandardResult.points)).filter(
            StandardResult.standard_id == standard.id
        ).scalar()
        avg_points = round(float(avg_points), 2) if avg_points else 0
        
        completion.append({
            'standard': standard,
            'completed_by': completed,
            'total_students': total_students,
            'completion_rate': completion_rate,
            'avg_points': avg_points
        })
    
    # Сортировка по проценту выполнения
    sort_by = request.args.get('sort', 'completion')
    if sort_by == 'completion':
        completion.sort(key=lambda x: x['completion_rate'], reverse=True)
    elif sort_by == 'avg_points':
        completion.sort(key=lambda x: x['avg_points'], reverse=True)
    elif sort_by == 'name':
        completion.sort(key=lambda x: x['standard'].name)
    
    return render_template('department/standards_completion.html',
                         completion=completion,
                         sort_by=sort_by)


@bp.route('/reports/medical-groups')
@login_required
@department_head_required
def medical_groups():
    """Отчет по медицинским группам"""
    
    medical_groups_data = db.session.query(
        Student.medical_group,
        func.count(Student.id).label('count')
    ).group_by(Student.medical_group).all()
    
    total = Student.query.count()
    
    distribution = []
    for mg in medical_groups_data:
        percentage = round((mg.count / total * 100), 2) if total > 0 else 0
        distribution.append({
            'medical_group': mg.medical_group,
            'count': mg.count,
            'percentage': percentage
        })
    
    # Сортировка по количеству
    distribution.sort(key=lambda x: x['count'], reverse=True)
    
    return render_template('department/medical_groups.html',
                         distribution=distribution,
                         total_students=total)


@bp.route('/reports/low-performance')
@login_required
@department_head_required
def low_performance():
    """Отчет по студентам с низкой успеваемостью"""
    
    threshold = request.args.get('threshold', type=int, default=60)
    
    students = Student.query.all()
    
    low_performers = []
    for student in students:
        rating = calculate_student_rating(student.id)
        attendance_pct = student.get_attendance_percentage()
        
        if rating['total'] < threshold:
            low_performers.append({
                'student': student,
                'rating': rating,
                'attendance': attendance_pct,
                'group': student.group
            })
    
    # Сортировка по рейтингу (худшие первыми)
    low_performers.sort(key=lambda x: x['rating']['total'])
    
    return render_template('department/low_performance.html',
                         low_performers=low_performers,
                         threshold=threshold)


@bp.route('/reports/assignments-summary')
@login_required
@department_head_required
def assignments_summary():
    """Сводка по индивидуальным заданиям"""
    
    # Общая статистика по заданиям
    total_assignments = Assignment.query.count()
    completed = Assignment.query.filter_by(status='выполнено').count()
    assigned = Assignment.query.filter_by(status='назначено').count()
    overdue = Assignment.query.filter_by(status='просрочено').count()
    
    completion_rate = round((completed / total_assignments * 100), 2) if total_assignments > 0 else 0
    
    # Задания по типам
    assignments_by_type = db.session.query(
        Assignment.type,
        func.count(Assignment.id).label('count')
    ).group_by(Assignment.type).all()
    
    type_distribution = []
    for atype in assignments_by_type:
        percentage = round((atype.count / total_assignments * 100), 2) if total_assignments > 0 else 0
        type_distribution.append({
            'type': atype.type,
            'count': atype.count,
            'percentage': percentage
        })
    
    # Последние просроченные задания
    overdue_assignments = Assignment.query.filter_by(status='просрочено').order_by(
        Assignment.deadline.desc()
    ).limit(10).all()
    
    stats = {
        'total': total_assignments,
        'completed': completed,
        'assigned': assigned,
        'overdue': overdue,
        'completion_rate': completion_rate
    }
    
    return render_template('department/assignments_summary.html',
                         stats=stats,
                         type_distribution=type_distribution,
                         overdue_assignments=overdue_assignments)