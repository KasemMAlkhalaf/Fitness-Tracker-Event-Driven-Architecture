"""
Fitness Tracker — Event Consumer (StatisticsService)
Обрабатывает события из RabbitMQ и обновляет Read-модель.
Реализует идемпотентность через processed_event_ids.
"""

import json
import os
import time
from datetime import datetime

import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")

EXCHANGES = {
    "user.events": "topic",
    "workout.events": "topic",
    "exercise.events": "topic",
}

BINDINGS = [
    ("user.events",    "user.created",             "q.statistics.user.created"),
    ("workout.events", "workout.created",           "q.statistics.workout.created"),
    ("workout.events", "workout.exercise.added",    "q.statistics.exercise.added"),
    ("workout.events", "workout.completed",         "q.statistics.workout.completed"),
]

# In-memory Read Model (в реальной системе — Redis / PostgreSQL)
read_model = {
    "users": {},         # user_id -> profile
    "workout_counts": {},  # user_id -> int
    "workout_history": {},  # user_id -> [workout]
}

# Идемпотентность: набор уже обработанных event_id
processed_event_ids: set = set()


# ─── Handlers ────────────────────────────────────────────────────────────────

def handle_user_created(data: dict) -> None:
    user_id = data["user_id"]
    read_model["users"][user_id] = {
        "login": data["login"],
        "full_name": f"{data['first_name']} {data['last_name']}",
        "email": data["email"],
    }
    read_model["workout_counts"][user_id] = 0
    read_model["workout_history"][user_id] = []
    print(f"  [Statistics] Профиль создан для {data['first_name']} {data['last_name']} ({user_id})")


def handle_workout_created(data: dict) -> None:
    user_id = data["user_id"]
    read_model["workout_counts"].setdefault(user_id, 0)
    read_model["workout_counts"][user_id] += 1
    print(f"  [Statistics] Тренировка начата для {user_id}. "
          f"Всего: {read_model['workout_counts'][user_id]}")


def handle_exercise_added(data: dict) -> None:
    print(f"  [Statistics] Упражнение '{data['exercise_name']}' "
          f"добавлено в тренировку {data['workout_id']}")


def handle_workout_completed(data: dict) -> None:
    user_id = data["user_id"]
    record = {
        "workout_id": data["workout_id"],
        "title": data["title"],
        "completed_at": data["completed_at"],
        "duration_minutes": data["duration_minutes"],
        "total_volume_kg": data["total_volume_kg"],
    }
    read_model["workout_history"].setdefault(user_id, []).append(record)
    print(f"  [Statistics] Тренировка завершена: {data['title']} "
          f"({data['duration_minutes']} мин, {data['total_volume_kg']} кг)")
    print_read_model(user_id)


HANDLERS = {
    "UserCreated": handle_user_created,
    "WorkoutCreated": handle_workout_created,
    "ExerciseAddedToWorkout": handle_exercise_added,
    "WorkoutCompleted": handle_workout_completed,
}


def print_read_model(user_id: str) -> None:
    print(f"\n  ─── Read Model для {user_id} ───────────────────────")
    profile = read_model["users"].get(user_id, {})
    print(f"  Пользователь: {profile.get('full_name', '?')} ({profile.get('email', '?')})")
    print(f"  Тренировок: {read_model['workout_counts'].get(user_id, 0)}")
    history = read_model["workout_history"].get(user_id, [])
    for w in history:
        print(f"  • {w['title']} — {w['duration_minutes']} мин, объём {w['total_volume_kg']} кг")
    print(f"  ────────────────────────────────────────────────────\n")


# ─── Message callback ─────────────────────────────────────────────────────────

def on_message(channel, method, properties, body):
    try:
        event = json.loads(body)
        event_id = event.get("event_id", "no-id")
        event_type = event.get("event_type", "unknown")

        # Идемпотентность
        if event_id in processed_event_ids:
            print(f"[Consumer] ⚠️  Дубликат события {event_type} (id={event_id[:8]}...) — пропуск")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"[Consumer] 📨 Получено: {event_type} (id={event_id[:8]}...)")

        handler = HANDLERS.get(event_type)
        if handler:
            handler(event["data"])
            processed_event_ids.add(event_id)
        else:
            print(f"[Consumer] ❓ Нет обработчика для {event_type}")

        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[Consumer] ❌ Ошибка обработки: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ─── Setup & Start ────────────────────────────────────────────────────────────

def connect_with_retry(retries: int = 10, delay: float = 3.0) -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
    )
    for attempt in range(1, retries + 1):
        try:
            print(f"[Consumer] Подключение к RabbitMQ (попытка {attempt}/{retries})...")
            conn = pika.BlockingConnection(params)
            print("[Consumer] Подключение установлено.")
            return conn
        except pika.exceptions.AMQPConnectionError as e:
            if attempt == retries:
                raise
            print(f"[Consumer] Не удалось подключиться: {e}. Повтор через {delay}с...")
            time.sleep(delay)


def main():
    conn = connect_with_retry()
    channel = conn.channel()

    # Объявляем exchanges
    for exchange, ex_type in EXCHANGES.items():
        channel.exchange_declare(exchange=exchange, exchange_type=ex_type, durable=True)

    # Объявляем очереди и binding'и
    for exchange, routing_key, queue_name in BINDINGS:
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)
        channel.basic_consume(queue=queue_name, on_message_callback=on_message)
        print(f"[Consumer] Слушаем: {queue_name} ({exchange} -> {routing_key})")

    channel.basic_qos(prefetch_count=1)
    print("\n[Consumer] Ожидание событий... (Ctrl+C для выхода)\n")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[Consumer] Остановка.")
        channel.stop_consuming()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
