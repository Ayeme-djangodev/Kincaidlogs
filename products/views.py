
# Create your views here.
from django.db.models import Q
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

    categories = Category.objects.filter(parent__isnull=True)

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

    subcategories = category.subcategories.all()

    if subcategories.exists():
        return render(
            request,
            "products/category_products.html",
            {
                "category": category,
                "subcategories": subcategories,
                "products": None,
            },
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
            "subcategories": None,
            "products": products,
        },
    )


def browse(request):

    products = Product.objects.filter(
        status="available"
    )

    categories = Category.objects.filter(parent__isnull=True)

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

def search(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    products = Product.objects.filter(status="available")

    if query:
        products = products.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(platform__icontains=query)
            | Q(country__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    products = products.order_by("-created_at")

    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "query": query,
        "page_obj": page_obj,
        "categories": Category.objects.filter(parent__isnull=True),
        "selected_category": category_slug,
    }
    return render(request, "products/search_results.html", context)