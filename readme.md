# Physical Education System

Веб-приложение для автоматизации учебного процесса по дисциплине "Физическая культура". Реализует балльно-рейтинговую систему оценивания с контролем посещаемости, учётом результатов нормативов и формированием отчётной документации.

## Возможности

- **Управление студентами**: регистрация, группировка по специальностям, учёт медицинских групп
- **Балльно-рейтинговая система**: автоматический расчёт баллов (посещаемость 30 + модули 70)
- **Учёт нормативов**: 14 контрольных испытаний из РПД с гендерными оценочными шкалами
- **Посещаемость**: журнал занятий с отметками присутствия/отсутствия
- **Отчётность**: формирование и экспорт ведомостей в Excel
- **Роли**: администратор, преподаватель, заведующий кафедрой, студент

## Стек технологий

- **Backend**: Flask 3.0, SQLAlchemy 2.0
- **Database**: PostgreSQL 15
- **Frontend**: Bootstrap 5, Jinja2
- **Auth**: Flask-Login

## Требования

- Python 3.10+
- PostgreSQL 15+
- pip

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/yourusername/physical_education_system.git
cd physical_education_system
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить базу данных

Создайте БД в PostgreSQL:

```sql
CREATE DATABASE pe_system_db;
CREATE USER pe_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE pe_system_db TO pe_admin;
```

### 5. Настроить переменные окружения

Создайте файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql://pe_admin:your_password@localhost:5432/pe_system_db
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 6. Инициализировать БД

```bash
python
>>> from app import db, create_app
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 7. Заполнить тестовыми данными (опционально)

```bash
python seed_data.py
```

### 8. Запустить приложение

```bash
flask run
```

Приложение будет доступно по адресу: `http://localhost:5000`

## Тестовые аккаунты

После выполнения `seed_data.py`:

| Роль | Email | Пароль |
|------|-------|--------|
| Администратор | admin@muiv.ru | admin123 |
| Преподаватель | teacher1@muiv.ru | teacher123 |
| Зав. кафедрой | head@muiv.ru | head123 |

## Структура проекта

```
physical_education_system/
├── app/
│   ├── __init__.py          # Инициализация приложения
│   ├── models.py            # Модели БД (14 таблиц)
│   ├── forms.py             # WTForms формы
│   ├── utils.py             # Вспомогательные функции
│   ├── routes/              # Маршруты (blueprints)
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── teacher.py
│   │   ├── department_head.py
│   │   └── student.py
│   └── templates/           # HTML шаблоны
├── config.py                # Конфигурация
├── seed_data.py             # Заполнение тестовыми данными
├── run.py                   # Точка входа
└── requirements.txt
```

## Модель данных

Система включает 14 взаимосвязанных таблиц:

- **users** - пользователи системы
- **faculties** - факультеты
- **specialties** - специальности
- **education_forms** - формы обучения
- **groups** - учебные группы
- **students** - студенты
- **modules** - учебные модули (2 шт)
- **themes** - темы занятий (4 шт)
- **standards** - контрольные нормативы (14 шт)
- **standard_scales** - оценочные шкалы (140 шт)
- **attendances** - журнал посещаемости
- **standard_results** - результаты нормативов
- **assignments** - индивидуальные задания
- **statements** - ведомости

## Балльно-рейтинговая система

**Максимум: 100 баллов**

- Посещаемость: 0-30 баллов (≥90% = 30, ≥80% = 25, ≥70% = 20, ≥60% = 15, <60% = 10)
- Модуль 1: 0-35 баллов (Спортивно-оздоровительная деятельность)
- Модуль 2: 0-35 баллов (Практико-ориентированная подготовка)
- Бонусы: за индивидуальные задания

**Зачёт: ≥60 баллов**

**Оценки:**
- 90-100: Отлично
- 75-89: Хорошо
- 60-74: Удовлетворительно
- 0-59: Не зачтено

## Нормативы из РПД

Система включает 14 контрольных нормативов:

**Легкая атлетика:**
- Бег 100м, 500м (Ж), 1000м (М), Кросс 2000м (Ж), 3000м (М), Прыжок в длину

**Атлетическая гимнастика:**
- Челночный бег 3х10м, Подтягивание, Отжимание

**ОФП:**
- Подъем ног за голову, Подъем корпуса, Приседание 30с

**Степ-гимнастика:**
- Прыжки со скакалкой, Подскоки на степе

Каждый норматив имеет 10 оценочных шкал (5 баллов × 2 пола).

## Разработка

### Создание миграций

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Запуск в режиме отладки

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

## Deployment

### Docker (рекомендуется)

```bash
docker-compose up -d
```

### Production настройки

В production используйте:
- Gunicorn/uWSGI для WSGI
- Nginx для reverse proxy
- PostgreSQL с SSL
- Переменные окружения для секретов

## Лицензия

MIT

## Контакты

Автор: Костарнова Полина Андреевна  
Email: kostarnova.p@mail.ru  
GitHub: https://github.com/kostranovap/pe-teacher-automation