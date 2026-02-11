from drf_spectacular.utils import OpenApiExample

VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    name="ValidationError",
    value={
        "error": "ValidationError",
        "message": "Email обязателен для заполнения",
    },
    response_only=True,
    status_codes=["400"],
)

NOT_FOUND_ERROR_EXAMPLE = OpenApiExample(
    name="NotFoundError",
    value={
        "error": "NotFoundError",
        "message": "Проект не найден",
    },
    response_only=True,
    status_codes=["404"],
)

PERMISSION_DENIED_ERROR_EXAMPLE = OpenApiExample(
    name="PermissionDeniedError",
    value={
        "error": "PermissionDeniedError",
        "message": "У вас нет прав для выполнения этого действия",
    },
    response_only=True,
    status_codes=["403"],
)

CONFLICT_ERROR_EXAMPLE = OpenApiExample(
    name="ConflictError",
    value={
        "error": "ConflictError",
        "message": "Пользователь с таким email уже существует",
    },
    response_only=True,
    status_codes=["409"],
)
