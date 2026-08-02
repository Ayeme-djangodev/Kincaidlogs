from django.urls import path
from . import views

urlpatterns = [
    path("browse/", views.browse, name="browse_products"),
    path("category/<int:category_id>/", views.category_products, name="category_products",),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("search/", views.search, name="search"),
]
