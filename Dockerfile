# Backend (Django)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=cloud_storage.settings
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "cloud_storage.wsgi:application", "--bind", "0.0.0.0:8000"]
