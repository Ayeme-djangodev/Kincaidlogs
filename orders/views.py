from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.views import *
from products.models import Product
from wallet.models import Wallet

from .models import Order, OrderItem
from .emails import send_order_confirmation_email


@login_required
def checkout(request):

    cart = request.session.get("cart", {})

    items = []

    total = Decimal("0.00")

    for product_id, quantity in cart.items():

        product = Product.objects.get(id=product_id)

        subtotal = product.price * quantity

        total += subtotal

        items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    if request.method == "POST":

        if not items:
            return render(
                request,
                "orders/checkout.html",
                {
                    "items": items,
                    "total": total,
                    "error": "Your cart is empty.",
                },
            )

        with transaction.atomic():

            Wallet.objects.get_or_create(user=request.user)
            wallet = Wallet.objects.select_for_update().get(user=request.user)

            product_ids = [item["product"].id for item in items]

            locked_products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            unavailable = [
                product for product in locked_products.values()
                if product.status != "available"
            ]

            if unavailable:

                unavailable_ids = {product.id for product in unavailable}

                request.session["cart"] = {
                    pid: qty for pid, qty in cart.items()
                    if int(pid) not in unavailable_ids
                }

                names = ", ".join(product.title for product in unavailable)

                return render(
                    request,
                    "orders/checkout.html",
                    {
                        "items": items,
                        "total": total,
                        "wallet": wallet,
                        "error": f"Sorry, someone just bought: {names}. It's been removed from your cart — please review and try again.",
                    },
                )

            # Recompute total from the locked rows, not the earlier snapshot,
            # in case a price changed between page load and checkout.
            total = sum(
                locked_products[item["product"].id].price * item["quantity"]
                for item in items
            )

            if wallet.balance < total:
                return render(
                    request,
                    "orders/checkout.html",
                    {
                        "items": items,
                        "total": total,
                        "wallet": wallet,
                        "error": "Insufficient wallet balance. Please fund your wallet to continue.",
                    },
                )

            wallet.balance -= total
            wallet.save()

            order = Order.objects.create(
                customer=request.user,
                full_name=request.POST.get("full_name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                total=total,
                status="paid",
            )

            for item in items:

                product = locked_products[item["product"].id]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    unit_price=product.price,
                )

                product.status = "sold"
                product.save()

        request.session["cart"] = {}

        send_order_confirmation_email(order)

        return redirect("order_success")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(
        request,
        "orders/checkout.html",
        {
            "items": items,
            "total": total,
            "wallet": wallet,
        },
    )


@login_required
def order_success(request):
    return render(
        request,
        "orders/success.html"
    )


@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        customer=request.user,
    )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
        },
    )