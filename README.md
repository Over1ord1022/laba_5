# Contact_Book_Docker

Приложение для хранение оценок студентов.

## Функциональность

- Добавление оценок по БД и по XML
- Возможность поиска
- Docker контейнеризация
- PostgreSQL база данных

## Установка и запуск

1. Клонируйте репозиторий

2. Создайте файл .env, взяв информацию из .env.example:

POSTGRES_DB=stud_db<br>
POSTGRES_USER=stud_us<br>
POSTGRES_PASSWORD=stud_pass<br>
POSTGRES_HOST=postgres<br>
POSTGRES_PORT=5432<br>
SECRET_KEY="Ключ"<br>
DEBUG=True<br>

3. Запустите приложение:
```bash
docker-compose up --build
```
4. Выполните миграции (в новом терминале):

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```
5. Откройте в браузере: http://localhost:8000
