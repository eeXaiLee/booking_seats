"""Модуль с константами, используемыми в приложении."""

# Автоматизация создания миграций БД
convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

# JWT Types
ACCESS_TOKEN_TYPE = 'access'
REFRESH_TOKEN_TYPE = 'refresh'

# JWT Claims
JWT_EXP = 'exp'
JWT_TYPE = 'type'
JWT_JTI = 'jti'
JWT_USER_ID = 'user_id'

# Error messages JWT
INVALID_TOKEN = 'Невалидный токен'
INVALID_TOKEN_TYPE = 'Невалидный тип токена'
INVALID_TOKEN_USER_ID = 'Невалидный токен: отсутствует user_id'
INVALID_TOKEN_JTI_OR_USER_ID = 'Невалидный токен: отсутствует jti или user_id'
INVALID_TOKEN_SIGNATURE = 'Невалидная подпись токена'
TOKEN_NOT_FOUND = 'Токен не найден в базе'
TOKEN_REVOKED = 'Токен отозван'
TOKEN_EXPIRED = 'Токен истёк'

# Error messages Booking
BOOKING_PAST_DATE_ERROR = 'Нельзя создать бронирование на прошедшую дату.'
BOOKING_TABLES_BUSY_ERROR = 'Один или несколько столов уже заняты в этот слот.'
BOOKING_USER_CONFLICT_ERROR = (
    'Бронирования пользователя не должны пересекаться.'
)
BOOKING_CANNOT_UPDATE_ACTIVE_ERROR = (
    'Нельзя изменить бронирование со статусом active.'
)
BOOKING_CANNOT_UPDATE_PAST_ERROR = 'Нельзя изменить прошедшее бронирование.'
BOOKING_TABLES_NOT_FOUND_ERROR = 'Не все столы найдены.'
BOOKING_SLOTS_NOT_FOUND_ERROR = 'Не все временные слоты найдены.'
BOOKING_CAFE_MISMATCH_ERROR = 'Выбран стол или слот из другого кафе.'
BOOKING_CREATION_ERROR = 'Бронирование не найдено после создания.'
BOOKING_UPDATE_ERROR = 'Бронирование не найдено после обновления.'

# Error messages Cafe
CAFE_NOT_FOUND_AFTER_CREATE = 'Кафе не найдено после создания.'
CAFE_NOT_FOUND_AFTER_UPDATE = 'Кафе не найдено после обновления.'

# Error messages Tables
TABLE_NOT_FOUND_AFTER_CREATE = 'Стол не найден после создания.'
TABLE_NOT_FOUND_AFTER_UPDATE = 'Стол не найден после обновления.'

# Error messages Timeslot
TIME_SLOT_ERROR = 'Время начала слота должно быть раньше времени окончания!'

# Кодировка
ENCODING = 'utf-8'

# Logging constants
SYSTEM_USER_ID = 'SYSTEM'
SYSTEM_USERNAME = 'Событие выполнено приложением'
INIT_DB = 'Инициализация БД'

# Domain events constants
DOMAIN_EVENTS_QUEUE = 'domain.events'
DOMAIN_EVENTS_EXCHANGE = 'domain.events'
DOMAIN_EVENTS_ROUTING_KEY = 'domain.events'
OUTBOX_STATUS_PENDING = 'pending'
OUTBOX_STATUS_PUBLISHED = 'published'
OUTBOX_STATUS_FAILED = 'failed'

# Health-check thresholds
HEALTH_PENDING_STALE_MINUTES = 5
HEALTH_PENDING_WARN_COUNT = 10
HEALTH_FAILED_WARN_COUNT = 1

# Booking model constants
NOTE_MAX_LENGTH = 255

# Cafe model constants
CAFE_NAME_MAX_LENGTH = 255
ADDRESS_MAX_LENGTH = 255
PHONE_MAX_LENGTH = 20

# Dish model constants
DISH_MAX_LENGTH = 255

# Token model constants
TOKEN_HASH_MAX_LENGTH = 64

# User model constants
USER_NAME_MAX_LENGTH = 255
USER_PASSWORD_MAX_LENGTH = 255
USER_EMAIL_MAX_LENGTH = 255
USER_PHONE_MAX_LENGTH = 255

# Booking Schemas Constants
BOOKING_MIN_TABLES_COUNT = 1
BOOKING_MIN_SLOTS_COUNT = 1
GUEST_NUBMBER_MIN = 0
GUEST_NUBMBER_MAX = 20

STATUS_BOOK = 0
STATUS_CANCEL = 1
STATUS_ACTIVE = 2

# Cafe Schemas Constants
CAFE_DESCRIPTION_MIN_LENGTH = 1
CAFE_DESCRIPTION_MAX_LENGTH = 10000

# Table Schemas Constants
TABLE_MIN_SEAT_NUMBER = 1
TABLE_MAX_SEAT_NUMBER = 60
TABLE_DESCRIPTION_MIN_LENGTH = 1
TABLE_DESCRIPTION_MAX_LENGTH = 10000

# Timeslot Schemas Constants
DESCRIPTION_MAX_LENGTH = 255

# Media error messages
MEDIA_FILE_TOO_LARGE = 'Размер файла превышает 5 MB.'
MEDIA_INVALID_TYPE = (
    'Недопустимый тип файла. Разрешены: image/jpeg, image/png.'
)
MEDIA_INVALID_EXTENSION = (
    'Недопустимое расширение. Разрешены: .jpg, .jpeg, .png.'
)
MEDIA_CORRUPTED_IMAGE = 'Файл поврежден или не является изображением.'
MEDIA_NOT_FOUND = 'Изображение не найдено.'
MEDIA_INVALID_UUID = 'Неверный формат UUID. Ожидается UUID4.'
MEDIA_SAVE_ERROR = 'Ошибка сохранения файла.'
MEDIA_PROCESS_ERROR = 'Ошибка обработки изображения'

# Regex Patterns
USERNAME_PATTERN = r'^[A-Za-z][A-Za-z0-9_]{2,254}$'
PHONE_PATTERN = r'^(\+7|8)9\d{9}$'
EMAIL_PATTERN = r'^[\w.-]{1,255}@[A-Za-z.-]{1,255}\.[A-Za-z]{2,10}'
TG_ID_PATTERN = r'^\d{1,128}$'

DESCRIPTION_PATTERN = r'^[\s\S]{1,500}$'
DISH_NAME_PATTERN = r'^[A-Za-zА-Яа-яЁё0-9\s\-.,!?()&«»"\'№/+%]{3,255}$'
PRICE_PATTERN = r'^\d{1,6}(\.\d{1,2})?$'

DESCRIPTION_MIN_LENGTH = 1
DESCRIPTION_MAX_LENGTH = 10000
