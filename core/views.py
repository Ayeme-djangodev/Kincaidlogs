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


def about_us(request):
    return render(request, "core/about.html")


def privacy_policy(request):
    return render(request, "core/privacy.html")


def about_us(request):
    return render(request, "core/about.html")


def privacy_policy(request):
    return render(request, "core/privacy.html")
