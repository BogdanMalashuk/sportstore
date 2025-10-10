from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    avatar = models.URLField(max_length=500, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.username
