# Event Catalog — Fitness Tracker

> Каталог всех событий системы с описанием структуры, производителей, потребителей и гарантий доставки.

---

## 1. UserCreated

| Поле | Значение |
|---|---|
| **Название** | `UserCreated` |
| **Exchange** | `user.events` |
| **Routing Key** | `user.created` |
| **Производитель** | `UserService` |
| **Потребители** | `StatisticsService`, `NotificationService` |
| **Гарантии доставки** | at-least-once |

### Payload

```json
{
  "event_id": "uuid-v4",
  "event_type": "UserCreated",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0",
  "data": {
    "user_id": "usr_123",
    "login": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Действия потребителей

- **StatisticsService**: создать пустой профиль статистики пользователя
- **NotificationService**: отправить приветственный email

---

## 2. ExerciseCreated

| Поле | Значение |
|---|---|
| **Название** | `ExerciseCreated` |
| **Exchange** | `exercise.events` |
| **Routing Key** | `exercise.created` |
| **Производитель** | `ExerciseService` |
| **Потребители** | `CatalogService` (read-side cache обновление) |
| **Гарантии доставки** | at-least-once |

### Payload

```json
{
  "event_id": "uuid-v4",
  "event_type": "ExerciseCreated",
  "timestamp": "2024-01-15T11:00:00Z",
  "version": "1.0",
  "data": {
    "exercise_id": "ex_456",
    "name": "Приседания со штангой",
    "type": "STRENGTH",
    "muscle_group": "LEGS",
    "description": "Базовое упражнение для ног",
    "created_by": "usr_123",
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 3. WorkoutCreated

| Поле | Значение |
|---|---|
| **Название** | `WorkoutCreated` |
| **Exchange** | `workout.events` |
| **Routing Key** | `workout.created` |
| **Производитель** | `WorkoutService` |
| **Потребители** | `StatisticsService` |
| **Гарантии доставки** | at-least-once |

### Payload

```json
{
  "event_id": "uuid-v4",
  "event_type": "WorkoutCreated",
  "timestamp": "2024-01-15T09:00:00Z",
  "version": "1.0",
  "data": {
    "workout_id": "wkt_789",
    "user_id": "usr_123",
    "title": "Тренировка ног",
    "scheduled_at": "2024-01-15T09:00:00Z",
    "status": "IN_PROGRESS"
  }
}
```

### Действия потребителей

- **StatisticsService**: увеличить счётчик начатых тренировок

---

## 4. ExerciseAddedToWorkout

| Поле | Значение |
|---|---|
| **Название** | `ExerciseAddedToWorkout` |
| **Exchange** | `workout.events` |
| **Routing Key** | `workout.exercise.added` |
| **Производитель** | `WorkoutService` |
| **Потребители** | `StatisticsService` |
| **Гарантии доставки** | at-least-once |

### Payload

```json
{
  "event_id": "uuid-v4",
  "event_type": "ExerciseAddedToWorkout",
  "timestamp": "2024-01-15T09:05:00Z",
  "version": "1.0",
  "data": {
    "workout_id": "wkt_789",
    "user_id": "usr_123",
    "exercise_id": "ex_456",
    "exercise_name": "Приседания со штангой",
    "sets": 4,
    "reps": 8,
    "weight_kg": 80,
    "duration_seconds": null,
    "order_index": 1
  }
}
```

### Действия потребителей

- **StatisticsService**: обновить историю упражнений пользователя в Read-модели

---

## 5. WorkoutCompleted

| Поле | Значение |
|---|---|
| **Название** | `WorkoutCompleted` |
| **Exchange** | `workout.events` |
| **Routing Key** | `workout.completed` |
| **Производитель** | `WorkoutService` |
| **Потребители** | `StatisticsService`, `NotificationService` |
| **Гарантии доставки** | at-least-once |

### Payload

```json
{
  "event_id": "uuid-v4",
  "event_type": "WorkoutCompleted",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.0",
  "data": {
    "workout_id": "wkt_789",
    "user_id": "usr_123",
    "title": "Тренировка ног",
    "started_at": "2024-01-15T09:00:00Z",
    "completed_at": "2024-01-15T10:00:00Z",
    "duration_minutes": 60,
    "exercises_count": 5,
    "total_sets": 18,
    "total_volume_kg": 4200
  }
}
```

### Действия потребителей

- **StatisticsService**: записать итоги тренировки, обновить агрегаты за период
- **NotificationService**: отправить уведомление о завершении тренировки

---

## Сводная таблица

| Событие | Exchange | Routing Key | Producer | Consumers | Delivery |
|---|---|---|---|---|---|
| `UserCreated` | `user.events` | `user.created` | UserService | Statistics, Notification | at-least-once |
| `ExerciseCreated` | `exercise.events` | `exercise.created` | ExerciseService | CatalogService | at-least-once |
| `WorkoutCreated` | `workout.events` | `workout.created` | WorkoutService | StatisticsService | at-least-once |
| `ExerciseAddedToWorkout` | `workout.events` | `workout.exercise.added` | WorkoutService | StatisticsService | at-least-once |
| `WorkoutCompleted` | `workout.events` | `workout.completed` | WorkoutService | Statistics, Notification | at-least-once |
