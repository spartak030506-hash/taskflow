from typing import List, Optional
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .responses import (
    ValidationErrorResponse,
    NotFoundErrorResponse,
    PermissionDeniedErrorResponse,
    ConflictErrorResponse,
)
from .examples import (
    VALIDATION_ERROR_EXAMPLE,
    NOT_FOUND_ERROR_EXAMPLE,
    PERMISSION_DENIED_ERROR_EXAMPLE,
    CONFLICT_ERROR_EXAMPLE,
)


def list_endpoint_schema(
    summary: str,
    description: str,
    tags: List[str],
    parameters: Optional[List[OpenApiParameter]] = None,
    examples: Optional[List[OpenApiExample]] = None,
):
    return extend_schema(
        summary=summary,
        description=description,
        tags=tags,
        parameters=parameters or [],
        examples=examples or [],
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Не авторизован'},
            status.HTTP_403_FORBIDDEN: PermissionDeniedErrorResponse.get(
                examples=[PERMISSION_DENIED_ERROR_EXAMPLE]
            ),
        },
    )


def create_endpoint_schema(
    summary: str,
    description: str,
    tags: List[str],
    request_examples: Optional[List[OpenApiExample]] = None,
    response_examples: Optional[List[OpenApiExample]] = None,
):
    return extend_schema(
        summary=summary,
        description=description,
        tags=tags,
        examples=(request_examples or []) + (response_examples or []),
        responses={
            status.HTTP_201_CREATED: None,
            status.HTTP_400_BAD_REQUEST: ValidationErrorResponse.get(
                examples=[VALIDATION_ERROR_EXAMPLE]
            ),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Не авторизован'},
            status.HTTP_403_FORBIDDEN: PermissionDeniedErrorResponse.get(
                examples=[PERMISSION_DENIED_ERROR_EXAMPLE]
            ),
            status.HTTP_409_CONFLICT: ConflictErrorResponse.get(
                examples=[CONFLICT_ERROR_EXAMPLE]
            ),
        },
    )


def retrieve_endpoint_schema(
    summary: str,
    description: str,
    tags: List[str],
    examples: Optional[List[OpenApiExample]] = None,
):
    return extend_schema(
        summary=summary,
        description=description,
        tags=tags,
        examples=examples or [],
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_401_UNAUTHORIZED: {'description': 'Не авторизован'},
            status.HTTP_403_FORBIDDEN: PermissionDeniedErrorResponse.get(
                examples=[PERMISSION_DENIED_ERROR_EXAMPLE]
            ),
            status.HTTP_404_NOT_FOUND: NotFoundErrorResponse.get(
                examples=[NOT_FOUND_ERROR_EXAMPLE]
            ),
        },
    )


def update_endpoint_schema(
    summary: str,
    description: str,
    tags: List[str],
    request_examples: Optional[List[OpenApiExample]] = None,
    response_examples: Optional[List[OpenApiExample]] = None,
):
    return extend_schema(
        summary=summary,
        description=description,
        tags=tags,
        examples=(request_examples or []) + (response_examples or []),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: ValidationErrorResponse.get(
                examples=[VALIDATION_ERROR_EXAMPLE]
            ),
            status.HTTP_401_UNAUTHORIZED: {'description': 'Не авторизован'},
            status.HTTP_403_FORBIDDEN: PermissionDeniedErrorResponse.get(
                examples=[PERMISSION_DENIED_ERROR_EXAMPLE]
            ),
            status.HTTP_404_NOT_FOUND: NotFoundErrorResponse.get(
                examples=[NOT_FOUND_ERROR_EXAMPLE]
            ),
        },
    )


def delete_endpoint_schema(
    summary: str,
    description: str,
    tags: List[str],
):
    return extend_schema(
        summary=summary,
        description=description,
        tags=tags,
        responses={
            status.HTTP_204_NO_CONTENT: {'description': 'Успешно удалено'},
            status.HTTP_401_UNAUTHORIZED: {'description': 'Не авторизован'},
            status.HTTP_403_FORBIDDEN: PermissionDeniedErrorResponse.get(
                examples=[PERMISSION_DENIED_ERROR_EXAMPLE]
            ),
            status.HTTP_404_NOT_FOUND: NotFoundErrorResponse.get(
                examples=[NOT_FOUND_ERROR_EXAMPLE]
            ),
        },
    )


def action_endpoint_schema(
    summary: str,
    description: str,
    tags: List[str],
    method: str = 'POST',
    request_examples: Optional[List[OpenApiExample]] = None,
    response_examples: Optional[List[OpenApiExample]] = None,
    custom_responses: Optional[dict] = None,
):
    default_responses = {
        status.HTTP_200_OK: None,
        status.HTTP_400_BAD_REQUEST: ValidationErrorResponse.get(
            examples=[VALIDATION_ERROR_EXAMPLE]
        ),
        status.HTTP_401_UNAUTHORIZED: {'description': 'Не авторизован'},
        status.HTTP_403_FORBIDDEN: PermissionDeniedErrorResponse.get(
            examples=[PERMISSION_DENIED_ERROR_EXAMPLE]
        ),
        status.HTTP_404_NOT_FOUND: NotFoundErrorResponse.get(
            examples=[NOT_FOUND_ERROR_EXAMPLE]
        ),
    }

    if custom_responses:
        default_responses.update(custom_responses)

    return extend_schema(
        summary=summary,
        description=description,
        tags=tags,
        methods=[method],
        examples=(request_examples or []) + (response_examples or []),
        responses=default_responses,
    )
