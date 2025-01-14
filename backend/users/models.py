from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username


class User(AbstractUser):
    email = models.EmailField(
        'E-mail address',
        unique=True,
        blank=False,
        max_length=256,
    )
    username = models.CharField(
        'Username',
        unique=True,
        blank=False,
        max_length=150,
        validators=[validate_username]
    )
    first_name = models.CharField(
        'first name',
        max_length=150,
        blank=False,
    )
    last_name = models.CharField(
        'last name',
        max_length=150,
        blank=False,
    )
    password = models.CharField(
        'password',
        blank=False,
        max_length=150,
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribed_users')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'], name='unique_subscription')
        ]
