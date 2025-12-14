import pytest
from app import create_app, db
from app.models import User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    """Создать тестовое приложение"""
    app = create_app()
    app.config.from_object(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Тестовый клиент"""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Создать тестового администратора"""
    with app.app_context():
        admin = User(
            email='admin@test.com',
            full_name='Test Admin',
            role='admin',
            is_active=True
        )
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def teacher_user(app):
    """Создать тестового преподавателя"""
    with app.app_context():
        teacher = User(
            email='teacher@test.com',
            full_name='Test Teacher',
            role='teacher',
            is_active=True
        )
        teacher.set_password('password123')
        db.session.add(teacher)
        db.session.commit()
        return teacher


@pytest.fixture
def auth_headers_admin(client, admin_user):
    """Получить headers с авторизацией администратора"""
    response = client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    return {'Content-Type': 'application/json'}


@pytest.fixture
def auth_headers_teacher(client, teacher_user):
    """Получить headers с авторизацией преподавателя"""
    response = client.post('/auth/login', json={
        'email': 'teacher@test.com',
        'password': 'password123'
    })
    return {'Content-Type': 'application/json'}