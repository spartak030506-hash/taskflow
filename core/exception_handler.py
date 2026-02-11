from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .exceptions import (
    BaseServiceError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PermissionDeniedError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, BaseServiceError):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        return None

    return Response(
        {
            "error": exc.__class__.__name__,
            "message": exc.message,
            **exc.extra,
        },
        status=status_code,
    )
