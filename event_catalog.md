# Event Catalog — Fitness Tracker

> Каталог событий системы.  
> Описаны основные поля, кто создаёт события и кто их обрабатывает.

---

## 1. UserCreated

| Поле | Значение |
|---|---|
| Название | UserCreated |
| Exchange | user.events |
| Routing Key | user.created |
| Producer | UserService |
| Consumers | StatisticsService, NotificationService |
| Delivery | at-least-once |

### Payload

```json
{
  "event_id": "uuid",
  "event_type": "UserCreated",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "usr_123",
    "login": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  }
}
````

---

## 2. ExerciseCreated

| Поле        | Значение         |
| ----------- | ---------------- |
| Название    | ExerciseCreated  |
| Exchange    | exercise.events  |
| Routing Key | exercise.created |
| Producer    | ExerciseService  |
| Consumers   | CatalogService   |
| Delivery    | at-least-once    |

### Payload

```json
{
  "event_id": "uuid",
  "event_type": "ExerciseCreated",
  "timestamp": "2024-01-15T11:00:00Z",
  "data": {
    "exercise_id": "ex_456",
    "name": "Приседания со штангой",
    "type": "STRENGTH",
    "muscle_group": "LEGS"
  }
}
```

---

## 3. WorkoutCreated

| Поле        | Значение          |
| ----------- | ----------------- |
| Название    | WorkoutCreated    |
| Exchange    | workout.events    |
| Routing Key | workout.created   |
| Producer    | WorkoutService    |
| Consumers   | StatisticsService |
| Delivery    | at-least-once     |

### Payload

```json
{
  "event_id": "uuid",
  "event_type": "WorkoutCreated",
  "timestamp": "2024-01-15T09:00:00Z",
  "data": {
    "workout_id": "wkt_789",
    "user_id": "usr_123",
    "title": "Тренировка ног",
    "status": "IN_PROGRESS"
  }
}
```

---

## 4. ExerciseAddedToWorkout

| Поле        | Значение               |
| ----------- | ---------------------- |
| Название    | ExerciseAddedToWorkout |
| Exchange    | workout.events         |
| Routing Key | workout.exercise.added |
| Producer    | WorkoutService         |
| Consumers   | StatisticsService      |
| Delivery    | at-least-once          |

### Payload

```json
{
  "event_id": "uuid",
  "event_type": "ExerciseAddedToWorkout",
  "timestamp": "2024-01-15T09:05:00Z",
  "data": {
    "workout_id": "wkt_789",
    "exercise_name": "Жим лёжа",
    "sets": 4,
    "reps": 10,
    "weight_kg": 70
  }
}
```

---

## 5. WorkoutCompleted

| Поле        | Значение                               |
| ----------- | -------------------------------------- |
| Название    | WorkoutCompleted                       |
| Exchange    | workout.events                         |
| Routing Key | workout.completed                      |
| Producer    | WorkoutService                         |
| Consumers   | StatisticsService, NotificationService |
| Delivery    | at-least-once                          |

### Payload

```json
{
  "event_id": "uuid",
  "event_type": "WorkoutCompleted",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "workout_id": "wkt_789",
    "user_id": "usr_123",
    "title": "Тренировка ног",
    "duration_minutes": 60,
    "total_volume_kg": 4200
  }
}
```

---

## Сводка

| Событие                | Producer        | Consumers                              | Delivery      |
| ---------------------- | --------------- | -------------------------------------- | ------------- |
| UserCreated            | UserService     | StatisticsService, NotificationService | at-least-once |
| ExerciseCreated        | ExerciseService | CatalogService                         | at-least-once |
| WorkoutCreated         | WorkoutService  | StatisticsService                      | at-least-once |
| ExerciseAddedToWorkout | WorkoutService  | StatisticsService                      | at-least-once |
| WorkoutCompleted       | WorkoutService  | StatisticsService, NotificationService | at-least-once |
