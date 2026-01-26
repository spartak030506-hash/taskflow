class BaseServiceError(Exception):
    default_message = "Произошла ошибка"

    def __init__(self, message: str = None, **kwargs):
        self.message = message or self.default_message
        self.extra = kwargs
        super().__init__(self.message)


class NotFoundError(BaseServiceError):
    default_message = "Объект не найден"


class PermissionDeniedError(BaseServiceError):
    default_message = "Доступ запрещён"


class ValidationError(BaseServiceError):
    default_message = "Ошибка валидации"


class ConflictError(BaseServiceError):
    default_message = "Конфликт данных"
