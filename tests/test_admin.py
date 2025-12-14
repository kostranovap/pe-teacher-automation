from app.models import Faculty, Specialty, EducationForm


def test_create_faculty(client, admin_user, auth_headers_admin):
    """Тест создания факультета"""
    # Войти
    client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    response = client.post('/admin/faculties', json={
        'code': 'ФИТ',
        'name': 'Факультет информационных технологий'
    }, headers=auth_headers_admin)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['faculty']['code'] == 'ФИТ'
    assert data['faculty']['name'] == 'Факультет информационных технологий'


def test_get_faculties(client, app, admin_user, auth_headers_admin):
    """Тест получения списка факультетов"""
    # Создать факультет
    with app.app_context():
        from app import db
        faculty = Faculty(code='ФИТ', name='Факультет информационных технологий')
        db.session.add(faculty)
        db.session.commit()
    
    # Войти
    client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    response = client.get('/admin/faculties', headers=auth_headers_admin)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'faculties' in data
    assert len(data['faculties']) > 0


def test_create_user(client, admin_user, auth_headers_admin):
    """Тест создания пользователя"""
    # Войти
    client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    response = client.post('/admin/users', json={
        'email': 'newteacher@test.com',
        'password': 'password123',
        'full_name': 'New Teacher',
        'role': 'teacher'
    }, headers=auth_headers_admin)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['user']['email'] == 'newteacher@test.com'
    assert data['user']['role'] == 'teacher'


def test_create_duplicate_user(client, admin_user, auth_headers_admin):
    """Тест создания дубликата пользователя"""
    # Войти
    client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    # Попытаться создать пользователя с существующим email
    response = client.post('/admin/users', json={
        'email': 'admin@test.com',
        'password': 'password123',
        'full_name': 'Another Admin',
        'role': 'admin'
    }, headers=auth_headers_admin)
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data