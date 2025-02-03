from django.contrib.auth.models import AbstractUser
from django.db import models

from .users_constants import (MAX_EMAIL_LENGTH, MAX_NAME_LENGTH,
                              MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH)
from .validators import validate_username


class User(AbstractUser):
    email = models.EmailField(
        'E-mail address',
        unique=True,
        blank=False,
        max_length=MAX_EMAIL_LENGTH,
    )

    username = models.CharField(
        'Username',
        unique=True,
        blank=False,
        max_length=MAX_USERNAME_LENGTH,
        validators=[validate_username]
    )

    first_name = models.CharField(
        'First name',
        max_length=MAX_NAME_LENGTH,
        blank=False,
    )

    last_name = models.CharField(
        'Last name',
        max_length=MAX_NAME_LENGTH,
        blank=False,
    )

    password = models.CharField(
        'Password',
        blank=False,
        max_length=MAX_PASSWORD_LENGTH,
    )

    is_subscribed = models.BooleanField(
        'Is subscribed',
        default=False,
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)

    def get_username(self):
        return self.email


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribed_users'
    )

    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription')
        ]
