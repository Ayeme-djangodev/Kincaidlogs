from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_order_confirmation_email(order):
    """
    Sends a plain-text order confirmation to the buyer.
    Uses whatever EMAIL_BACKEND is configured in settings —
    console backend in dev, real SMTP/provider in production.
    """

    subject = f"KincaidLogs — Order Confirmed (LOG-{order.id:04d})"

    message = render_to_string(
        "orders/email/order_confirmation.txt",
        {"order": order},
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[order.email],
        fail_silently=True,
    )
