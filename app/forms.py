from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SelectField, 
                     IntegerField, FloatField, DateField, TextAreaField, FileField)
from wtforms.validators import (DataRequired, Email, Length, Optional, 
                               ValidationError, NumberRange, EqualTo)
from flask_wtf.file import FileAllowed
from app.models import User, Student, Group, Faculty, Specialty, EducationForm
from datetime import date


# ===================== АВТОРИЗАЦИЯ =====================

class LoginForm(FlaskForm):
    """Форма входа в систему"""
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Неверный формат email')
    ], render_kw={'placeholder': 'email@example.com', 'autocomplete': 'email'})
    
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен')
    ], render_kw={'placeholder': 'Введите пароль', 'autocomplete': 'current-password'})
    
    remember = BooleanField('Запомнить меня')


class ChangePasswordForm(FlaskForm):
    """Форма смены пароля"""
    old_password = PasswordField('Текущий пароль', validators=[
        DataRequired(message='Текущий пароль обязателен')
    ], render_kw={'placeholder': 'Введите текущий пароль'})
    
    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(message='Новый пароль обязателен'),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ], render_kw={'placeholder': 'Минимум 6 символов'})
    
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[
        DataRequired(message='Подтверждение пароля обязательно'),
        EqualTo('new_password', message='Пароли не совпадают')
    ], render_kw={'placeholder': 'Повторите новый пароль'})


class EditProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    full_name = StringField('ФИО', validators=[
        DataRequired(message='ФИО обязательно'),
        Length(min=3, max=200, message='ФИО должно быть от 3 до 200 символов')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Неверный формат email')
    ])


# ===================== ПОЛЬЗОВАТЕЛИ =====================

class UserForm(FlaskForm):
    """Форма создания/редактирования пользователя"""
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Неверный формат email')
    ], render_kw={'placeholder': 'email@muiv.ru'})
    
    full_name = StringField('ФИО', validators=[
        DataRequired(message='ФИО обязательно'),
        Length(min=3, max=200, message='ФИО должно быть от 3 до 200 символов')
    ], render_kw={'placeholder': 'Иванов Иван Иванович'})
    
    password = PasswordField('Пароль', validators=[
        Optional(),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ], render_kw={'placeholder': 'Минимум 6 символов (оставьте пустым при редактировании)'})
    
    role = SelectField('Роль', choices=[
        ('admin', 'Администратор'),
        ('teacher', 'Преподаватель'),
        ('department_head', 'Заведующий кафедрой')
    ], validators=[DataRequired(message='Роль обязательна')])
    
    is_active = BooleanField('Активен', default=True)
    
    def __init__(self, user_id=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
    
    def validate_email(self, field):
        """Проверка уникальности email"""
        user = User.query.filter_by(email=field.data).first()
        if user:
            if self.user_id is None or user.id != self.user_id:
                raise ValidationError('Пользователь с таким email уже существует')


# ===================== ФАКУЛЬТЕТЫ И СПЕЦИАЛЬНОСТИ =====================

class FacultyForm(FlaskForm):
    """Форма создания/редактирования факультета"""
    code = StringField('Код факультета', validators=[
        DataRequired(message='Код обязателен'),
        Length(min=2, max=50, message='Код должен быть от 2 до 50 символов')
    ], render_kw={'placeholder': 'ФИТ'})
    
    name = StringField('Название факультета', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=3, max=200, message='Название должно быть от 3 до 200 символов')
    ], render_kw={'placeholder': 'Факультет информационных технологий'})
    
    def __init__(self, faculty_id=None, *args, **kwargs):
        super(FacultyForm, self).__init__(*args, **kwargs)
        self.faculty_id = faculty_id
    
    def validate_code(self, field):
        """Проверка уникальности кода"""
        faculty = Faculty.query.filter_by(code=field.data).first()
        if faculty:
            if self.faculty_id is None or faculty.id != self.faculty_id:
                raise ValidationError('Факультет с таким кодом уже существует')


