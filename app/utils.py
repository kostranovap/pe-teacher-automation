from datetime import datetime, date, timedelta
from flask import current_app
from app import db
from app.models import Student, Attendance, StandardResult, Assignment, StandardScale, Theme
import os
import uuid


# ===================== РАСЧЕТ БАЛЛОВ =====================

def calculate_attendance_points(student_id):
    student = Student.query.get(student_id)
    if not student:
        return 0
    
    total = student.attendances.count()
    if total == 0:
        return 0
    
    present = student.attendances.filter_by(status='присутствовал').count()
    percentage = (present / total) * 100
    
    max_points = current_app.config.get('ATTENDANCE_MAX_POINTS', 30)
    
    if percentage >= 90:
        return max_points
    elif percentage >= 80:
        return int(max_points * 0.833)  # 25 из 30
    elif percentage >= 70:
        return int(max_points * 0.667)  # 20 из 30
    elif percentage >= 60:
        return int(max_points * 0.5)    # 15 из 30
    else:
        return int(max_points * 0.333)  # 10 из 30


def calculate_module_points(student_id, module_number):
    from app.models import Module
    
    module = Module.query.filter_by(number=module_number).first()
    if not module:
        return 0
    
    themes = module.themes.all()
    if not themes:
        return 0
    
    total_points = 0
    
    for theme in themes:
        theme_points = calculate_theme_points(student_id, theme.id)
        total_points += theme_points
    
    return min(total_points, module.max_points)


def calculate_theme_points(student_id, theme_id):
    theme = Theme.query.get(theme_id)
    if not theme:
        return 0
    
    standards = theme.standards.filter_by(is_active=True).all()
    if not standards:
        return 0
    
    total_points = 0
    standards_count = len(standards)
    
    for standard in standards:
        best_result = StandardResult.query.filter_by(
            student_id=student_id,
            standard_id=standard.id
        ).order_by(StandardResult.points.desc()).first()
        
        if best_result:
            total_points += best_result.points
    
    if standards_count > 0:
        avg_points = total_points / standards_count
        normalized_points = (avg_points / 5) * theme.max_points
        return round(normalized_points, 2)
    
    return 0


def calculate_student_rating(student_id):
    attendance_points = calculate_attendance_points(student_id)
    module1_points = calculate_module_points(student_id, 1)
    module2_points = calculate_module_points(student_id, 2)
    
    bonus_points = db.session.query(db.func.sum(Assignment.bonus_points)).filter(
        Assignment.student_id == student_id,
        Assignment.status.in_(['выполнено', 'проверено'])
    ).scalar() or 0
    
    total = attendance_points + module1_points + module2_points + bonus_points
    
    max_points = current_app.config.get('TOTAL_MAX_POINTS', 100)
    total = min(total, max_points)
    
    passing_score = current_app.config.get('PASSING_SCORE', 60)
    
    return {
        'attendance': round(attendance_points, 2),
        'module1': round(module1_points, 2),
        'module2': round(module2_points, 2),
        'bonus': round(bonus_points, 2),
        'total': round(total, 2),
        'passed': total >= passing_score,
        'grade': get_grade_from_points(total)
    }


def calculate_points_from_result(standard_id, gender, result_value):
    from app.models import Standard
    
    standard = Standard.query.get(standard_id)
    if not standard:
        return 0
    
    scales = StandardScale.query.filter_by(
        standard_id=standard_id,
        gender=gender
    ).order_by(StandardScale.points.desc()).all()
    
    if not scales:
        return 0
    
    for scale in scales:
        if standard.comparison_type == 'less_better':
            if scale.max_value is None or result_value <= scale.max_value:
                if scale.min_value is None or result_value >= scale.min_value:
                    return scale.points
        else:
            if scale.min_value is None or result_value >= scale.min_value:
                if scale.max_value is None or result_value <= scale.max_value:
                    return scale.points
    
    return 1 


def get_grade_from_points(points):
    if points >= 90:
        return 'Отлично'
    elif points >= 75:
        return 'Хорошо'
    elif points >= 60:
        return 'Удовлетворительно'
    else:
        return 'Не зачтено'


# ===================== РАБОТА С ФАЙЛАМИ =====================

def allowed_file(filename, allowed_extensions=None):
    """
    Проверка допустимого расширения файла
    
    Args:
        filename: Имя файла
        allowed_extensions: Множество допустимых расширений или None (использовать из конфига)
    
    Returns:
        bool: True если файл допустим
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'pdf'})
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_unique_filename(filename):
    """
    Генерация уникального имени файла с временной меткой
    
    Args:
        filename: Исходное имя файла
    
    Returns:
        str: Уникальное имя файла
    
    Example:
        'document.pdf' → 'document_20250106_143052.pdf'
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = filename.rsplit('.', 1)
    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
    return f"{safe_name}_{timestamp}.{ext}"


