from dotenv import load_dotenv
load_dotenv()
from app import db, create_app
app = create_app()
with app.app_context():
    db.drop_all()
    print("✅ Таблицы удалены")
    db.create_all()
    print("✅ Таблицы созданы")