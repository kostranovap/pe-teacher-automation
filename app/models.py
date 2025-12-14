from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    groups = db.relationship('Group', backref='teacher', lazy='dynamic', foreign_keys='Group.teacher_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Faculty(db.Model):
    __tablename__ = 'faculties'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    specialties = db.relationship('Specialty', backref='faculty', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'specialties_count': self.specialties.count()
        }


class Specialty(db.Model):
    __tablename__ = 'specialties'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    groups = db.relationship('Group', backref='specialty', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'faculty_id': self.faculty_id,
            'faculty': self.faculty.to_dict() if self.faculty else None,
            'groups_count': self.groups.count()
        }


class EducationForm(db.Model):
    __tablename__ = 'education_forms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    duration_years = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    groups = db.relationship('Group', backref='education_form', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'duration_years': self.duration_years,
            'groups_count': self.groups.count()
        }


class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    course = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), nullable=False)
    education_form_id = db.Column(db.Integer, db.ForeignKey('education_forms.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    students = db.relationship('Student', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    statements = db.relationship('Statement', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'course': self.course,
            'semester': self.semester,
            'specialty': self.specialty.to_dict() if self.specialty else None,
            'education_form': self.education_form.to_dict() if self.education_form else None,
            'teacher': self.teacher.to_dict() if self.teacher else None,
            'students_count': self.students.count()
        }


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False, index=True)
    student_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    gender = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.Date)
    medical_group = db.Column(db.String(50), default='основная')
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('StandardResult', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_attendance_percentage(self):
        total = self.attendances.count()
        if total == 0:
            return 0
        present = self.attendances.filter(
            (Attendance.status == 'присутствовал') | (Attendance.status == 'уважительная')
        ).count()
        return round((present / total) * 100, 1)
    
    def to_dict(self, include_rating=False):
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'student_number': self.student_number,
            'gender': self.gender,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'medical_group': self.medical_group,
            'group_id': self.group_id,
            'group': self.group.to_dict() if self.group else None,
            'photo_path': self.photo_path,
            'attendance_percentage': self.get_attendance_percentage()
        }
        
        if include_rating:
            from app.utils import calculate_student_rating
            data['rating'] = calculate_student_rating(self.id)
        
        return data


class Module(db.Model):
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    max_points = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    themes = db.relationship('Theme', backref='module', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'name': self.name,
            'max_points': self.max_points,
            'themes': [t.to_dict() for t in self.themes.all()]
        }


class Theme(db.Model):
    __tablename__ = 'themes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    max_points = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    standards = db.relationship('Standard', backref='theme', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'module_id': self.module_id,
            'max_points': self.max_points,
            'standards_count': self.standards.count()
        }


class Standard(db.Model):
    __tablename__ = 'standards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    comparison_type = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(1), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    scales = db.relationship('StandardScale', backref='standard', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('StandardResult', backref='standard', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'theme_id': self.theme_id,
            'theme': self.theme.to_dict() if self.theme else None,
            'unit': self.unit,
            'comparison_type': self.comparison_type,
            'is_active': self.is_active
        }


class StandardScale(db.Model):
    __tablename__ = 'standard_scales'
    
    id = db.Column(db.Integer, primary_key=True)
    standard_id = db.Column(db.Integer, db.ForeignKey('standards.id'), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    min_value = db.Column(db.Float, nullable=False)
    max_value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'standard_id': self.standard_id,
            'gender': self.gender,
            'points': self.points,
            'min_value': self.min_value,
            'max_value': self.max_value
        }


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by])
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='unique_student_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student': self.student.to_dict() if self.student else None,
            'date': self.date.isoformat(),
            'status': self.status,
            'comment': self.comment,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StandardResult(db.Model):
    __tablename__ = 'standard_results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    standard_id = db.Column(db.Integer, db.ForeignKey('standards.id'), nullable=False)
    result_value = db.Column(db.Float, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'standard_id': self.standard_id,
            'standard': self.standard.to_dict() if self.standard else None,
            'result_value': self.result_value,
            'points': self.points,
            'date': self.date.isoformat(),
            'attempt_number': self.attempt_number,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='назначено')
    bonus_points = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student': self.student.to_dict() if self.student else None,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.isoformat(),
            'status': self.status,
            'bonus_points': self.bonus_points,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None
        }


class Statement(db.Model):
    __tablename__ = 'statements'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), unique=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dean_name = db.Column(db.String(200))
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'group_id': self.group_id,
            'group': self.group.to_dict() if self.group else None,
            'semester': self.semester,
            'type': self.type,
            'date': self.date.isoformat(),
            'teacher_id': self.teacher_id,
            'teacher': self.teacher.to_dict() if self.teacher else None,
            'dean_name': self.dean_name,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }