from app.models import User, Student, Attendance, StandardResult
from datetime import date


def test_user_password_hashing(app):
    """Тест хеширования пароля"""
    with app.app_context():
        user = User(
            email='test@test.com',
            full_name='Test User',
            role='teacher'
        )
        user.set_password('password123')
        
        assert user.password_hash is not None
        assert user.password_hash != 'password123'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')


def test_student_attendance_percentage(app):
    """Тест расчета процента посещаемости"""
    with app.app_context():
        from app import db
        from app.models import Group, Faculty, Specialty, EducationForm, User
        
        # Создать необходимые данные
        faculty = Faculty(code='TEST', name='Test Faculty')
        db.session.add(faculty)
        db.session.flush()
        
        specialty = Specialty(code='00.00.00', name='Test Specialty', faculty_id=faculty.id)
        db.session.add(specialty)
        db.session.flush()
        
        edu_form = EducationForm(name='Test Form', duration_years=4)
        db.session.add(edu_form)
        db.session.flush()
        
        teacher = User(email='teacher@test.com', full_name='Teacher', role='teacher')
        teacher.set_password('pass')
        db.session.add(teacher)
        db.session.flush()
        
        group = Group(
            name='TEST-101',
            course=1,
            semester=1,
            specialty_id=specialty.id,
            education_form_id=edu_form.id,
            teacher_id=teacher.id
        )
        db.session.add(group)
        db.session.flush()
        
        student = Student(
            full_name='Test Student',
            student_number='TEST001',
            gender='male',
            group_id=group.id
        )
        db.session.add(student)
        db.session.flush()
        
        # Создать записи посещаемости
        for i in range(10):
            status = 'присутствовал' if i < 8 else 'отсутствовал'
            attendance = Attendance(
                student_id=student.id,
                date=date(2025, 1, i + 1),
                status=status,
                created_by=teacher.id
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        # Проверить процент посещаемости
        percentage = student.get_attendance_percentage()
        assert percentage == 80.0


def test_student_to_dict(app):
    """Тест сериализации студента"""
    with app.app_context():
        from app import db
        from app.models import Group, Faculty, Specialty, EducationForm, User
        
        # Создать минимальные необходимые данные
        faculty = Faculty(code='TEST', name='Test')
        db.session.add(faculty)
        db.session.flush()
        
        specialty = Specialty(code='00.00.00', name='Test', faculty_id=faculty.id)
        db.session.add(specialty)
        db.session.flush()
        
        edu_form = EducationForm(name='Test', duration_years=4)
        db.session.add(edu_form)
        db.session.flush()
        
        teacher = User(email='t@t.com', full_name='T', role='teacher')
        teacher.set_password('p')
        db.session.add(teacher)
        db.session.flush()
        
        group = Group(
            name='T-1',
            course=1,
            semester=1,
            specialty_id=specialty.id,
            education_form_id=edu_form.id,
            teacher_id=teacher.id
        )
        db.session.add(group)
        db.session.flush()
        
        student = Student(
            full_name='Test Student',
            student_number='T001',
            gender='male',
            group_id=group.id
        )
        db.session.add(student)
        db.session.commit()
        
        data = student.to_dict()
        
        assert 'id' in data
        assert data['full_name'] == 'Test Student'
        assert data['student_number'] == 'T001'
        assert data['gender'] == 'male'