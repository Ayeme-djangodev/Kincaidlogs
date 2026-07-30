from django.urls import path
from . import views

urlpatterns = [
    path("fund/", views.fund_wallet, name="fund_wallet"),
    path("verify/", views.verify_payment, name="verify_payment"),
    path("webhook/", views.transactpay_webhook, name="transactpay_webhook"),
    path("transactions/", views.transaction_history, name="wallet_transactions"),
]