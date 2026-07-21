from django.contrib import admin

from .models import Wallet, WalletTransaction


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ("reference", "amount", "status", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user",)
    inlines = [WalletTransactionInline]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "wallet", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "wallet__user__username")
    readonly_fields = ("wallet", "reference", "amount", "created_at")
    date_hierarchy = "created_at"
