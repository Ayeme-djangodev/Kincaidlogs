from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from orders.models import Order
from wallet.models import Wallet

from .forms import RegisterForm


def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


def register(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(request, "Welcome to KincaidLogs!")

            return redirect("dashboard")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


@login_required
def dashboard(request):

    order_count = Order.objects.filter(customer=request.user).count()

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "order_count": order_count,
            "wallet": wallet,
        },
    )


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        customer=request.user
    ).prefetch_related("items__product")

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "accounts/my_orders.html",
        {
            "orders": page_obj,
            "page_obj": page_obj,
        },
    )