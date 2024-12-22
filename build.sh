#!/bin/bash

# Останавливаем старый контейнер, если он запущен
docker-compose down

# Собираем и запускаем контейнеры
docker-compose up --build -d

# Выполняем миграции (инициализация базы данных)
docker exec pdd_question_base python parser.py

# Готово
echo "Сервис успешно запущен. Доступен на http://localhost:5000"