# Fitness Tracker — Event-Driven Architecture (Вариант 14)

Домашнее задание по курсу «Архитектура программных систем» — ДЗ 06.

## Структура проекта

```
fitness-tracker-eda/
├── docker-compose.yml          # RabbitMQ + Producer + Consumer
├── event_driven_design.md      # Описание EDA и CQRS архитектуры
├── event_catalog.md            # Каталог всех событий системы
├── README.md                   # Этот файл
└── src/
    ├── producer/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── main.py             # Публикует 4 события в RabbitMQ
    └── consumer/
        ├── Dockerfile
        ├── requirements.txt
        └── main.py             # Обрабатывает события, обновляет Read-модель
```

## Быстрый старт

### Требования
- Docker + Docker Compose

### Запуск

```bash
# 1. Поднять всё окружение
docker compose up --build

# Consumer запустится автоматически и начнёт слушать очереди.
# Producer опубликует 4 события и завершится.
```

### Ожидаемый вывод

```
fitness-consumer | [Consumer] Подключение установлено.
fitness-consumer | [Consumer] Слушаем: q.statistics.user.created (user.events -> user.created)
fitness-consumer | [Consumer] Слушаем: q.statistics.workout.created ...
fitness-consumer | [Consumer] Ожидание событий...

fitness-producer | [Producer] Подключение установлено.
fitness-producer | [Producer] ✅ Опубликовано [user.created]: UserCreated
fitness-producer | [Producer] ✅ Опубликовано [workout.created]: WorkoutCreated
fitness-producer | [Producer] ✅ Опубликовано [workout.exercise.added]: ExerciseAddedToWorkout
fitness-producer | [Producer] ✅ Опубликовано [workout.completed]: WorkoutCompleted

fitness-consumer | [Consumer] 📨 Получено: UserCreated
fitness-consumer |   [Statistics] Профиль создан для Иван Петров
fitness-consumer | [Consumer] 📨 Получено: WorkoutCreated
fitness-consumer | [Consumer] 📨 Получено: ExerciseAddedToWorkout
fitness-consumer | [Consumer] 📨 Получено: WorkoutCompleted
fitness-consumer |   ─── Read Model ────────────────────────────
fitness-consumer |   Пользователь: Иван Петров (ivan@example.com)
fitness-consumer |   Тренировок: 1
fitness-consumer |   • Силовая тренировка — 55 мин, объём 3500 кг
```

### RabbitMQ Management UI

Открыть в браузере: http://localhost:15672  
Логин: `admin` / Пароль: `admin123`

## Запуск только RabbitMQ (для ручного тестирования)

```bash
docker compose up rabbitmq

# В другом терминале — запустить consumer
cd src/consumer && pip install pika && python main.py

# В третьем — запустить producer
cd src/producer && pip install pika && python main.py
```

## Описание архитектуры

Подробное описание событийно-ориентированной архитектуры, паттерна CQRS,  
выбора RabbitMQ и схемы потоков данных находится в файле:
**[event_driven_design.md](./event_driven_design.md)**

Каталог всех событий с описанием структуры payload, производителей и  
потребителей находится в файле:
**[event_catalog.md](./event_catalog.md)**

## Ключевые решения

| Решение | Обоснование |
|---|---|
| **RabbitMQ** | Простота настройки, гибкая маршрутизация через topic exchange, достаточная производительность для фитнес-трекера |
| **Topic Exchange** | Позволяет гибко добавлять новых consumer'ов без изменения producer'а |
| **at-least-once** | Надёжная доставка с ack; идемпотентность на стороне consumer |
| **CQRS** | Разделение Write (UserService, WorkoutService) и Read (StatisticsService) моделей для оптимизации запросов истории и статистики |
| **Идемпотентность** | Consumer хранит set обработанных event_id и пропускает дубликаты |
