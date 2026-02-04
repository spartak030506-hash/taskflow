import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User, EmailVerificationToken, PasswordResetToken


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_verified = False
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or 'TestPass123!'
        self.set_password(password)
        if create:
            self.save(update_fields=['password'])


class EmailVerificationTokenFactory(DjangoModelFactory):
    class Meta:
        model = EmailVerificationToken

    user = factory.SubFactory(UserFactory)
    token = factory.LazyFunction(lambda: __import__('secrets').token_urlsafe(48))
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=24))


class PasswordResetTokenFactory(DjangoModelFactory):
    class Meta:
        model = PasswordResetToken

    user = factory.SubFactory(UserFactory)
    token = factory.LazyFunction(lambda: __import__('secrets').token_urlsafe(48))
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    is_used = False