class SpecialtyForm(FlaskForm):
    """Форма создания/редактирования специальности"""
    code = StringField('Код специальности', validators=[
        DataRequired(message='Код обязателен'),
        Length(min=5, max=50, message='Код должен быть от 5 до 50 символов')
    ], render_kw={'placeholder': '09.03.03'})
    
    name = StringField('Название специальности', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=3, max=200, message='Название должно быть от 3 до 200 символов')
    ], render_kw={'placeholder': 'Прикладная информатика'})
    
    faculty_id = SelectField('Факультет', coerce=int, validators=[
        DataRequired(message='Факультет обязателен')
    ])
    
    def __init__(self, specialty_id=None, *args, **kwargs):
        super(SpecialtyForm, self).__init__(*args, **kwargs)
        self.specialty_id = specialty_id
        # Загрузить факультеты
        self.faculty_id.choices = [
            (f.id, f'{f.code} - {f.name}') for f in Faculty.query.order_by(Faculty.name).all()
        ]
    
    def validate_code(self, field):
        """Проверка уникальности кода"""
        specialty = Specialty.query.filter_by(code=field.data).first()
        if specialty:
            if self.specialty_id is None or specialty.id != self.specialty_id:
                raise ValidationError('Специальность с таким кодом уже существует')


class EducationFormForm(FlaskForm):
    """Форма создания/редактирования формы обучения"""
    name = StringField('Название формы обучения', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=3, max=100, message='Название должно быть от 3 до 100 символов')
    ], render_kw={'placeholder': 'Очная'})
    
    duration_years = FloatField('Продолжительность (лет)', validators=[
        DataRequired(message='Продолжительность обязательна'),
        NumberRange(min=1, max=10, message='Продолжительность должна быть от 1 до 10 лет')
    ], render_kw={'placeholder': '4'})
    
    def __init__(self, form_id=None, *args, **kwargs):
        super(EducationFormForm, self).__init__(*args, **kwargs)
        self.form_id = form_id
    
    def validate_name(self, field):
        """Проверка уникальности названия"""
        form = EducationForm.query.filter_by(name=field.data).first()
        if form:
            if self.form_id is None or form.id != self.form_id:
                raise ValidationError('Форма обучения с таким названием уже существует')


# ===================== ГРУППЫ =====================

