from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "platform",
        "category",
        "price",
        "status",
        "verified",
        "created_at",
    )

    list_filter = ("status", "platform", "category", "verified", "monetized")

    list_editable = ("status", "price")

    search_fields = ("title", "description")

    readonly_fields = ("created_at",)

    fieldsets = (
        ("Listing Info", {
            "fields": ("title", "category", "platform", "description", "image")
        }),
        ("Account Details", {
            "fields": ("followers", "account_age", "country", "verified", "monetized")
        }),
        ("Pricing & Status", {
            "fields": ("price", "status")
        }),
        ("Fulfillment (shown to buyer after payment)", {
            "fields": ("login_identifier", "login_password", "delivery_notes"),
            "description": "login_password is encrypted at rest, but is displayed here in "
                            "plain text since admin users are trusted. Handle with care.",
        }),
        ("Metadata", {
            "fields": ("created_at",)
        }),
    )
