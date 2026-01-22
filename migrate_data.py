import os
import sys
import sqlite3
import django
from pathlib import Path

# Настройка Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studentstat.settings')
django.setup()

from studStat.models import StatStudent

def migrate_sqlite_to_postgres():
    """Перенос данных из SQLite в PostgreSQL"""
    
    sqlite_path = BASE_DIR / 'db.sqlite3'
    
    if not sqlite_path.exists():
        print("❌ Файл db.sqlite3 не найден!")
        print("Положите файл SQLite рядом с manage.py")
        return False
    
    print(f"📦 Найден файл SQLite: {sqlite_path}")
    
    # Подключение к SQLite
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_cursor = sqlite_conn.cursor()
    
    # Получение данных из SQLite
    sqlite_cursor.execute('''
        SELECT name, subject, grade, date, teacher, cafedra 
        FROM studstat 
        ORDER BY id
    ''')
    
    rows = sqlite_cursor.fetchall()
    total = len(rows)
    
    if total == 0:
        print("✅ Нет данных для миграции")
        sqlite_conn.close()
        return True
    
    print(f"📊 Найдено записей в SQLite: {total}")
    
    # Перенос данных в PostgreSQL
    migrated = 0
    skipped = 0
    errors = 0
    
    for i, (name, subject, grade, date, teacher, cafedra) in enumerate(rows, 1):
        try:
            # Проверка на дубликаты
            duplicate = StatStudent.objects.filter(
                name=name,
                subject=subject,
                grade=grade,
                date=date
            ).exists()
            
            if duplicate:
                print(f"   ⚠️  Запись {i}/{total}: Дубликат, пропускаем")
                skipped += 1
                continue
            
            # Создание записи в PostgreSQL
            StatStudent.objects.create(
                name=name,
                subject=subject,
                grade=grade,
                date=date,
                teacher=teacher or '',
                cafedra=cafedra or ''
            )
            
            migrated += 1
            if i % 10 == 0 or i == total:
                print(f"   ✅ Обработано {i}/{total} записей")
                
        except Exception as e:
            print(f"   ❌ Ошибка при миграции записи {i}: {str(e)}")
            errors += 1
    
    sqlite_conn.close()
    
    # Статистика
    print("\n" + "="*50)
    print("📊 ИТОГИ МИГРАЦИИ:")
    print(f"   Всего записей в SQLite: {total}")
    print(f"   Успешно мигрировано: {migrated}")
    print(f"   Пропущено (дубликаты): {skipped}")
    print(f"   Ошибок: {errors}")
    print(f"   Всего записей в PostgreSQL: {StatStudent.objects.count()}")
    
    return errors == 0

if __name__ == '__main__':
    success = migrate_sqlite_to_postgres()
    sys.exit(0 if success else 1)