from app import create_app, db
from app.models import (User, Faculty, Specialty, EducationForm, Group, Student,
                        Module, Theme, Standard, StandardScale, Attendance,
                        StandardResult, Assignment, Statement)
from datetime import date, datetime, timedelta
from random import randint, choice

app = create_app()


def seed_all():
    """Заполнить БД тестовыми данными"""
    with app.app_context():
        print("Начало заполнения тестовыми данными...")

        print("Создание пользователей...")
        
        admin = User(email='admin@muiv.ru', full_name='Администратор Системы', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        teacher1 = User(email='teacher1@muiv.ru', full_name='Иванов Иван Иванович', role='teacher')
        teacher1.set_password('teacher123')
        db.session.add(teacher1)
        
        teacher2 = User(email='teacher2@muiv.ru', full_name='Петрова Мария Сергеевна', role='teacher')
        teacher2.set_password('teacher123')
        db.session.add(teacher2)
        
        dept_head = User(email='head@muiv.ru', full_name='Сидоров Петр Александрович', role='department_head')
        dept_head.set_password('head123')
        db.session.add(dept_head)
        
        db.session.commit()
        print(f"Создано пользователей: 4")
        
        print("Создание факультетов...")
        
        faculty_it = Faculty(code='ФИТ', name='Факультет информационных технологий')
        faculty_econ = Faculty(code='ФЭ', name='Факультет экономики')
        
        db.session.add_all([faculty_it, faculty_econ])
        db.session.commit()
        print(f"Создано факультетов: 2")
        
        print("Создание специальностей...")
        
        spec1 = Specialty(
            code='09.03.03',
            name='Прикладная информатика',
            faculty_id=faculty_it.id
        )
        spec2 = Specialty(
            code='38.03.05',
            name='Бизнес-информатика',
            faculty_id=faculty_it.id
        )
        spec3 = Specialty(
            code='38.03.01',
            name='Экономика',
            faculty_id=faculty_econ.id
        )
        
        db.session.add_all([spec1, spec2, spec3])
        db.session.commit()
        print(f"Создано специальностей: 3")
        
        print("📋 Создание форм обучения...")
        
        form_full = EducationForm(name='Очная', duration_years=4)
        form_part = EducationForm(name='Очно-заочная', duration_years=4.5)
        form_ext = EducationForm(name='Заочная', duration_years=5)
        
        db.session.add_all([form_full, form_part, form_ext])
        db.session.commit()
        print(f"Создано форм обучения: 3")
        
        print("Создание групп...")
        
        group1 = Group(
            name='о.ИЗДт 30.3/Б3-21',
            course=3,
            semester=5,
            specialty_id=spec2.id,
            education_form_id=form_part.id,
            teacher_id=teacher1.id
        )
        
        group2 = Group(
            name='ПИ-201',
            course=2,
            semester=3,
            specialty_id=spec1.id,
            education_form_id=form_full.id,
            teacher_id=teacher1.id
        )
        
        group3 = Group(
            name='ЭК-401',
            course=4,
            semester=7,
            specialty_id=spec3.id,
            education_form_id=form_part.id,
            teacher_id=teacher2.id
        )
        
        db.session.add_all([group1, group2, group3])
        db.session.commit()
        print(f"Создано групп: 3")
        
        print("Создание студентов...")
        
        students_data = [

            ('Петров Петр Петрович', 'ГБ123001', 'M', date(2002, 3, 15), 'основная', group1.id),
            ('Иванова Анна Сергеевна', 'ГБ123002', 'F', date(2002, 5, 20), 'основная', group1.id),
            ('Сидоров Алексей Иванович', 'ГБ123003', 'M', date(2002, 8, 10), 'подготовительная', group1.id),
            ('Козлова Мария Александровна', 'ГБ123004', 'F', date(2002, 11, 3), 'основная', group1.id),
            ('Смирнов Дмитрий Павлович', 'ГБ123005', 'M', date(2002, 2, 28), 'основная', group1.id),
            ('Новикова Елена Викторовна', 'ГБ123006', 'F', date(2002, 7, 17), 'основная', group1.id),
            ('Волков Игорь Николаевич', 'ГБ123007', 'M', date(2002, 4, 9), 'основная', group1.id),
            ('Морозова Ольга Дмитриевна', 'ГБ123008', 'F', date(2002, 10, 22), 'СМГ', group1.id),
            ('Лебедев Андрей Сергеевич', 'ГБ123009', 'M', date(2002, 6, 14), 'основная', group1.id),
            ('Соколова Татьяна Игоревна', 'ГБ123010', 'F', date(2002, 9, 5), 'основная', group1.id),
            

            ('Васильев Максим Олегович', 'ГБ122001', 'M', date(2003, 1, 12), 'основная', group2.id),
            ('Павлова Светлана Петровна', 'ГБ122002', 'F', date(2003, 4, 8), 'основная', group2.id),
            ('Федоров Никита Андреевич', 'ГБ122003', 'M', date(2003, 7, 19), 'основная', group2.id),
            ('Михайлова Наталья Владимировна', 'ГБ122004', 'F', date(2003, 10, 25), 'подготовительная', group2.id),
            ('Александров Роман Юрьевич', 'ГБ122005', 'M', date(2003, 3, 30), 'основная', group2.id),
            

            ('Кузнецов Сергей Михайлович', 'ГБ124001', 'M', date(2001, 2, 7), 'основная', group3.id),
            ('Романова Виктория Алексеевна', 'ГБ124002', 'F', date(2001, 6, 16), 'основная', group3.id),
            ('Егоров Владимир Константинович', 'ГБ124003', 'M', date(2001, 9, 23), 'основная', group3.id),
            ('Захарова Ирина Геннадьевна', 'ГБ124004', 'F', date(2001, 12, 11), 'освобождение', group3.id),
            ('Борисов Евгений Валерьевич', 'ГБ124005', 'M', date(2001, 5, 4), 'основная', group3.id),
        ]
        
        students = []
        for full_name, student_number, gender, birth_date, medical_group, group_id in students_data:
            student = Student(
                full_name=full_name,
                student_number=student_number,
                gender=gender,
                birth_date=birth_date,
                medical_group=medical_group,
                group_id=group_id
            )
            db.session.add(student)
            students.append(student)
        
        db.session.commit()
        print(f"Создано студентов: {len(students_data)}")
        
        print("Создание модулей...")
        
        module1 = Module(
            number=1,
            name='Спортивно-оздоровительная деятельность',
            max_points=35
        )
        module2 = Module(
            number=2,
            name='Практико-ориентированная подготовка',
            max_points=35
        )
        
        db.session.add_all([module1, module2])
        db.session.commit()
        print(f"Создано модулей: 2")
        
        print("Создание тем...")
        
        theme1 = Theme(name='Легкая атлетика', module_id=module1.id, max_points=20)
        theme2 = Theme(name='Атлетическая гимнастика', module_id=module1.id, max_points=15)
        theme3 = Theme(name='Степ-гимнастика', module_id=module2.id, max_points=15)
        theme4 = Theme(name='ОФП', module_id=module2.id, max_points=20)
        
        db.session.add_all([theme1, theme2, theme3, theme4])
        db.session.commit()
        print(f"Создано тем: 4")
        
        print("Создание нормативов из РПД...")
        
        # ========== ЛЕГКАЯ АТЛЕТИКА (theme1) ==========
        
        # 1. Бег 100м (для всех)
        standard1 = Standard(
            name='Бег 100м',
            theme_id=theme1.id,
            unit='секунды',
            comparison_type='less_better',
            gender=None  # Универсальный
        )
        
        # 2. Бег 1000м (мужчины)
        standard2 = Standard(
            name='Бег 1000м (мужчины)',
            theme_id=theme1.id,
            unit='секунды',
            comparison_type='less_better',
            gender='M'
        )
        
        # 3. Бег 500м (женщины)
        standard3 = Standard(
            name='Бег 500м (женщины)',
            theme_id=theme1.id,
            unit='секунды',
            comparison_type='less_better',
            gender='F'
        )
        
        # 4. Кросс 3000м (мужчины)
        standard4 = Standard(
            name='Кросс 3000м (мужчины)',
            theme_id=theme1.id,
            unit='минуты',
            comparison_type='less_better',
            gender='M'
        )
        
        # 5. Кросс 2000м (женщины)
        standard5 = Standard(
            name='Кросс 2000м (женщины)',
            theme_id=theme1.id,
            unit='минуты',
            comparison_type='less_better',
            gender='F'
        )
        
        # 6. Прыжок в длину с места (универсальный)
        standard6 = Standard(
            name='Прыжок в длину с места',
            theme_id=theme1.id,
            unit='см',
            comparison_type='more_better',
            gender=None
        )
        
        # ========== АТЛЕТИЧЕСКАЯ ГИМНАСТИКА (theme2) ==========
        
        # 7. Челночный бег 3х10м (универсальный)
        standard7 = Standard(
            name='Челночный бег 3х10м',
            theme_id=theme2.id,
            unit='секунды',
            comparison_type='less_better',
            gender=None
        )
        
        # 8. Подтягивание (универсальное - разные нормативы для М и Ж)
        standard8 = Standard(
            name='Подтягивание на перекладине',
            theme_id=theme2.id,
            unit='раз',
            comparison_type='more_better',
            gender=None
        )
        
        # 9. Отжимание (универсальное)
        standard9 = Standard(
            name='Отжимание от пола',
            theme_id=theme2.id,
            unit='раз',
            comparison_type='more_better',
            gender=None
        )
        
        # ========== ОФП (theme4) ==========
        
        # 10. Подъем ног за голову (универсальное)
        standard10 = Standard(
            name='Подъем ног за голову',
            theme_id=theme4.id,
            unit='раз',
            comparison_type='more_better',
            gender=None
        )
        
        # 11. Подъем корпуса (универсальное)
        standard11 = Standard(
            name='Подъем корпуса из положения лежа',
            theme_id=theme4.id,
            unit='раз',
            comparison_type='more_better',
            gender=None
        )
        
        # 12. Приседание 30с (универсальное)
        standard12 = Standard(
            name='Приседание за 30 секунд',
            theme_id=theme4.id,
            unit='раз',
            comparison_type='more_better',
            gender=None
        )
        
        # ========== СТЕП-ГИМНАСТИКА (theme3) ==========
        
        # 13. Прыжки со скакалкой (универсальное)
        standard13 = Standard(
            name='Прыжки со скакалкой',
            theme_id=theme3.id,
            unit='раз/мин',
            comparison_type='more_better',
            gender=None
        )
        
        # 14. Подскоки на степе (универсальное)
        standard14 = Standard(
            name='Подскоки на степ-платформе',
            theme_id=theme3.id,
            unit='раз/мин',
            comparison_type='more_better',
            gender=None
        )
        
        standards = [
            standard1, standard2, standard3, standard4, standard5,
            standard6, standard7, standard8, standard9, standard10,
            standard11, standard12, standard13, standard14
        ]
        
        db.session.add_all(standards)
        db.session.commit()
        print(f"✅ Создано нормативов: {len(standards)}")
        
        # 10. Создать оценочные шкалы ИЗ РПД (стр. 16-17)
        print("📊 Создание оценочных шкал из РПД...")
        
        all_scales = []
        
        # ========== БЕГ 100М (универсальный) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard1.id, gender='M', points=5, min_value=0, max_value=14.0),
            StandardScale(standard_id=standard1.id, gender='M', points=4, min_value=14.01, max_value=14.3),
            StandardScale(standard_id=standard1.id, gender='M', points=3, min_value=14.31, max_value=14.8),
            StandardScale(standard_id=standard1.id, gender='M', points=2, min_value=14.81, max_value=15.5),
            StandardScale(standard_id=standard1.id, gender='M', points=1, min_value=15.51, max_value=999),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard1.id, gender='F', points=5, min_value=0, max_value=16.0),
            StandardScale(standard_id=standard1.id, gender='F', points=4, min_value=16.01, max_value=16.5),
            StandardScale(standard_id=standard1.id, gender='F', points=3, min_value=16.51, max_value=17.3),
            StandardScale(standard_id=standard1.id, gender='F', points=2, min_value=17.31, max_value=18.0),
            StandardScale(standard_id=standard1.id, gender='F', points=1, min_value=18.01, max_value=999),
        ])
        
        # ========== БЕГ 1000М (МУЖЧИНЫ) - в СЕКУНДАХ ==========
        # Конвертируем минуты в секунды: 3:20 = 200 секунд
        all_scales.extend([
            StandardScale(standard_id=standard2.id, gender='M', points=5, min_value=0, max_value=200),     # 3:20
            StandardScale(standard_id=standard2.id, gender='M', points=4, min_value=201, max_value=202),   # 3:22
            StandardScale(standard_id=standard2.id, gender='M', points=3, min_value=203, max_value=212),   # 3:32
            StandardScale(standard_id=standard2.id, gender='M', points=2, min_value=213, max_value=225),   # 3:45
            StandardScale(standard_id=standard2.id, gender='M', points=1, min_value=226, max_value=9999),  # 4:10+
        ])
        
        # ========== БЕГ 500М (ЖЕНЩИНЫ) - в СЕКУНДАХ ==========
        # 155 секунд = 2:35
        all_scales.extend([
            StandardScale(standard_id=standard3.id, gender='F', points=5, min_value=0, max_value=155),     # 2:35
            StandardScale(standard_id=standard3.id, gender='F', points=4, min_value=156, max_value=205),   # 3:25
            StandardScale(standard_id=standard3.id, gender='F', points=3, min_value=206, max_value=215),   # 3:35
            StandardScale(standard_id=standard3.id, gender='F', points=2, min_value=216, max_value=220),   # 3:40
            StandardScale(standard_id=standard3.id, gender='F', points=1, min_value=221, max_value=9999),  # 3:50+
        ])
        
        # ========== КРОСС 3000М (МУЖЧИНЫ) - в МИНУТАХ ==========
        # В минутах: 11:30 = 11.5
        all_scales.extend([
            StandardScale(standard_id=standard4.id, gender='M', points=5, min_value=0, max_value=11.5),    # 11:30
            StandardScale(standard_id=standard4.id, gender='M', points=4, min_value=11.51, max_value=12.5),# 12:30
            StandardScale(standard_id=standard4.id, gender='M', points=3, min_value=12.51, max_value=13.5),# 13:30
            StandardScale(standard_id=standard4.id, gender='M', points=2, min_value=13.51, max_value=14.5),# 14:30
            StandardScale(standard_id=standard4.id, gender='M', points=1, min_value=14.51, max_value=999), # 15:30+
        ])
        
        # ========== КРОСС 2000М (ЖЕНЩИНЫ) - в МИНУТАХ ==========
        all_scales.extend([
            StandardScale(standard_id=standard5.id, gender='F', points=5, min_value=0, max_value=9.5),     # 9:30
            StandardScale(standard_id=standard5.id, gender='F', points=4, min_value=9.51, max_value=10.0), # 10:00
            StandardScale(standard_id=standard5.id, gender='F', points=3, min_value=10.01, max_value=11.0),# 11:00
            StandardScale(standard_id=standard5.id, gender='F', points=2, min_value=11.01, max_value=12.0),# 12:00
            StandardScale(standard_id=standard5.id, gender='F', points=1, min_value=12.01, max_value=999), # 13:30+
        ])
        
        # ========== ЧЕЛНОЧНЫЙ БЕГ 3х10М (универсальный) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard7.id, gender='M', points=5, min_value=0, max_value=7.1),
            StandardScale(standard_id=standard7.id, gender='M', points=4, min_value=7.11, max_value=7.4),
            StandardScale(standard_id=standard7.id, gender='M', points=3, min_value=7.41, max_value=8.0),
            StandardScale(standard_id=standard7.id, gender='M', points=2, min_value=8.01, max_value=8.5),
            StandardScale(standard_id=standard7.id, gender='M', points=1, min_value=8.51, max_value=999),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard7.id, gender='F', points=5, min_value=0, max_value=8.0),
            StandardScale(standard_id=standard7.id, gender='F', points=4, min_value=8.01, max_value=8.3),
            StandardScale(standard_id=standard7.id, gender='F', points=3, min_value=8.31, max_value=9.3),
            StandardScale(standard_id=standard7.id, gender='F', points=2, min_value=9.31, max_value=10.0),
            StandardScale(standard_id=standard7.id, gender='F', points=1, min_value=10.01, max_value=999),
        ])
        
        # ========== ПРЫЖОК В ДЛИНУ С МЕСТА (универсальный) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard6.id, gender='M', points=5, min_value=250, max_value=9999),
            StandardScale(standard_id=standard6.id, gender='M', points=4, min_value=230, max_value=249),
            StandardScale(standard_id=standard6.id, gender='M', points=3, min_value=210, max_value=229),
            StandardScale(standard_id=standard6.id, gender='M', points=2, min_value=180, max_value=209),
            StandardScale(standard_id=standard6.id, gender='M', points=1, min_value=0, max_value=179),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard6.id, gender='F', points=5, min_value=230, max_value=9999),
            StandardScale(standard_id=standard6.id, gender='F', points=4, min_value=210, max_value=229),
            StandardScale(standard_id=standard6.id, gender='F', points=3, min_value=180, max_value=209),
            StandardScale(standard_id=standard6.id, gender='F', points=2, min_value=160, max_value=179),
            StandardScale(standard_id=standard6.id, gender='F', points=1, min_value=0, max_value=159),
        ])
        
        # ========== ПОДТЯГИВАНИЕ (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard8.id, gender='M', points=5, min_value=15, max_value=9999),
            StandardScale(standard_id=standard8.id, gender='M', points=4, min_value=13, max_value=14),
            StandardScale(standard_id=standard8.id, gender='M', points=3, min_value=11, max_value=12),
            StandardScale(standard_id=standard8.id, gender='M', points=2, min_value=7, max_value=10),
            StandardScale(standard_id=standard8.id, gender='M', points=1, min_value=0, max_value=6),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard8.id, gender='F', points=5, min_value=22, max_value=9999),
            StandardScale(standard_id=standard8.id, gender='F', points=4, min_value=19, max_value=21),
            StandardScale(standard_id=standard8.id, gender='F', points=3, min_value=10, max_value=18),
            StandardScale(standard_id=standard8.id, gender='F', points=2, min_value=7, max_value=9),
            StandardScale(standard_id=standard8.id, gender='F', points=1, min_value=0, max_value=6),
        ])
        
        # ========== ОТЖИМАНИЕ (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard9.id, gender='M', points=5, min_value=50, max_value=9999),
            StandardScale(standard_id=standard9.id, gender='M', points=4, min_value=45, max_value=49),
            StandardScale(standard_id=standard9.id, gender='M', points=3, min_value=40, max_value=44),
            StandardScale(standard_id=standard9.id, gender='M', points=2, min_value=35, max_value=39),
            StandardScale(standard_id=standard9.id, gender='M', points=1, min_value=0, max_value=34),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard9.id, gender='F', points=5, min_value=29, max_value=9999),
            StandardScale(standard_id=standard9.id, gender='F', points=4, min_value=27, max_value=28),
            StandardScale(standard_id=standard9.id, gender='F', points=3, min_value=22, max_value=26),
            StandardScale(standard_id=standard9.id, gender='F', points=2, min_value=18, max_value=21),
            StandardScale(standard_id=standard9.id, gender='F', points=1, min_value=0, max_value=17),
        ])
        
        # ========== ПОДЪЕМ НОГ ЗА ГОЛОВУ (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard10.id, gender='M', points=5, min_value=45, max_value=9999),
            StandardScale(standard_id=standard10.id, gender='M', points=4, min_value=40, max_value=44),
            StandardScale(standard_id=standard10.id, gender='M', points=3, min_value=35, max_value=39),
            StandardScale(standard_id=standard10.id, gender='M', points=2, min_value=30, max_value=34),
            StandardScale(standard_id=standard10.id, gender='M', points=1, min_value=0, max_value=29),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard10.id, gender='F', points=5, min_value=14, max_value=9999),
            StandardScale(standard_id=standard10.id, gender='F', points=4, min_value=12, max_value=13),
            StandardScale(standard_id=standard10.id, gender='F', points=3, min_value=10, max_value=11),
            StandardScale(standard_id=standard10.id, gender='F', points=2, min_value=8, max_value=9),
            StandardScale(standard_id=standard10.id, gender='F', points=1, min_value=0, max_value=7),
        ])
        
        # ========== ПОДЪЕМ КОРПУСА (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard11.id, gender='M', points=5, min_value=50, max_value=9999),
            StandardScale(standard_id=standard11.id, gender='M', points=4, min_value=40, max_value=49),
            StandardScale(standard_id=standard11.id, gender='M', points=3, min_value=35, max_value=39),
            StandardScale(standard_id=standard11.id, gender='M', points=2, min_value=25, max_value=34),
            StandardScale(standard_id=standard11.id, gender='M', points=1, min_value=0, max_value=24),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard11.id, gender='F', points=5, min_value=40, max_value=9999),
            StandardScale(standard_id=standard11.id, gender='F', points=4, min_value=35, max_value=39),
            StandardScale(standard_id=standard11.id, gender='F', points=3, min_value=30, max_value=34),
            StandardScale(standard_id=standard11.id, gender='F', points=2, min_value=25, max_value=29),
            StandardScale(standard_id=standard11.id, gender='F', points=1, min_value=0, max_value=24),
        ])
        
        # ========== ПРИСЕДАНИЕ 30С (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard12.id, gender='M', points=5, min_value=160, max_value=9999),
            StandardScale(standard_id=standard12.id, gender='M', points=4, min_value=150, max_value=159),
            StandardScale(standard_id=standard12.id, gender='M', points=3, min_value=140, max_value=149),
            StandardScale(standard_id=standard12.id, gender='M', points=2, min_value=130, max_value=139),
            StandardScale(standard_id=standard12.id, gender='M', points=1, min_value=0, max_value=129),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard12.id, gender='F', points=5, min_value=170, max_value=9999),
            StandardScale(standard_id=standard12.id, gender='F', points=4, min_value=160, max_value=169),
            StandardScale(standard_id=standard12.id, gender='F', points=3, min_value=150, max_value=159),
            StandardScale(standard_id=standard12.id, gender='F', points=2, min_value=140, max_value=149),
            StandardScale(standard_id=standard12.id, gender='F', points=1, min_value=0, max_value=139),
        ])
        
        # ========== ПРЫЖКИ СО СКАКАЛКОЙ (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard13.id, gender='M', points=5, min_value=35, max_value=9999),
            StandardScale(standard_id=standard13.id, gender='M', points=4, min_value=30, max_value=34),
            StandardScale(standard_id=standard13.id, gender='M', points=3, min_value=25, max_value=29),
            StandardScale(standard_id=standard13.id, gender='M', points=2, min_value=20, max_value=24),
            StandardScale(standard_id=standard13.id, gender='M', points=1, min_value=0, max_value=19),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard13.id, gender='F', points=5, min_value=25, max_value=9999),
            StandardScale(standard_id=standard13.id, gender='F', points=4, min_value=20, max_value=24),
            StandardScale(standard_id=standard13.id, gender='F', points=3, min_value=15, max_value=19),
            StandardScale(standard_id=standard13.id, gender='F', points=2, min_value=10, max_value=14),
            StandardScale(standard_id=standard13.id, gender='F', points=1, min_value=0, max_value=9),
        ])
        
        # ========== ПОДСКОКИ НА СТЕПЕ (универсальное) ==========
        # Мужчины
        all_scales.extend([
            StandardScale(standard_id=standard14.id, gender='M', points=5, min_value=60, max_value=9999),
            StandardScale(standard_id=standard14.id, gender='M', points=4, min_value=55, max_value=59),
            StandardScale(standard_id=standard14.id, gender='M', points=3, min_value=45, max_value=54),
            StandardScale(standard_id=standard14.id, gender='M', points=2, min_value=30, max_value=44),
            StandardScale(standard_id=standard14.id, gender='M', points=1, min_value=0, max_value=29),
        ])
        # Женщины
        all_scales.extend([
            StandardScale(standard_id=standard14.id, gender='F', points=5, min_value=57, max_value=9999),
            StandardScale(standard_id=standard14.id, gender='F', points=4, min_value=43, max_value=56),
            StandardScale(standard_id=standard14.id, gender='F', points=3, min_value=37, max_value=42),
            StandardScale(standard_id=standard14.id, gender='F', points=2, min_value=30, max_value=36),
            StandardScale(standard_id=standard14.id, gender='F', points=1, min_value=0, max_value=29),
        ])
        
        db.session.add_all(all_scales)
        db.session.commit()
        print(f"Создано оценочных шкал: {len(all_scales)}")
        
        # 11. Создать записи посещаемости
        print("Создание посещаемости...")
        
        attendance_records = []
        today = date.today()
        
        # Генерируем посещаемость за последние 12 занятий для группы ПИ-201
        for student in students[10:15]:  # Группа ПИ-201 (5 студентов)
            for i in range(12):
                class_date = today - timedelta(days=(i * 3))
                
                # 80% вероятность присутствия
                if randint(1, 100) <= 80:
                    status = 'присутствовал'
                elif randint(1, 100) <= 10:
                    status = 'уважительная'
                else:
                    status = 'отсутствовал'
                
                attendance = Attendance(
                    student_id=student.id,
                    date=class_date,
                    status=status,
                    created_by=teacher1.id
                )
                attendance_records.append(attendance)
        
        db.session.add_all(attendance_records)
        db.session.commit()
        print(f"Создано записей посещаемости: {len(attendance_records)}")
        
        # 12. Создать результаты нормативов
        print("Создание результатов нормативов...")
        
        results = []
        
        # Группа ПИ-201 - результаты по основным нормативам
        for student in students[10:15]:  # 5 студентов
            gender = student.gender
            
            # Бег 100м
            if gender == 'M':
                result_value = round(14.0 + (randint(0, 20) / 10), 1)  # 14.0-16.0
            else:
                result_value = round(16.0 + (randint(0, 30) / 10), 1)  # 16.0-19.0
            
            result = StandardResult(
                student_id=student.id,
                standard_id=standard1.id,
                result_value=result_value,
                points=randint(3, 5),
                date=today - timedelta(days=20),
                attempt_number=1,
                created_by=teacher1.id
            )
            results.append(result)
            
            # Подтягивание
            if gender == 'M':
                result_value = randint(10, 16)
            else:
                result_value = randint(15, 25)
            
            result = StandardResult(
                student_id=student.id,
                standard_id=standard8.id,
                result_value=result_value,
                points=randint(3, 5),
                date=today - timedelta(days=15),
                attempt_number=1,
                created_by=teacher1.id
            )
            results.append(result)
            
            # Отжимания
            if gender == 'M':
                result_value = randint(35, 55)
            else:
                result_value = randint(20, 32)
            
            result = StandardResult(
                student_id=student.id,
                standard_id=standard9.id,
                result_value=result_value,
                points=randint(3, 5),
                date=today - timedelta(days=10),
                attempt_number=1,
                created_by=teacher1.id
            )
            results.append(result)
            
            # Прыжок в длину
            if gender == 'M':
                result_value = randint(200, 260)
            else:
                result_value = randint(170, 240)
            
            result = StandardResult(
                student_id=student.id,
                standard_id=standard6.id,
                result_value=result_value,
                points=randint(3, 5),
                date=today - timedelta(days=5),
                attempt_number=1,
                created_by=teacher1.id
            )
            results.append(result)
        
        db.session.add_all(results)
        db.session.commit()
        print(f"Создано результатов нормативов: {len(results)}")
        
        # 13. Создать индивидуальные задания
        print("Создание индивидуальных заданий...")
        
        assignments = []
        
        assignment1 = Assignment(
            student_id=students[2].id,  # Сидоров (подготовительная группа)
            type='реферат',
            title='Влияние физических нагрузок на здоровье',
            description='Написать реферат объемом 10-15 страниц о влиянии регулярных физических нагрузок на состояние здоровья человека.',
            deadline=today + timedelta(days=14),
            status='назначено',
            bonus_points=5,
            created_by=teacher1.id
        )
        
        assignment2 = Assignment(
            student_id=students[7].id,  # Морозова (СМГ)
            type='доп_занятия',
            title='Дополнительные занятия ЛФК',
            description='Посещение дополнительных занятий лечебной физкультурой 2 раза в неделю.',
            deadline=today + timedelta(days=30),
            status='назначено',
            bonus_points=10,
            created_by=teacher1.id
        )
        
        assignment3 = Assignment(
            student_id=students[0].id,  # Петров
            type='пересдача',
            title='Пересдача норматива "Бег 100м"',
            description='Пересдача норматива для улучшения результата.',
            deadline=today + timedelta(days=7),
            status='выполнено',
            bonus_points=3,
            created_by=teacher1.id,
            completion_date=datetime.now() - timedelta(days=2)
        )
        
        assignments = [assignment1, assignment2, assignment3]
        db.session.add_all(assignments)
        db.session.commit()
        print(f"✅ Создано индивидуальных заданий: {len(assignments)}")
        
        # 14. Создать ведомости
        print("Создание ведомостей...")
        
        statement1 = Statement(
            number=f'ФК-{today.year}-001',
            group_id=group2.id,  # ПИ-201
            semester=3,
            type='зачет',
            date=today - timedelta(days=30),
            teacher_id=teacher1.id,
            dean_name='Смирнов Валерий Петрович',
            file_path='/uploads/statements/statement_001.xlsx'
        )
        
        statement2 = Statement(
            number=f'ФК-{today.year}-002',
            group_id=group3.id,  # ЭК-401
            semester=7,
            type='зачет',
            date=today - timedelta(days=20),
            teacher_id=teacher2.id,
            dean_name='Кузнецова Анна Ивановна'
        )
        
        statements = [statement1, statement2]
        db.session.add_all(statements)
        db.session.commit()
        print(f"Создано ведомостей: {len(statements)}")
        
        print("\nЗаполнение завершено!")
        print("\n" + "=" * 70)
        print("СТАТИСТИКА СОЗДАННЫХ ДАННЫХ:")
        print("=" * 70)
        print(f"Пользователей: 4")
        print(f"Факультетов: 2")
        print(f"Специальностей: 3")
        print(f"Форм обучения: 3")
        print(f"Групп: 3")
        print(f"Студентов: {len(students)}")
        print(f"Модулей: 2")
        print(f"Тем: 4")
        print(f"Нормативов: {len(standards)} (ВСЕ из РПД)")
        print(f"Оценочных шкал: {len(all_scales)} (Все баллы 5-4-3-2-1)")
        print(f"Записей посещаемости: {len(attendance_records)}")
        print(f"Результатов нормативов: {len(results)}")
        print(f"Индивидуальных заданий: {len(assignments)}")
        print(f"Ведомостей: {len(statements)}")
        print("=" * 70)
        
        print("\nТЕСТОВЫЕ УЧЕТНЫЕ ДАННЫЕ:")
        print("=" * 70)
        print("Администратор:")
        print("   Email: admin@muiv.ru")
        print("   Пароль: admin123")
        print()
        print("Преподаватель 1 (группы: о.ИЗДт 30.3/Б3-21, ПИ-201):")
        print("   Email: teacher1@muiv.ru")
        print("   Пароль: teacher123")
        print()
        print("Преподаватель 2 (группа: ЭК-401):")
        print("   Email: teacher2@muiv.ru")
        print("   Пароль: teacher123")
        print()
        print("Заведующий кафедрой:")
        print("   Email: head@muiv.ru")
        print("   Пароль: head123")
        print("=" * 70)
        
        print("\nПРИМЕРЫ СТУДЕНТОВ ДЛЯ ПОИСКА:")
        print("=" * 70)
        for i in range(min(5, len(students))):
            print(f"• {students[i].full_name} - {students[i].student_number} (пол: {students[i].gender})")
        print("=" * 70)
        
        print("\n📋 НОРМАТИВЫ ИЗ РПД (таблица стр. 16-17):")
        print("=" * 70)
        print("Легкая атлетика (6 нормативов):")
        print("   1. Бег 100м (универсальный)")
        print("   2. Бег 1000м (мужчины)")
        print("   3. Бег 500м (женщины)")
        print("   4. Кросс 3000м (мужчины)")
        print("   5. Кросс 2000м (женщины)")
        print("   6. Прыжок в длину с места (универсальный)")
        print()
        print("Атлетическая гимнастика (3 норматива):")
        print("   7. Челночный бег 3х10м (универсальный)")
        print("   8. Подтягивание (универсальное)")
        print("   9. Отжимание (универсальное)")
        print()
        print("ОФП (3 норматива):")
        print("   10. Подъем ног за голову (универсальное)")
        print("   11. Подъем корпуса (универсальное)")
        print("   12. Приседание 30с (универсальное)")
        print()
        print("Степ-гимнастика (2 норматива):")
        print("   13. Прыжки со скакалкой (универсальное)")
        print("   14. Подскоки на степе (универсальное)")
        print("=" * 70)
        
        print("\nФОРМАТ ДАННЫХ:")
        print("=" * 70)
        print("• Пол студентов: 'M' / 'F' (не 'male'/'female')")
        print("• Пол в шкалах: 'M' / 'F' (не 'male'/'female')")
        print("• Gender нормативов: NULL (универсальные) или 'M'/'F'")
        print("• Оценочные шкалы: есть для КАЖДОГО пола (даже для универсальных)")
        print("=" * 70)
        
        print("\nСистема готова к использованию!")
        print("Откройте: http://localhost:5000")
        print()


if __name__ == '__main__':
    seed_all()