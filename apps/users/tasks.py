from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import User, EmailVerificationToken, PasswordResetToken


@shared_task
def send_verification_email(user_id: int) -> None:
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    try:
        token_obj = EmailVerificationToken.objects.filter(user=user).latest('created_at')
    except EmailVerificationToken.DoesNotExist:
        return

    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token_obj.token}"

    subject = 'Подтверждение email - TaskFlow'
    message = f'''
Здравствуйте, {user.first_name}!

Для подтверждения email перейдите по ссылке:
{verification_url}

Ссылка действительна 24 часа.

Если вы не регистрировались на TaskFlow, просто проигнорируйте это письмо.

С уважением,
Команда TaskFlow
'''

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@shared_task
def send_password_reset_email(user_id: int) -> None:
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    try:
        token_obj = PasswordResetToken.objects.filter(
            user=user,
            is_used=False
        ).latest('created_at')
    except PasswordResetToken.DoesNotExist:
        return

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token_obj.token}"

    subject = 'Сброс пароля - TaskFlow'
    message = f'''
Здравствуйте, {user.first_name}!

Вы запросили сброс пароля. Для установки нового пароля перейдите по ссылке:
{reset_url}

Ссылка действительна 1 час.

Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.

С уважением,
Команда TaskFlow
'''

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
