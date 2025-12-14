#!/bin/bash

echo "Заполнение базы данных тестовыми данными..."

docker-compose exec web python app/seed_data.py

echo "Готово!"