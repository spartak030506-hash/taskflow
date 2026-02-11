from django.db.models import Count, Max, Q, QuerySet

from core.exceptions import NotFoundError

from .models import EmailVerificationToken, PasswordResetToken, User


def get_by_id(user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFoundError("Пользователь не найден")


def get_by_email(email: str) -> User:
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        raise NotFoundError("Пользователь не найден")


def filter_active() -> QuerySet[User]:
    return User.objects.filter(is_active=True)


def exists_email(email: str) -> bool:
    return User.objects.filter(email=email).exists()


def get_verification_token(token: str) -> EmailVerificationToken:
    try:
        return EmailVerificationToken.objects.select_related("user").get(token=token)
    except EmailVerificationToken.DoesNotExist:
        raise NotFoundError("Токен верификации не найден")


def get_password_reset_token(token: str) -> PasswordResetToken:
    try:
        return PasswordResetToken.objects.select_related("user").get(token=token)
    except PasswordResetToken.DoesNotExist:
        raise NotFoundError("Токен сброса пароля не найден")


def get_user_task_stats(user: User) -> dict:
    from apps.tasks.models import Task

    return Task.objects.filter(assignee=user).aggregate(
        total_assigned=Count("id"),
        pending=Count("id", filter=Q(status=Task.Status.PENDING)),
        in_progress=Count("id", filter=Q(status=Task.Status.IN_PROGRESS)),
        completed=Count("id", filter=Q(status=Task.Status.COMPLETED)),
        high_priority=Count(
            "id", filter=Q(priority__in=[Task.Priority.HIGH, Task.Priority.URGENT])
        ),
        last_task_created=Max("created_at"),
    )
