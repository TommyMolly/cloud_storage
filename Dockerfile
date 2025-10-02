# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости для psycopg2 и Pillow
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && apt-get clean

# Копируем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . /app/

# Собираем статику Django
RUN python manage.py collectstatic --noinput

# Запускаем gunicorn (продакшн-сервер)
CMD ["gunicorn", "cloud_storage.wsgi:application", "--bind", "0.0.0.0:8000"]
