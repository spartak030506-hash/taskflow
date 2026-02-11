from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from core.exceptions import ConflictError, NotFoundError, ValidationError

from . import selectors
from .models import EmailVerificationToken, PasswordResetToken, User
from .tasks import send_password_reset_email, send_verification_email


@transaction.atomic
def register_user(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> User:
    email = email.lower()

    if selectors.exists_email(email):
        raise ConflictError("Пользователь с таким email уже существует")

    try:
        validate_password(password)
    except DjangoValidationError as e:
        raise ValidationError("; ".join(e.messages))

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    EmailVerificationToken.create_for_user(user)

    transaction.on_commit(lambda: send_verification_email.delay(user.id))

    return user


@transaction.atomic
def verify_email(*, token: str) -> User:
    token_obj = selectors.get_verification_token(token)

    if token_obj.is_expired:
        raise ValidationError("Токен верификации истёк")

    user = token_obj.user

    if user.is_verified:
        raise ValidationError("Email уже подтверждён")

    user.is_verified = True
    user.save(update_fields=["is_verified"])

    token_obj.delete()

    return user


@transaction.atomic
def resend_verification_email(*, user: User) -> None:
    if user.is_verified:
        raise ValidationError("Email уже подтверждён")

    EmailVerificationToken.create_for_user(user)

    transaction.on_commit(lambda: send_verification_email.delay(user.id))


@transaction.atomic
def update_profile(
    *,
    user: User,
    first_name: str = None,
    last_name: str = None,
    phone: str = None,
    bio: str = None,
    avatar=None,
) -> User:
    update_fields = []

    if first_name is not None:
        user.first_name = first_name
        update_fields.append("first_name")

    if last_name is not None:
        user.last_name = last_name
        update_fields.append("last_name")

    if phone is not None:
        user.phone = phone
        update_fields.append("phone")

    if bio is not None:
        user.bio = bio
        update_fields.append("bio")

    if avatar is not None:
        user.avatar = avatar
        update_fields.append("avatar")

    if update_fields:
        user.save(update_fields=update_fields)

    return user


@transaction.atomic
def change_password(
    *,
    user: User,
    old_password: str,
    new_password: str,
) -> User:
    if not user.check_password(old_password):
        raise ValidationError("Неверный текущий пароль")

    try:
        validate_password(new_password, user)
    except DjangoValidationError as e:
        raise ValidationError("; ".join(e.messages))

    user.set_password(new_password)
    user.save(update_fields=["password"])

    return user


@transaction.atomic
def request_password_reset(*, email: str) -> None:
    email = email.lower()

    try:
        user = selectors.get_by_email(email)
    except NotFoundError:
        return

    if not user.is_active:
        return

    PasswordResetToken.create_for_user(user)

    transaction.on_commit(lambda: send_password_reset_email.delay(user.id))


@transaction.atomic
def reset_password(*, token: str, new_password: str) -> User:
    token_obj = selectors.get_password_reset_token(token)

    if not token_obj.is_valid:
        raise ValidationError("Токен недействителен или истёк")

    user = token_obj.user

    try:
        validate_password(new_password, user)
    except DjangoValidationError as e:
        raise ValidationError("; ".join(e.messages))

    user.set_password(new_password)
    user.save(update_fields=["password"])

    token_obj.is_used = True
    token_obj.save(update_fields=["is_used"])

    return user
