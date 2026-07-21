from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.order_success, name="order_success"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
]