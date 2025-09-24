from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    """Assign sensible defaults for the custom ``role`` field."""

    def _create_user(self, username, email, password, **extra_fields):
        if not extra_fields.get("role"):
            extra_fields["role"] = "admin" if extra_fields.get("is_superuser") else "user"
        return super()._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    role = models.CharField(max_length=50, blank=True, null=True)

    objects = UserManager()

    def __str__(self):
        return self.username
