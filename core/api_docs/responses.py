from drf_spectacular.utils import OpenApiResponse


class ValidationErrorResponse:
    @staticmethod
    def get(description: str = "Ошибка валидации данных", examples=None):
        return OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "ValidationError"},
                    "message": {"type": "string"},
                },
            },
            description=description,
            examples=examples,
        )


class NotFoundErrorResponse:
    @staticmethod
    def get(description: str = "Объект не найден", examples=None):
        return OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "NotFoundError"},
                    "message": {"type": "string"},
                },
            },
            description=description,
            examples=examples,
        )


class PermissionDeniedErrorResponse:
    @staticmethod
    def get(description: str = "Доступ запрещён", examples=None):
        return OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "PermissionDeniedError"},
                    "message": {"type": "string"},
                },
            },
            description=description,
            examples=examples,
        )


class ConflictErrorResponse:
    @staticmethod
    def get(description: str = "Конфликт данных", examples=None):
        return OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "ConflictError"},
                    "message": {"type": "string"},
                },
            },
            description=description,
            examples=examples,
        )
