# Event-Driven Architecture: Fitness Tracker (Вариант 14)

## 1. Анализ событий в системе

### Домен и основные сущности
- **User** — пользователь приложения (логин, имя, фамилия, email)
- **Exercise** — упражнение (название, тип, описание)
- **Workout** — тренировка (дата, список упражнений, пользователь)

---

## 2. Команды и события

### Команды (Commands — инициируют изменения состояния)

| Команда | Описание |
|---|---|
| `CreateUser` | Регистрация нового пользователя |
| `CreateExercise` | Добавление нового упражнения в каталог |
| `CreateWorkout` | Создание новой тренировки |
| `AddExerciseToWorkout` | Добавление упражнения в тренировку |

### События (Events — факты, которые уже произошли)

| Событие | Источник команды |
|---|---|
| `UserCreated` | `CreateUser` |
| `ExerciseCreated` | `CreateExercise` |
| `WorkoutCreated` | `CreateWorkout` |
| `ExerciseAddedToWorkout` | `AddExerciseToWorkout` |
| `WorkoutCompleted` | (автоматически при закрытии тренировки) |

---

## 3. Producers и Consumers

### Event Producers

| Сервис | Публикуемые события |
|---|---|
| **UserService** | `UserCreated` |
| **ExerciseService** | `ExerciseCreated` |
| **WorkoutService** | `WorkoutCreated`, `ExerciseAddedToWorkout`, `WorkoutCompleted` |

### Event Consumers

| Событие | Consumer | Действие |
|---|---|---|
| `UserCreated` | **NotificationService** | Отправить приветственное письмо |
| `UserCreated` | **StatisticsService** | Инициализировать профиль статистики |
| `WorkoutCreated` | **StatisticsService** | Обновить счётчик тренировок |
| `WorkoutCompleted` | **StatisticsService** | Записать итоги тренировки |
| `WorkoutCompleted` | **NotificationService** | Отправить поздравление |
| `ExerciseAddedToWorkout` | **StatisticsService** | Обновить историю упражнений |

---

## 4. Архитектурная схема

```
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway                                │
└──────────┬──────────────┬────────────────┬────────────────────────┘
           │              │                │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
    │ UserService │ │ Exercise   │ │  Workout    │
    │  (Write)    │ │ Service    │ │  Service    │
    │             │ │  (Write)   │ │  (Write)    │
    └──────┬──────┘ └─────┬──────┘ └──────┬──────┘
           │              │               │
           └──────────────┴───────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   RabbitMQ Broker  │
                    │                   │
                    │  Exchanges:       │
                    │  • user.events    │
                    │  • workout.events │
                    │  • exercise.events│
                    └─────────┬─────────┘
                              │
           ┌──────────────────┴───────────────────┐
           │                                      │
    ┌──────▼──────────┐                  ┌────────▼──────────┐
    │ StatisticsService│                  │ NotificationService│
    │   (Read Model)   │                  │                   │
    └──────────────────┘                  └───────────────────┘
           │
    ┌──────▼──────────┐
    │  Read DB (Redis │
    │  / PostgreSQL)  │
    └─────────────────┘
```

---

## 5. Выбор брокера сообщений: RabbitMQ

**Обоснование выбора RabbitMQ над Kafka:**

| Критерий | RabbitMQ | Kafka |
|---|---|---|
| Сложность | Низкая | Высокая |
| Гарантии доставки | at-least-once, можно exactly-once через идемпотентность | exactly-once нативно |
| Подходит для | Небольших команд, event-driven микросервисов | Высоконагруженных потоков данных |
| Маршрутизация | Гибкая (exchanges, bindings) | По топикам и партициям |

Для фитнес-трекера с умеренной нагрузкой RabbitMQ является оптимальным выбором.

### Топология RabbitMQ

```
Exchange: user.events       (type: topic)
  └── Queue: user.created.statistics
  └── Queue: user.created.notifications

Exchange: workout.events    (type: topic)
  └── Queue: workout.created.statistics
  └── Queue: workout.completed.statistics
  └── Queue: workout.completed.notifications
  └── Queue: exercise.added.statistics

Exchange: exercise.events   (type: topic)
  └── Queue: exercise.created.catalog
```

### Гарантии доставки

- **at-least-once** — основной режим для всех событий.  
  Consumers подтверждают сообщения (`ack`) только после успешной обработки.
- **Идемпотентность на стороне Consumer** — каждый обработчик проверяет, не было ли событие уже обработано (по `event_id` в БД).

---

## 6. Паттерн CQRS

CQRS (Command Query Responsibility Segregation) применяется для разделения операций записи и чтения.

### Применимость в Fitness Tracker

Система имеет явное разделение:
- **Команды (Write)**: создание пользователей, тренировок, упражнений
- **Запросы (Read)**: история тренировок, статистика за период, поиск пользователей

### CQRS-схема

```
Команды (Write Side)                    Запросы (Read Side)
─────────────────────                   ──────────────────────
CreateUser ──► UserService              GetWorkoutHistory ──► StatisticsService
               │  (Write DB)                                    (Read DB / Cache)
               │
               ▼ UserCreated event
         RabbitMQ Broker
               │
               ▼
         StatisticsService
         (обновляет Read DB)
```

### Read vs Write модели

| Операция | Тип | Модель |
|---|---|---|
| `POST /users` | Command (Write) | UserService + Write DB |
| `GET /users?login=...` | Query (Read) | StatisticsService + Read DB |
| `POST /workouts` | Command (Write) | WorkoutService + Write DB |
| `GET /users/{id}/workouts` | Query (Read) | StatisticsService + Read DB |
| `GET /users/{id}/stats?from=...&to=...` | Query (Read) | StatisticsService + Read DB |

### Синхронизация Read и Write моделей

1. Write-сервис сохраняет данные в основную БД (PostgreSQL).
2. Write-сервис публикует событие в RabbitMQ.
3. StatisticsService (Consumer) получает событие и обновляет Read-модель (денормализованные таблицы / Redis).
4. Read-запросы идут напрямую к Read-модели — быстро, без JOIN'ов.

**Eventual Consistency:** Между записью команды и обновлением Read-модели возможна небольшая задержка. Для фитнес-трекера это приемлемо.
