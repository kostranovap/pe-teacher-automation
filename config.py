import os
from datetime import timedelta


class Config:
    """Базовая конфигурация"""
    
    # Секретный ключ для сессий
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # База данных
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'postgresql://postgres:postgres@localhost:5432/pe_system'
    SQLALCHEMY_DATABASE_URI = 'postgresql://pe_admin:SecurePassword123!@localhost:5432/pe_system_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Загрузка файлов
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB максимум
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xlsx', 'xls', 'docx', 'doc'}
    
    # Балльно-рейтинговая система
    ATTENDANCE_MAX_POINTS = 30  # Максимум баллов за посещаемость
    MODULE_MAX_POINTS = 35      # Максимум баллов за модуль
    TOTAL_MAX_POINTS = 100      # Максимум баллов всего
    PASSING_SCORE = 60          # Минимум для зачета
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Токен не истекает
    
    # Timezone
    TIMEZONE = 'Europe/Moscow'
    
    # Пагинация
    ITEMS_PER_PAGE = 20
    
    # Логирование
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    TESTING = False


class ProductionConfig(Config):
    """Конфигурация для production"""
    DEBUG = False
    TESTING = False
    
    # В production используйте переменные окружения
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Безопасность
    SESSION_COOKIE_SECURE = True
    
    # Логирование
    LOG_TO_STDOUT = True


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    DEBUG = True
    
    # Использовать отдельную тестовую БД
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/pe_system_test'
    
    # Отключить CSRF для тестов
    WTF_CSRF_ENABLED = False


# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}