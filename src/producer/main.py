import json
import uuid
import time
import os
from datetime import datetime, timezone

import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")

EXCHANGES = {
    "user": "user.events",
    "workout": "workout.events",
    "exercise": "exercise.events",
}


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
            print(f"[Producer] Подключение к RabbitMQ (попытка {attempt}/{retries})...")
            conn = pika.BlockingConnection(params)
            print("[Producer] Подключение установлено.")
            return conn
        except pika.exceptions.AMQPConnectionError as e:
            if attempt == retries:
                raise
            print(f"[Producer] Не удалось подключиться: {e}. Повтор через {delay}с...")
            time.sleep(delay)


def setup_exchanges(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    for name, exchange in EXCHANGES.items():
        channel.exchange_declare(
            exchange=exchange,
            exchange_type="topic",
            durable=True,
        )
        print(f"[Producer] Exchange объявлен: {exchange}")


def make_event(event_type: str, data: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "data": data,
    }


def publish(channel, exchange: str, routing_key: str, event: dict) -> None:
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(event, ensure_ascii=False),
        properties=pika.BasicProperties(
            delivery_mode=2,          # persistent message
            content_type="application/json",
            message_id=event["event_id"],
        ),
    )
    print(f"[Producer] ✅ Опубликовано [{routing_key}]: {event['event_type']} (id={event['event_id'][:8]}...)")


def main():
    conn = connect_with_retry()
    channel = conn.channel()
    setup_exchanges(channel)

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    user_event = make_event("UserCreated", {
        "user_id": user_id,
        "login": "ivan_petrov",
        "first_name": "Иван",
        "last_name": "Петров",
        "email": "ivan@example.com",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    publish(channel, EXCHANGES["user"], "user.created", user_event)
    time.sleep(1)

    workout_id = f"wkt_{uuid.uuid4().hex[:8]}"
    workout_event = make_event("WorkoutCreated", {
        "workout_id": workout_id,
        "user_id": user_id,
        "title": "Силовая тренировка",
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS",
    })
    publish(channel, EXCHANGES["workout"], "workout.created", workout_event)
    time.sleep(1)

    exercise_added = make_event("ExerciseAddedToWorkout", {
        "workout_id": workout_id,
        "user_id": user_id,
        "exercise_id": "ex_bench_press",
        "exercise_name": "Жим лёжа",
        "sets": 4,
        "reps": 10,
        "weight_kg": 70,
        "duration_seconds": None,
        "order_index": 1,
    })
    publish(channel, EXCHANGES["workout"], "workout.exercise.added", exercise_added)
    time.sleep(1)

    completed_event = make_event("WorkoutCompleted", {
        "workout_id": workout_id,
        "user_id": user_id,
        "title": "Силовая тренировка",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 55,
        "exercises_count": 4,
        "total_sets": 16,
        "total_volume_kg": 3500,
    })
    publish(channel, EXCHANGES["workout"], "workout.completed", completed_event)

    print("\n[Producer] Все события опубликованы. Завершение.")
    conn.close()


if __name__ == "__main__":
    main()
