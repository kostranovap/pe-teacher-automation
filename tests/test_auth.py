def test_login_success(client, admin_user):
    """Тест успешной авторизации"""
    response = client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'admin@test.com'
    assert data['user']['role'] == 'admin'


def test_login_wrong_password(client, admin_user):
    """Тест авторизации с неверным паролем"""
    response = client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_login_nonexistent_user(client):
    """Тест авторизации несуществующего пользователя"""
    response = client.post('/auth/login', json={
        'email': 'nonexistent@test.com',
        'password': 'password123'
    })
    
    assert response.status_code == 401


def test_logout(client, admin_user):
    """Тест выхода из системы"""
    # Сначала войти
    client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    # Выйти
    response = client.post('/auth/logout')
    assert response.status_code == 200


def test_get_current_user_authenticated(client, admin_user):
    """Тест получения текущего пользователя"""
    # Войти
    client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'password123'
    })
    
    # Получить текущего пользователя
    response = client.get('/auth/me')
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['email'] == 'admin@test.com'


def test_get_current_user_not_authenticated(client):
    """Тест получения пользователя без авторизации"""
    response = client.get('/auth/me')
    assert response.status_code == 401