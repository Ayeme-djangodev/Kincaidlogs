
# Create your views here.
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from .models import Product, Category


def product_detail(request, pk):

    product = get_object_or_404(
        Product,
        pk=pk,
        status="available",
    )

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
        },
    )


def home(request):

    products = Product.objects.filter(
        status="available"
    )

    categories = Category.objects.all()

    search = request.GET.get("search")

    if search:
        products = products.filter(
            title__icontains=search
        )

    category_slug = request.GET.get("category")

    if category_slug:
        products = products.filter(
            category__slug=category_slug
        )

    platform = request.GET.get("platform")

    if platform:
        products = products.filter(
            platform__iexact=platform
        )

    max_price = request.GET.get("max_price")

    if max_price:
        try:
            max_price = float(max_price)
            products = products.filter(price__lte=max_price)
        except ValueError:
            pass

    context = {
        "products": products,
        "categories": categories,
    }

    return render(
        request,
        "products/home.html",
        context,
    )

def category_products(request, category_id):

    category = get_object_or_404(
        Category,
        id=category_id
    )

    products = Product.objects.filter(
        category=category,
        status="available"
    )

    return render(
        request,
        "products/category_products.html",
        {
            "category": category,
            "products": products,
        },
    )


def browse(request):

    products = Product.objects.filter(
        status="available"
    )

    categories = Category.objects.all()

    search = request.GET.get("search")

    if search:
        products = products.filter(
            title__icontains=search
        )

    category_slug = request.GET.get("category")

    if category_slug:
        products = products.filter(
            category__slug=category_slug
        )

    platform = request.GET.get("platform")

    if platform:
        products = products.filter(
            platform__iexact=platform
        )

    max_price = request.GET.get("max_price")

    if max_price:
        try:
            max_price = float(max_price)
            products = products.filter(price__lte=max_price)
        except ValueError:
            pass

    products = products.order_by("-id")

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "active_category": category_slug,
        "active_platform": platform,
    }

    return render(
        request,
        "products/browse.html",
        context,
    )