def get_upload_path(filename, subfolder=''):
    """
    Получить полный путь для загрузки файла
    
    Args:
        filename: Имя файла
        subfolder: Подпапка (например, 'photos', 'statements')
    
    Returns:
        str: Полный путь к файлу
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    if subfolder:
        folder_path = os.path.join(upload_folder, subfolder)
    else:
        folder_path = upload_folder
    
    os.makedirs(folder_path, exist_ok=True)
    
    unique_filename = get_unique_filename(filename)
    return os.path.join(folder_path, unique_filename)


# ===================== ЗАДАНИЯ И ДЕДЛАЙНЫ =====================

def check_assignment_deadlines():
    """
    Проверить дедлайны заданий и обновить статусы на "просрочено"
    
    Returns:
        int: Количество обновленных заданий
    """
    today = date.today()
    overdue_assignments = Assignment.query.filter(
        Assignment.deadline < today,
        Assignment.status == 'назначено'
    ).all()
    
    for assignment in overdue_assignments:
        assignment.status = 'просрочено'
    
    if overdue_assignments:
        db.session.commit()
    
    return len(overdue_assignments)


def get_upcoming_deadlines(days=7):
    """
    Получить задания с приближающимся дедлайном
    
    Args:
        days: Количество дней вперед (по умолчанию 7)
    
    Returns:
        list: Список заданий
    """
    today = date.today()
    future_date = today + timedelta(days=days)
    
    upcoming = Assignment.query.filter(
        Assignment.deadline.between(today, future_date),
        Assignment.status == 'назначено'
    ).order_by(Assignment.deadline.asc()).all()
    
    return upcoming


# ===================== ГЕНЕРАЦИЯ НОМЕРОВ =====================

def generate_statement_number(year=None):
    """
    Генерировать номер ведомости
    
    Формат: ФК-YYYY-NNN
    Пример: ФК-2025-001
    
    Args:
        year: Год (по умолчанию текущий)
    
    Returns:
        str: Номер ведомости
    """
    from app.models import Statement
    
    if year is None:
        year = datetime.now().year
    
    count = Statement.query.filter(
        db.func.extract('year', Statement.date) == year
    ).count()
    
    return f"ФК-{year}-{count + 1:03d}"


def generate_student_number(prefix='ГБ', year=None):
    """
    Генерировать номер студенческого билета
    
    Формат: PREFIXYYNNNN
    Пример: ГБ125001
    
    Args:
        prefix: Префикс (по умолчанию 'ГБ')
        year: Год поступления (по умолчанию текущий)
    
    Returns:
        str: Номер студенческого билета
    """
    if year is None:
        year = datetime.now().year
    
    year_suffix = str(year)[-2:]
    
    last_student = Student.query.filter(
        Student.student_number.like(f'{prefix}{year_suffix}%')
    ).order_by(Student.student_number.desc()).first()
    
    if last_student:
        last_number = int(last_student.student_number[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}{year_suffix}{new_number:04d}"


# ===================== ФОРМАТИРОВАНИЕ =====================

def format_date(date_obj, format='%d.%m.%Y'):
    """
    Форматировать дату для отображения
    
    Args:
        date_obj: Объект даты или datetime
        format: Формат строки (по умолчанию 'DD.MM.YYYY')
    
    Returns:
        str: Отформатированная дата
    """
    if not date_obj:
        return ''
    
    if isinstance(date_obj, str):
        return date_obj
    
    return date_obj.strftime(format)


def format_datetime(datetime_obj, format='%d.%m.%Y %H:%M'):
    """
    Форматировать дату и время для отображения
    
    Args:
        datetime_obj: Объект datetime
        format: Формат строки
    
    Returns:
        str: Отформатированная дата и время
    """
    if not datetime_obj:
        return ''
    
    if isinstance(datetime_obj, str):
        return datetime_obj
    
    return datetime_obj.strftime(format)


def get_russian_month(month_number):
    """
    Получить название месяца на русском
    
    Args:
        month_number: Номер месяца (1-12)
    
    Returns:
        str: Название месяца
    """
    months = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    return months.get(month_number, '')


def get_semester_dates(semester):
    """
    Получить примерные даты начала и конца семестра
    
    Args:
        semester: Номер семестра (1-12)
    
    Returns:
        tuple: (start_date, end_date)
    """
    year = datetime.now().year
    
    if semester % 2 == 1:
        start_month = 9
        end_month = 12
    else: 
        start_month = 2
        end_month = 6
    
    start_date = date(year, start_month, 1)
    
    if end_month == 12:
        end_date = date(year, 12, 31)
    else:
        if end_month in [1, 3, 5, 7, 8, 10, 12]:
            end_date = date(year, end_month, 31)
        elif end_month in [4, 6, 9, 11]:
            end_date = date(year, end_month, 30)
        else:
            end_date = date(year, 2, 28)
    
    return start_date, end_date


# ===================== СТАТИСТИКА =====================

def get_group_statistics(group_id):
    """
    Получить статистику по группе
    
    Args:
        group_id: ID группы
    
    Returns:
        dict: Статистика группы
    """
    from app.models import Group
    
    group = Group.query.get(group_id)
    if not group:
        return None
    
    students = Student.query.filter_by(group_id=group_id).all()
    
    if not students:
        return {
            'students_count': 0,
            'avg_attendance': 0,
            'avg_rating': 0,
            'passed': 0,
            'failed': 0,
            'pass_rate': 0
        }
    
    total_attendance = 0
    total_rating = 0
    passed = 0
    failed = 0
    
    for student in students:
        total_attendance += student.get_attendance_percentage()
        rating = calculate_student_rating(student.id)
        total_rating += rating['total']
        
        if rating['passed']:
            passed += 1
        else:
            failed += 1
    
    students_count = len(students)
    
    return {
        'students_count': students_count,
        'avg_attendance': round(total_attendance / students_count, 2),
        'avg_rating': round(total_rating / students_count, 2),
        'passed': passed,
        'failed': failed,
        'pass_rate': round((passed / students_count * 100), 2)
    }


def get_medical_groups_distribution():
    """
    Получить распределение студентов по медицинским группам
    
    Returns:
        dict: Распределение по медицинским группам
    """
    distribution = db.session.query(
        Student.medical_group,
        db.func.count(Student.id).label('count')
    ).group_by(Student.medical_group).all()
    
    total = Student.query.count()
    
    result = {}
    for med_group, count in distribution:
        percentage = round((count / total * 100), 2) if total > 0 else 0
        result[med_group] = {
            'count': count,
            'percentage': percentage
        }
    
    return result


# ===================== ВАЛИДАЦИЯ =====================

def validate_student_number(student_number, student_id=None):
    """
    Проверить уникальность номера студенческого билета
    
    Args:
        student_number: Номер студенческого
        student_id: ID студента (для обновления)
    
    Returns:
        bool: True если номер уникален
    """
    student = Student.query.filter_by(student_number=student_number).first()
    
    if not student:
        return True
    
    if student_id and student.id == student_id:
        return True
    
    return False


def validate_email(email, user_id=None):
    """
    Проверить уникальность email
    
    Args:
        email: Email адрес
        user_id: ID пользователя (для обновления)
    
    Returns:
        bool: True если email уникален
    """
    from app.models import User
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return True
    
    if user_id and user.id == user_id:
        return True
    
    return False


# ===================== HELPER ФУНКЦИИ ДЛЯ ШАБЛОНОВ =====================

def get_status_badge_class(status):
    """
    Получить CSS класс для badge статуса
    
    Args:
        status: Статус (присутствовал, отсутствовал, назначено, и т.д.)
    
    Returns:
        str: Bootstrap класс
    """
    status_classes = {
        'присутствовал': 'success',
        'отсутствовал': 'danger',
        'уважительная': 'warning',
        'назначено': 'info',
        'выполнено': 'success',
        'просрочено': 'danger',
        'основная': 'primary',
        'подготовительная': 'info',
        'СМГ': 'warning',
        'освобождение': 'secondary'
    }
    return status_classes.get(status, 'secondary')


def get_rating_badge_class(points):
    """
    Получить CSS класс для badge рейтинга
    
    Args:
        points: Количество баллов
    
    Returns:
        str: Bootstrap класс
    """
    if points >= 90:
        return 'success'
    elif points >= 75:
        return 'primary'
    elif points >= 60:
        return 'warning'
    else:
        return 'danger'


def truncate_string(text, length=50, suffix='...'):
    """
    Обрезать строку до указанной длины
    
    Args:
        text: Исходный текст
        length: Максимальная длина
        suffix: Суффикс для обрезанного текста
    
    Returns:
        str: Обрезанный текст
    """
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix