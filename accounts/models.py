from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    CUSTOMER = "customer"
    ADMIN = "admin"

    ROLE_CHOICES = [
        (CUSTOMER, "Customer"),
        (ADMIN, "Admin"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CUSTOMER,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.username