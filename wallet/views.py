import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Wallet, WalletTransaction
from .paystack import Paystack


@login_required
def fund_wallet(request):
    if request.method == "POST":
        amount = request.POST.get("amount")

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return render(request, "wallet/fund.html", {"error": "Enter a valid amount"})

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        reference = str(uuid.uuid4())

        WalletTransaction.objects.create(
            wallet=wallet,
            reference=reference,
            amount=amount,
            status="pending",
        )

        callback_url = request.build_absolute_uri(reverse("verify_payment"))

        paystack = Paystack()
        response = paystack.initialize_transaction(
            email=request.user.email,
            amount_naira=amount,
            reference=reference,
            callback_url=callback_url,
        )

        if response.get("status"):
            return redirect(response["data"]["authorization_url"])

        return render(request, "wallet/fund.html", {"error": "Could not initiate payment"})

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(request, "wallet/fund.html", {"wallet": wallet})


@login_required
def verify_payment(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")

    paystack = Paystack()
    result = paystack.verify_transaction(reference)

    if result.get("status") and result["data"]["status"] == "success":
        _credit_wallet_once(reference, result["data"]["amount"])
        return render(request, "wallet/success.html")

    return render(request, "wallet/failed.html")


@csrf_exempt
def paystack_webhook(request):
    secret = settings.PAYSTACK_SECRET_KEY.encode("utf-8")
    signature = request.headers.get("x-paystack-signature", "")

    computed_signature = hmac.new(secret, request.body, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed_signature, signature):
        return HttpResponse(status=401)

    event = json.loads(request.body)

    if event.get("event") == "charge.success":
        data = event["data"]
        _credit_wallet_once(data["reference"], data["amount"])

    return HttpResponse(status=200)


@login_required
def transaction_history(request):

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    transactions = wallet.transactions.all().order_by("-created_at")

    paginator = Paginator(transactions, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "wallet/transactions.html",
        {
            "wallet": wallet,
            "page_obj": page_obj,
            "transactions": page_obj,
        },
    )


def _credit_wallet_once(reference, amount_kobo):
    """Idempotent credit: only apply once, only if the amount matches."""
    with transaction.atomic():
        try:
            txn = WalletTransaction.objects.select_for_update().get(reference=reference)
        except WalletTransaction.DoesNotExist:
            return

        if txn.status == "success":
            return  # already credited, do nothing

        expected_kobo = int(txn.amount * 100)
        if amount_kobo != expected_kobo:
            txn.status = "failed"
            txn.save()
            return

        txn.status = "success"
        txn.save()

        wallet = txn.wallet
        wallet.balance += txn.amount
        wallet.save()