class GroupForm(FlaskForm):
    """Форма создания/редактирования группы"""
    name = StringField('Номер группы', validators=[
        DataRequired(message='Номер группы обязателен'),
        Length(min=2, max=100, message='Номер группы должен быть от 2 до 100 символов')
    ], render_kw={'placeholder': 'ИТ-301'})
    
    course = IntegerField('Курс', validators=[
        DataRequired(message='Курс обязателен'),
        NumberRange(min=1, max=6, message='Курс должен быть от 1 до 6')
    ], render_kw={'placeholder': '3'})
    
    semester = IntegerField('Семестр', validators=[
        DataRequired(message='Семестр обязателен'),
        NumberRange(min=1, max=12, message='Семестр должен быть от 1 до 12')
    ], render_kw={'placeholder': '5'})
    
    specialty_id = SelectField('Специальность', coerce=int, validators=[
        DataRequired(message='Специальность обязательна')
    ])
    
    education_form_id = SelectField('Форма обучения', coerce=int, validators=[
        DataRequired(message='Форма обучения обязательна')
    ])
    
    teacher_id = SelectField('Преподаватель', coerce=int, validators=[Optional()])
    
    def __init__(self, group_id=None, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.group_id = group_id
        
        # Загрузить специальности
        self.specialty_id.choices = [
            (s.id, f'{s.code} - {s.name}') 
            for s in Specialty.query.order_by(Specialty.name).all()
        ]
        
        # Загрузить формы обучения
        self.education_form_id.choices = [
            (f.id, f'{f.name} ({f.duration_years} лет)') 
            for f in EducationForm.query.order_by(EducationForm.name).all()
        ]
        
        # Загрузить преподавателей
        self.teacher_id.choices = [(0, '-- Не назначен --')] + [
            (t.id, t.full_name) 
            for t in User.query.filter_by(role='teacher', is_active=True).order_by(User.full_name).all()
        ]
    
    def validate_name(self, field):
        """Проверка уникальности названия"""
        group = Group.query.filter_by(name=field.data).first()
        if group:
            if self.group_id is None or group.id != self.group_id:
                raise ValidationError('Группа с таким названием уже существует')


# ===================== СТУДЕНТЫ =====================

class StudentForm(FlaskForm):
    """Форма создания/редактирования студента"""
    full_name = StringField('ФИО', validators=[
        DataRequired(message='ФИО обязательно'),
        Length(min=3, max=200, message='ФИО должно быть от 3 до 200 символов')
    ], render_kw={'placeholder': 'Иванов Иван Иванович'})
    
    student_number = StringField('Номер студенческого билета', validators=[
        DataRequired(message='Номер студенческого билета обязателен'),
        Length(min=5, max=50, message='Номер должен быть от 5 до 50 символов')
    ], render_kw={'placeholder': 'ГБ123001'})
    
    gender = SelectField('Пол', choices=[
        ('male', 'Мужской'),
        ('female', 'Женский')
    ], validators=[DataRequired(message='Пол обязателен')])
    
    birth_date = DateField('Дата рождения', validators=[Optional()], format='%Y-%m-%d')
    
    medical_group = SelectField('Медицинская группа', choices=[
        ('основная', 'Основная'),
        ('подготовительная', 'Подготовительная'),
        ('СМГ', 'Специальная медицинская группа'),
        ('освобождение', 'Освобождение')
    ], default='основная', validators=[DataRequired()])
    
    group_id = SelectField('Группа', coerce=int, validators=[
        DataRequired(message='Группа обязательна')
    ])
    
    def __init__(self, student_id=None, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.student_id = student_id
        
        # Загрузить группы
        self.group_id.choices = [
            (g.id, g.name) for g in Group.query.order_by(Group.name).all()
        ]
    
    def validate_student_number(self, field):
        """Проверка уникальности номера студенческого"""
        student = Student.query.filter_by(student_number=field.data).first()
        if student:
            if self.student_id is None or student.id != self.student_id:
                raise ValidationError('Студент с таким номером уже существует')
    
    def validate_birth_date(self, field):
        """Проверка даты рождения"""
        if field.data and field.data > date.today():
            raise ValidationError('Дата рождения не может быть в будущем')


class StudentSearchForm(FlaskForm):
    """Форма поиска студента"""
    full_name = StringField('ФИО', validators=[Optional()], 
                           render_kw={'placeholder': 'Введите ФИО студента'})
    
    student_number = StringField('Номер студенческого', validators=[Optional()],
                                render_kw={'placeholder': 'Введите номер студенческого билета'})


# ===================== МОДУЛИ И ТЕМЫ =====================

class ModuleForm(FlaskForm):
    """Форма создания/редактирования модуля"""
    number = IntegerField('Номер модуля', validators=[
        DataRequired(message='Номер модуля обязателен'),
        NumberRange(min=1, max=10, message='Номер должен быть от 1 до 10')
    ])
    
    name = StringField('Название модуля', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=5, max=200, message='Название должно быть от 5 до 200 символов')
    ], render_kw={'placeholder': 'Спортивно-оздоровительная деятельность'})
    
    max_points = IntegerField('Максимум баллов', validators=[
        DataRequired(message='Максимум баллов обязателен'),
        NumberRange(min=1, max=100, message='Баллы должны быть от 1 до 100')
    ], render_kw={'placeholder': '35'})


