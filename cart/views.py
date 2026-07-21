from django.contrib import messages
from django.shortcuts import redirect, render

from products.models import Product


def add_to_cart(request, product_id):

    product = Product.objects.filter(id=product_id).first()

    if product is None or product.status != "available":
        messages.error(request, "That account is no longer available.")
        return redirect("cart")

    cart = request.session.get("cart", {})

    # Each product is a single, unique account — not restockable stock —
    # so quantity is always exactly 1, never incremented.
    cart[str(product_id)] = 1

    request.session["cart"] = cart

    return redirect("cart")


def remove_from_cart(request, product_id):

    cart = request.session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session["cart"] = cart

    return redirect("cart")


def cart_detail(request):

    cart = request.session.get("cart", {})

    items = []

    total = 0

    removed_titles = []

    for product_id, quantity in list(cart.items()):

        product = Product.objects.filter(id=product_id).first()

        # Product was deleted, or sold since it was added to the cart.
        if product is None or product.status != "available":
            removed_titles.append(product.title if product else f"#{product_id}")
            del cart[product_id]
            continue

        subtotal = product.price * quantity

        total += subtotal

        items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    if removed_titles:
        request.session["cart"] = cart
        messages.warning(
            request,
            f"Removed from your cart (no longer available): {', '.join(removed_titles)}",
        )

    return render(
        request,
        "cart/cart.html",
        {
            "items": items,
            "total": total,
        },
    )
