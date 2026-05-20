# Fitness Tracker — Event-Driven Architecture (Вариант 14)

Домашняя работа по курсу «Архитектура программных систем» — ДЗ 06.

## Структура проекта

```

fitness-tracker-eda/
├── docker-compose.yml
├── event_driven_design.md
├── event_catalog.md
├── README.md
└── src/
├── producer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
└── consumer/
├── Dockerfile
├── requirements.txt
└── main.py

````id="struct1"

---

## Быстрый старт

### Требования
- Docker
- Docker Compose

### Запуск

```bash
docker compose up --build
````

После запуска:

* Consumer начинает слушать очереди
* Producer отправляет события и завершает работу

---

## Пример вывода

```id="logs1"
fitness-consumer | [Consumer] Подключение установлено
fitness-consumer | [Consumer] Ожидание сообщений...

fitness-producer | [Producer] Подключение установлено
fitness-producer | [Producer] Отправлено: UserCreated
fitness-producer | [Producer] Отправлено: WorkoutCreated
fitness-producer | [Producer] Отправлено: ExerciseAddedToWorkout
fitness-producer | [Producer] Отправлено: WorkoutCompleted

fitness-consumer | [Consumer] Получено: UserCreated
fitness-consumer | [Consumer] Профиль создан для Иван Петров

fitness-consumer | [Consumer] Получено: WorkoutCompleted
fitness-consumer | ─── Read Model ───────────────
fitness-consumer | Пользователь: Иван Петров
fitness-consumer | Тренировок: 1
fitness-consumer | • Силовая тренировка — 55 мин
```

---

## RabbitMQ UI

[http://localhost:15672](http://localhost:15672)

```
login: admin
password: admin123
```

---

## Запуск вручную

### RabbitMQ

```bash id="rmq1"
docker compose up rabbitmq
```

### Consumer

```bash id="cons1"
cd src/consumer
pip install pika
python main.py
```

### Producer

```bash id="prod1"
cd src/producer
pip install pika
python main.py
```

---

## Архитектура

Проект основан на event-driven подходе:

* Producer отправляет события в RabbitMQ
* Consumer обрабатывает события
* Read model обновляется асинхронно

---

## Основные решения

| Решение        | Причина                                |
| -------------- | -------------------------------------- |
| RabbitMQ       | простая настройка для учебного проекта |
| Topic exchange | гибкость маршрутизации                 |
| CQRS           | разделение записи и чтения             |
| at-least-once  | надёжная доставка                      |
| idempotency    | защита от дублей                       |

---

## Итог

Система демонстрирует базовую event-driven архитектуру:

* асинхронная обработка событий
* разделение write/read логики
* расширяемая структура сервисов

```
```
