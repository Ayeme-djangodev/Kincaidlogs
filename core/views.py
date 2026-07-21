from django.shortcuts import render
from products.models import Product


def home(request):

    products = Product.objects.filter(
        status="available"
    ).order_by("-created_at")[:8]

    return render(
        request,
        "core/home.html",
        {
            "products": products
        },
    )