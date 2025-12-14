from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Фабрика приложения Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Настройка Login Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'warning'
    
    # Настройка логирования
    setup_logging(app)
    
    # Импорт моделей
    from app import models
    
    # Регистрация blueprints
    register_blueprints(app)
    
    # Создание необходимых папок
    create_directories(app)
    
    # Регистрация фильтров для шаблонов
    register_template_filters(app)
    
    # Регистрация context processors
    register_context_processors(app)
    
    # Главная страница
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Страница "О системе"
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    # Обработчики ошибок
    register_error_handlers(app)
    
    # Проверка дедлайнов при запуске приложения
    with app.app_context():
        try:
            from app.utils import check_assignment_deadlines
            check_assignment_deadlines()
        except Exception as e:
            app.logger.warning(f'Не удалось проверить дедлайны: {e}')
    
    return app


def register_blueprints(app):
    """Регистрация всех blueprints"""
    from app.routes import auth, admin, teacher, student, department_head, main
    
    # Главные маршруты
    if hasattr(main, 'bp'):
        app.register_blueprint(main.bp)
    
    # Авторизация
    app.register_blueprint(auth.bp)
    
    # Администратор
    app.register_blueprint(admin.bp)
    
    # Преподаватель
    app.register_blueprint(teacher.bp)
    
    # Студент
    app.register_blueprint(student.bp)
    
    # Заведующий кафедрой
    app.register_blueprint(department_head.bp)
    
    app.logger.info('Все blueprints успешно зарегистрированы')


def create_directories(app):
    """Создание необходимых папок для загрузок"""
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    
    directories = [
        upload_folder,
        os.path.join(upload_folder, 'photos'),
        os.path.join(upload_folder, 'documents'),
        os.path.join(upload_folder, 'statements'),
        os.path.join(upload_folder, 'imports'),
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    app.logger.info('Все необходимые папки созданы')


def register_template_filters(app):
    """Регистрация пользовательских фильтров для Jinja2"""
    from app.utils import (format_date, format_datetime, get_russian_month,
                          get_status_badge_class, get_rating_badge_class,
                          truncate_string)
    
    @app.template_filter('format_date')
    def format_date_filter(date_obj, format='%d.%m.%Y'):
        """Форматирование даты: {{ date|format_date }}"""
        return format_date(date_obj, format)
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(datetime_obj, format='%d.%m.%Y %H:%M'):
        """Форматирование даты и времени: {{ datetime|format_datetime }}"""
        return format_datetime(datetime_obj, format)
    
    @app.template_filter('russian_month')
    def russian_month_filter(month_number):
        """Название месяца на русском: {{ 3|russian_month }}"""
        return get_russian_month(month_number)
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """CSS класс для badge статуса: {{ status|status_badge }}"""
        return get_status_badge_class(status)
    
    @app.template_filter('rating_badge')
    def rating_badge_filter(points):
        """CSS класс для badge рейтинга: {{ points|rating_badge }}"""
        return get_rating_badge_class(points)
    
    @app.template_filter('truncate')
    def truncate_filter(text, length=50, suffix='...'):
        """Обрезка текста: {{ text|truncate(100) }}"""
        return truncate_string(text, length, suffix)
    
    @app.template_filter('round2')
    def round2_filter(value):
        """Округление до 2 знаков: {{ 3.14159|round2 }}"""
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return value
    
    @app.template_filter('percent')
    def percent_filter(value, decimals=1):
        """Форматирование процентов: {{ 0.85|percent }}"""
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return value
    
    app.logger.info('Фильтры шаблонов зарегистрированы')


def register_context_processors(app):
    """Регистрация context processors для доступа в шаблонах"""
    
    @app.context_processor
    def inject_user():
        """Сделать текущего пользователя доступным во всех шаблонах"""
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_csrf_token():
        """Добавить функцию csrf_token в шаблоны"""
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    @app.context_processor
    def inject_app_info():
        """Информация о приложении"""
        return dict(
            app_name='Система автоматизации преподавателя физической культуры',
            app_short_name='PE System',
            app_version='1.0.0',
            university_name='Московский университет им. С.Ю. Витте'
        )
    
    @app.context_processor
    def inject_config():
        """Конфигурационные значения"""
        return dict(
            ATTENDANCE_MAX_POINTS=app.config.get('ATTENDANCE_MAX_POINTS', 30),
            MODULE_MAX_POINTS=app.config.get('MODULE_MAX_POINTS', 35),
            TOTAL_MAX_POINTS=app.config.get('TOTAL_MAX_POINTS', 100),
            PASSING_SCORE=app.config.get('PASSING_SCORE', 60)
        )
    
    @app.context_processor
    def inject_nav_utils():
        """Утилиты для навигации"""
        def is_active(endpoint):
            """Проверка активности пункта меню"""
            return 'active' if request.endpoint and request.endpoint.startswith(endpoint) else ''
        
        return dict(is_active=is_active)
    
    @app.context_processor
    def inject_date_utils():
        """Утилиты для работы с датами"""
        from datetime import date, datetime
        return dict(
            today=date.today(),
            now=datetime.now()
        )
    
    app.logger.info('Context processors зарегистрированы')


def register_error_handlers(app):
    """Регистрация обработчиков ошибок"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Ошибка 400 - Неверный запрос"""
        app.logger.warning(f'Bad Request: {error}')
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        """Ошибка 403 - Доступ запрещен"""
        app.logger.warning(f'Forbidden: {error}')
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Ошибка 404 - Страница не найдена"""
        app.logger.info(f'Page not found: {request.url}')
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Ошибка 500 - Внутренняя ошибка сервера"""
        db.session.rollback()
        app.logger.error(f'Internal Server Error: {error}', exc_info=True)
        return render_template('errors/500.html', error=error), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Ошибка 503 - Сервис недоступен"""
        app.logger.error(f'Service Unavailable: {error}')
        return render_template('errors/503.html', error=error), 503
    
    app.logger.info('Обработчики ошибок зарегистрированы')


def setup_logging(app):
    """Настройка логирования приложения"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/pe_system.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('PE System startup')


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя по ID для Flask-Login"""
    from app.models import User
    return User.query.get(int(user_id))


def register_cli_commands(app):
    """Регистрация CLI команд"""
    
    @app.cli.command()
    def init_db():
        """Инициализация базы данных"""
        db.create_all()
        print('База данных инициализирована')
    
    @app.cli.command()
    def seed_db():
        """Заполнение БД тестовыми данными"""
        from seed_data import seed_all_data
        seed_all_data()
        print('База данных заполнена тестовыми данными')
    
    @app.cli.command()
    def check_deadlines():
        """Проверка и обновление просроченных заданий"""
        from app.utils import check_assignment_deadlines
        count = check_assignment_deadlines()
        print(f'Обновлено просроченных заданий: {count}')
    
    @app.cli.command()
    def create_admin():
        """Создание администратора"""
        from app.models import User
        
        email = input('Email: ')
        full_name = input('ФИО: ')
        password = input('Пароль: ')
        
        if User.query.filter_by(email=email).first():
            print('Пользователь с таким email уже существует')
            return
        
        admin = User(
            email=email,
            full_name=full_name,
            role='admin',
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f'Администратор {full_name} успешно создан')
    
    @app.cli.command()
    def list_routes():
        """Показать все маршруты приложения"""
        import urllib
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {rule}")
            output.append(line)
        
        for line in sorted(output):
            print(line)