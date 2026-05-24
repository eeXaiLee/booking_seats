# Booking Cafe Backend

Бэкенд сервиса бронирования мест в кафе на FastAPI + PostgreSQL + RabbitMQ + Celery.

## Технологии

1. FastAPI (API слой)
2. SQLAlchemy + Alembic (данные и миграции)
3. RabbitMQ (транспорт событий)
4. Celery + Celery Beat (фоновые задачи)
5. Flower (мониторинг задач Celery)
6. smtp4dev (локальный SMTP для разработки)

## Быстрый старт (Docker)

1. Скопируйте переменные окружения:

```shell
cp infra/.env.example infra/.env
```

`infra/.env` — единственный source of truth для runtime-настроек.
Не дублируйте туда отдельный `SYNC_DATABASE_URL`: приложение и Celery теперь
собирают DSN автоматически из `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`.

2. Поднимите сервисы:

```shell
docker compose --env-file infra/.env -f infra/docker-compose.yml up --build -d
```

3. Проверьте статус:

```shell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

## Основные URL

1. API docs: http://localhost:8000/docs
2. Flower: http://localhost:5555
3. RabbitMQ Management: http://localhost:15672
4. smtp4dev UI: http://localhost:5001

## Flower (требование ТЗ)

Flower поднимается как отдельный сервис в docker compose и запускается с опциями:

1. Basic Auth через `FLOWER_BASIC_AUTH`
2. Broker API по умолчанию собирается из `RABBITMQ_USER`, `RABBITMQ_PASS`, `DOCKER_RABBITMQ_HOST`, `RABBITMQ_MANAGEMENT_PORT`
3. Опциональный override через `FLOWER_BROKER_API`
4. Опциональный URL prefix через `FLOWER_URL_PREFIX`

Пример из `infra/.env.example`:

```env
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:admin
# FLOWER_BROKER_API=http://admin:adminpass@rabbitmq:15672/api/
FLOWER_URL_PREFIX=
```

`BROKER_URL` для Celery больше не используется, чтобы пароль RabbitMQ не расходился между сервисами.

### Проверки Flower

Проверка, что Flower отвечает и требует авторизацию:

```shell
curl -s -o /dev/null -w "%{http_code}" http://localhost:5555/
```

Ожидаемо: `401`.

Проверка входа с basic auth:

```shell
curl -s -o /dev/null -w "%{http_code}" -u admin:admin http://localhost:5555/
```

Ожидаемо: `200`.

### Что смотреть в Flower

1. Active/Reserved/Queued задачи
2. Failed и Retried задачи
3. Время выполнения задач (runtime)
4. Состояние воркеров (online/offline, concurrency)

## Асинхронный pipeline

Используется схема Outbox -> RabbitMQ -> Consumer -> Celery task:

1. Service-слой пишет бизнес-изменение и outbox-событие в одной транзакции
2. Задача `publish_pending_outbox_events` публикует `pending` события в `domain.events`
3. Задача `consume_domain_events` читает события и маршрутизирует их в Celery-задачи
4. Идемпотентность обеспечивается таблицей `processed_event`

## Сквозная трассировка (`X-Request-ID`)

Для наблюдаемости добавлен correlation id по всей цепочке обработки:

1. API принимает `X-Request-ID` из запроса или генерирует новый
2. API возвращает `X-Request-ID` в ответе
3. `correlation_id` сохраняется в payload outbox-события
4. Publisher, consumer и email-задачи логируют `request_id`

Пример вызова с фиксированным идентификатором:

```shell
curl -H "X-Request-ID: demo-trace-001" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"cafe_id":1,"booking_date":"2026-03-27","guest_number":2,"tables_id":[1],"slots_id":[1]}' \
  http://localhost:8000/bookings/
```

После этого в логах можно искать `request_id=demo-trace-001` и видеть полный путь от HTTP до SMTP.

## Локальная разработка (без Docker)

1. Создать виртуальное окружение и установить зависимости из `src/requirements.txt`
2. Поднять PostgreSQL и RabbitMQ
3. Применить миграции Alembic
4. Запустить API, Celery worker, Celery beat отдельно

## Production deploy

Production deploy читает значения только из серверного `infra/.env`.
Это относится и к `DOCKERHUB_USERNAME`, и к `POSTGRES_*` переменным.
GitHub Actions больше не перерисовывает production compose значениями из secrets
перед копированием на сервер.

## Стилистика

Проверка Ruff:

```shell
ruff check
```

Автоисправления:

```shell
ruff check --fix
```

Установка pre-commit hooks:

```shell
pre-commit install
```
