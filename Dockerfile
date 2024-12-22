# Dockerfile
FROM python:3.13

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# Открываем порт для Flask-сервера
EXPOSE 7777

# Команда для запуска
CMD ["python", "main.py"]
