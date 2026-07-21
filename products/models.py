from core.fields import EncryptedTextField
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):

    PLATFORM_CHOICES = [
        ("Instagram", "Instagram"),
        ("TikTok", "TikTok"),
        ("Facebook", "Facebook"),
        ("YouTube", "YouTube"),
        ("Twitter/X", "Twitter/X"),
        ("Website", "Website"),
        ("Domain", "Domain"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("sold", "Sold"),
    ]

    title = models.CharField(max_length=255)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,
    )

    followers = models.PositiveIntegerField(default=0)

    account_age = models.CharField(max_length=50)

    country = models.CharField(max_length=100)

    verified = models.BooleanField(default=False)

    monetized = models.BooleanField(default=False)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    description = models.TextField()

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
        db_index=True,
    )

    # --- Fulfillment: delivered to the buyer only after payment ---

    login_identifier = models.CharField(
        max_length=255,
        blank=True,
        help_text="The username, email, or handle used to log in to the account.",
    )

    login_password = EncryptedTextField(
        blank=True,
        help_text="Encrypted at rest. Only ever shown to the buyer after purchase.",
    )

    delivery_notes = models.TextField(
        blank=True,
        help_text="Optional extra info for the buyer: recovery email, 2FA backup codes, transfer instructions, etc.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    @property
    def is_available(self):
        return self.status == "available"
