import os
from app import create_app, db
from app.models import (User, Faculty, Specialty, EducationForm, Group, 
                       Student, Module, Theme, Standard, StandardScale,
                       Attendance, StandardResult, Assignment, Statement)


# Создать приложение
app = create_app(os.getenv('FLASK_ENV') or 'development')


@app.shell_context_processor
def make_shell_context():
    """
    Добавить объекты в shell контекст Flask
    Использование: flask shell
    """
    return {
        'db': db,
        'User': User,
        'Faculty': Faculty,
        'Specialty': Specialty,
        'EducationForm': EducationForm,
        'Group': Group,
        'Student': Student,
        'Module': Module,
        'Theme': Theme,
        'Standard': Standard,
        'StandardScale': StandardScale,
        'Attendance': Attendance,
        'StandardResult': StandardResult,
        'Assignment': Assignment,
        'Statement': Statement
    }


@app.cli.command()
def init_db():
    """Инициализация базы данных"""
    db.create_all()
    print('База данных инициализирована')


@app.cli.command()
def drop_db():
    """Удалить все таблицы (ОПАСНО!)"""
    if input('Вы уверены? Это удалит все данные! (yes/no): ').lower() == 'yes':
        db.drop_all()
        print('Все таблицы удалены')
    else:
        print('Отменено')


@app.cli.command()
def seed():
    """Заполнить БД тестовыми данными"""
    try:
        from seed_data import seed_all_data
        seed_all_data()
        print('База данных заполнена тестовыми данными')
    except Exception as e:
        print(f'Ошибка при заполнении: {e}')


@app.cli.command()
def reset_db():
    """Пересоздать БД с тестовыми данными"""
    if input('Вы уверены? Это удалит все данные! (yes/no): ').lower() == 'yes':
        db.drop_all()
        db.create_all()
        
        try:
            from seed_data import seed_all_data
            seed_all_data()
            print('✅ База данных пересоздана и заполнена')
        except Exception as e:
            print(f'Ошибка при заполнении: {e}')
    else:
        print('Отменено')


@app.cli.command()
def create_admin():
    """Создать администратора"""
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
    
    print(f'Администратор "{full_name}" успешно создан')


@app.cli.command()
def check_deadlines():
    """Проверить и обновить просроченные задания"""
    from app.utils import check_assignment_deadlines
    count = check_assignment_deadlines()
    print(f'Обновлено просроченных заданий: {count}')


@app.cli.command()
def routes():
    """Показать все маршруты приложения"""
    import urllib.parse
    
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {rule}")
        output.append(line)
    
    print('\n📍 Доступные маршруты:\n')
    for line in sorted(output):
        print(line)


if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )