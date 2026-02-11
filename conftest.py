import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    from apps.users.tests.factories import UserFactory

    return UserFactory(is_verified=True)


@pytest.fixture
def verified_user(db):
    from apps.users.tests.factories import UserFactory

    return UserFactory(is_verified=True)


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
