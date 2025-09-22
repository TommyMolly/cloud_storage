# ☁️ My_Cloud - Backend

Бэкенд для файлового облачного хранилища.
Реализован на Django + Django REST Framework с поддержкой JWT-аутентификации.

Позволяет пользователям загружать, хранить, скачивать, переименовывать и комментировать файлы.
Есть админ-возможности для управления пользователями и файлами.

---

## ⚙️ Технологии

- Python 3.10+

- Django — веб-фреймворк

- Django REST Framework — построение API

- SimpleJWT — JWT-аутентификация

- PostgreSQL (или SQLite для разработки)

## 🚀 Установка и запуск

#1. Клонируйте репозиторий:
```
git clone https://github.com/tommymolly/cloud_storage.git
cd cloud_storage
```

#2. Установите зависимости:
```
pip install -r requirements.txt
```

#3. Настройте переменные окружения:
Создайте файл .env в корне проекта:
```
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_NAME=cloud_db
DATABASE_USER=cloud_user
DATABASE_PASSWORD=cloud_pass
DATABASE_HOST=localhost
DATABASE_PORT=5432
```
#4. Примените миграции:
```
python manage.py migrate
```
#5. Создайте суперпользователя:
```
python manage.py createsuperuser
```
#6. Запустите сервер разработки:
```
python manage.py runserver
```

---

## 📂 Структура проекта
```
cloud_storage/
├── accounts/                # Пользователи и аутентификация
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── files/                   # Работа с файлами
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── cloud_storage/        # Настройки проекта
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── requirements.txt         # Зависимости
├── manage.py                
└── README.md                
```

---

## 🔑 API эндпоинты

### 🔐 Аутентификация

- POST /api/auth/register/ — регистрация

- POST /api/auth/login/ — вход (JWT access + refresh)

- POST /api/auth/refresh/ — обновление токена

### 📁 Файлы

- GET /api/files/ — список файлов

- POST /api/files/upload/ — загрузка файла

- GET /api/files/{id}/download/ — скачать файл

- POST /api/files/{id}/rename/ — переименовать

- POST /api/files/{id}/comment/ — изменить комментарий

- DELETE /api/files/{id}/ — удалить

- POST /api/files/shared/{id}/ — создать публичную ссылку

- GET /api/files/shared/{token}/ — скачать по публичной ссылке

---

## 🔗 Подключение фронтенда

Для работы фронтенда с бэкендом нужно настроить базовый URL API.

### 1. Настройка переменной окружения

UODO