class ThemeForm(FlaskForm):
    """Форма создания/редактирования темы"""
    name = StringField('Название темы', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=3, max=200, message='Название должно быть от 3 до 200 символов')
    ], render_kw={'placeholder': 'Легкая атлетика'})
    
    module_id = SelectField('Модуль', coerce=int, validators=[
        DataRequired(message='Модуль обязателен')
    ])
    
    max_points = IntegerField('Максимум баллов', validators=[
        DataRequired(message='Максимум баллов обязателен'),
        NumberRange(min=1, max=50, message='Баллы должны быть от 1 до 50')
    ], render_kw={'placeholder': '20'})
    
    def __init__(self, *args, **kwargs):
        super(ThemeForm, self).__init__(*args, **kwargs)
        from app.models import Module
        self.module_id.choices = [
            (m.id, f'Модуль {m.number}: {m.name}') 
            for m in Module.query.order_by(Module.number).all()
        ]


# ===================== НОРМАТИВЫ =====================

class StandardForm(FlaskForm):
    """Форма создания/редактирования норматива"""
    name = StringField('Название норматива', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=3, max=200, message='Название должно быть от 3 до 200 символов')
    ], render_kw={'placeholder': 'Бег 100м'})
    
    theme_id = SelectField('Тема', coerce=int, validators=[
        DataRequired(message='Тема обязательна')
    ])
    
    unit = StringField('Единица измерения', validators=[
        DataRequired(message='Единица измерения обязательна'),
        Length(max=50, message='Единица измерения должна быть не более 50 символов')
    ], render_kw={'placeholder': 'секунды, метры, раз'})
    
    comparison_type = SelectField('Тип сравнения', choices=[
        ('less_better', 'Меньше - лучше (время, секунды)'),
        ('more_better', 'Больше - лучше (расстояние, количество)')
    ], validators=[DataRequired(message='Тип сравнения обязателен')])
    
    is_active = BooleanField('Активен', default=True)
    
    def __init__(self, *args, **kwargs):
        super(StandardForm, self).__init__(*args, **kwargs)
        from app.models import Theme
        self.theme_id.choices = [
            (t.id, f'{t.module.name} - {t.name}') 
            for t in Theme.query.join(Theme.module).all()
        ]


class StandardScaleForm(FlaskForm):
    """Форма создания/редактирования оценочной шкалы"""
    standard_id = SelectField('Норматив', coerce=int, validators=[
        DataRequired(message='Норматив обязателен')
    ])
    
    gender = SelectField('Пол', choices=[
        ('male', 'Мужской'),
        ('female', 'Женский')
    ], validators=[DataRequired(message='Пол обязателен')])
    
    points = IntegerField('Баллы', validators=[
        DataRequired(message='Баллы обязательны'),
        NumberRange(min=1, max=5, message='Баллы должны быть от 1 до 5')
    ])
    
    min_value = FloatField('Минимальное значение', validators=[Optional()])
    max_value = FloatField('Максимальное значение', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(StandardScaleForm, self).__init__(*args, **kwargs)
        from app.models import Standard
        self.standard_id.choices = [
            (s.id, f'{s.name} ({s.unit})') 
            for s in Standard.query.filter_by(is_active=True).all()
        ]


# ===================== ПОСЕЩАЕМОСТЬ =====================

class AttendanceForm(FlaskForm):
    """Форма отметки посещаемости"""
    date = DateField('Дата занятия', validators=[
        DataRequired(message='Дата обязательна')
    ], format='%Y-%m-%d', default=date.today)
    
    def validate_date(self, field):
        """Проверка даты"""
        if field.data > date.today():
            raise ValidationError('Дата занятия не может быть в будущем')


# ===================== РЕЗУЛЬТАТЫ НОРМАТИВОВ =====================

class StandardResultForm(FlaskForm):
    """Форма внесения результата норматива"""
    result_value = FloatField('Результат', validators=[
        DataRequired(message='Результат обязателен'),
        NumberRange(min=0, message='Результат не может быть отрицательным')
    ])
    
    date = DateField('Дата', validators=[
        DataRequired(message='Дата обязательна')
    ], format='%Y-%m-%d', default=date.today)
    
    def validate_date(self, field):
        """Проверка даты"""
        if field.data > date.today():
            raise ValidationError('Дата не может быть в будущем')


# ===================== ИНДИВИДУАЛЬНЫЕ ЗАДАНИЯ =====================

class AssignmentForm(FlaskForm):
    """Форма создания/редактирования индивидуального задания"""
    student_id = SelectField('Студент', coerce=int, validators=[
        DataRequired(message='Студент обязателен')
    ])
    
    type = SelectField('Тип задания', choices=[
        ('реферат', 'Реферат'),
        ('пересдача', 'Пересдача норматива'),
        ('доп_занятия', 'Дополнительные занятия'),
        ('другое', 'Другое')
    ], validators=[DataRequired(message='Тип задания обязателен')])
    
    title = StringField('Название задания', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=5, max=300, message='Название должно быть от 5 до 300 символов')
    ], render_kw={'placeholder': 'Реферат на тему...'})
    
    description = TextAreaField('Описание', validators=[Optional()],
                               render_kw={'rows': 4, 'placeholder': 'Подробное описание задания'})
    
    deadline = DateField('Срок сдачи', validators=[
        DataRequired(message='Срок сдачи обязателен')
    ], format='%Y-%m-%d')
    
    bonus_points = IntegerField('Бонусные баллы', default=0, validators=[
        Optional(),
        NumberRange(min=0, max=20, message='Бонусные баллы должны быть от 0 до 20')
    ])
    
    status = SelectField('Статус', choices=[
        ('назначено', 'Назначено'),
        ('выполнено', 'Выполнено'),
        ('просрочено', 'Просрочено')
    ], default='назначено')
    
    def __init__(self, group_id=None, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        
        if group_id:
            students = Student.query.filter_by(group_id=group_id).order_by(Student.full_name).all()
        else:
            students = Student.query.order_by(Student.full_name).all()
        
        self.student_id.choices = [
            (s.id, f'{s.full_name} ({s.student_number})') for s in students
        ]
    
    def validate_deadline(self, field):
        """Проверка срока сдачи"""
        if field.data < date.today():
            raise ValidationError('Срок сдачи не может быть в прошлом')


# ===================== ВЕДОМОСТИ =====================

class StatementForm(FlaskForm):
    """Форма создания ведомости"""
    
    group_id = SelectField(
        'Группа',
        coerce=int,
        validators=[DataRequired(message='Выберите группу')]
    )
    
    semester = IntegerField(
        'Семестр',
        validators=[
            DataRequired(message='Укажите семестр'),
            NumberRange(min=1, max=12, message='Семестр должен быть от 1 до 12')
        ]
    )
    
    type = SelectField(
        'Тип',
        choices=[
            ('зачет', 'Зачёт'),
            ('экзамен', 'Экзамен')
        ],
        validators=[DataRequired(message='Выберите тип аттестации')]
    )
    
    date = DateField(
        'Дата',
        format='%Y-%m-%d',
        validators=[DataRequired(message='Укажите дату')]
    )
    
    dean_name = StringField(
        'ФИО декана',
        validators=[
            DataRequired(message='Укажите ФИО декана'),
            Length(min=5, max=200, message='ФИО должно содержать от 5 до 200 символов')
        ]
    )
    
    file = FileField(
        'Файл',
        validators=[
            FileAllowed(['xlsx', 'xls', 'pdf'], message='Разрешены только файлы .xlsx, .xls, .pdf')
        ]
    )


# ===================== ИМПОРТ =====================

class ImportStudentsForm(FlaskForm):
    """Форма импорта студентов из Excel"""
    file = FileField('Файл Excel', validators=[
        DataRequired(message='Выберите файл'),
        FileAllowed(['xlsx', 'xls'], message='Только файлы Excel (.xlsx, .xls)')
    ])
    
    group_id = SelectField('Группа по умолчанию (необязательно)', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ImportStudentsForm, self).__init__(*args, **kwargs)
        self.group_id.choices = [(0, '-- Не выбрано --')] + [
            (g.id, g.name) for g in Group.query.order_by(Group.name).all()
        ]