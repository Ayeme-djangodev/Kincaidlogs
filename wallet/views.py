import json
import logging
import re
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Wallet, WalletTransaction
from .transactpay import TransactPay, TransactPayError

logger = logging.getLogger(__name__)

MIN_FUNDING_AMOUNT = Decimal("100")

# TransactPay's Standard Kit requires "mobile" and their sample payloads use
# E.164-style numbers with country code, e.g. "+2348134543421". A blank or
# locally-formatted number (e.g. "08012345678") is what triggers the
# "mobile number required" block on the checkout modal.
NG_MOBILE_RE = re.compile(r"^\+?\d{10,15}$")


def normalize_mobile(raw):
    """
    Best-effort normalization to +234XXXXXXXXXX.
    Returns None if we can't produce something TransactPay will accept.
    """
    if not raw:
        return None

    digits = re.sub(r"[^\d+]", "", raw)

    if digits.startswith("+"):
        cleaned = digits
    elif digits.startswith("0") and len(digits) == 11:
        # Local Nigerian format: 0801... -> +234801...
        cleaned = "+234" + digits[1:]
    elif digits.startswith("234"):
        cleaned = "+" + digits
    else:
        cleaned = "+" + digits if len(digits) >= 10 else digits

    return cleaned if NG_MOBILE_RE.match(cleaned) else None


@login_required
def fund_wallet(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "GET":
        return render(
            request,
            "wallet/fund.html",
            {
                "wallet": wallet,
                "transactpay_public_key": settings.TRANSACTPAY_PUBLIC_KEY,
                "transactpay_encryption_key": settings.TRANSACTPAY_ENCRYPTION_KEY,
            },
        )

    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)

    try:
        amount = Decimal(request.POST.get("amount"))

        if amount < MIN_FUNDING_AMOUNT:
            raise InvalidOperation

    except (TypeError, InvalidOperation):
        return JsonResponse(
            {
                "status": "error",
                "message": "Enter a valid amount.",
            },
            status=400,
        )

    # We don't collect a phone number from customers. TransactPay's Standard
    # Kit requires a non-empty, validly-formatted "mobile" field to proceed
    # past the modal's own client-side check, so we fall back to a business
    # number we own rather than asking the customer for one.
    mobile = normalize_mobile(getattr(request.user, "phone", "")) or getattr(
        settings, "TRANSACTPAY_FALLBACK_MOBILE", "+2348024113305"
    )

    reference = str(uuid.uuid4())

    while WalletTransaction.objects.filter(reference=reference).exists():
        reference = str(uuid.uuid4())

    WalletTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        reference=reference,
        status="pending",
    )

    full_name = (
        request.user.get_full_name().strip()
        or request.user.username
    )

    parts = full_name.split(" ", 1)

    return JsonResponse(
        {
            "status": "success",
            "reference": reference,
            "merchantReference": reference,
            "amount": float(amount),      # standard currency units (naira, 2dp)
            "currency": "NGN",
            "description": "Wallet Funding",

            "customer": {
                "firstName": parts[0],
                "lastName": parts[1] if len(parts) > 1 else "Customer",
                "email": request.user.email,
                "mobile": mobile,
                "country": "NG",
            },
        }
    )


@login_required
def verify_payment(request):
    # UNCONFIRMED: query param name TransactPay appends to your redirect
    # URL. Trying a few likely candidates defensively — check your actual
    # redirect URL in the browser address bar after a real test payment
    # and confirm which one actually shows up, then simplify this.
    reference = (
        request.GET.get("reference")
        or request.GET.get("orderReference")
        or request.GET.get("ref")
    )

    if not reference:
        return render(request, "wallet/failed.html")

    transactpay = TransactPay()

    try:
        result = transactpay.verify_transaction(reference)
    except TransactPayError:
        logger.warning("TransactPay verify failed. Ref=%s", reference)
        return render(request, "wallet/failed.html")

    logger.info("Verify response for ref=%s: %s", reference, result)

    # UNCONFIRMED: exact success-status field/value from their Verify
    # endpoint. Their webhook payloads use status == "Successful"
    # (capital S) — mirroring that assumption here.
    data = result.get("data", {})

    if (
        result.get("status") == "success"
        and result.get("statusCode") == "00"
        and data.get("status") == "Successful"
        and data.get("currencyName") == "NGN"
        and data.get("orderReference") == reference
    ):
        _credit_wallet_once(reference, data.get("totalAmountCharged"))

    txn = WalletTransaction.objects.filter(reference=reference).first()

    if txn and txn.status == "success":
        return render(request, "wallet/success.html")

    return render(request, "wallet/failed.html")


@csrf_exempt
def transactpay_webhook(request):
    """
    TransactPay's webhook has NO signature verification available at all
    (confirmed from their docs) — meaning this endpoint cannot cryptographically
    confirm a request actually came from TransactPay. We treat it purely as
    a trigger: re-verify server-side via the authenticated API before
    crediting anything. Never trust this payload's amount/status directly.
    """
    try:
        event = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse(status=400)

    data = event.get("data", {})
    reference = data.get("orderReference") or data.get("paymentReference")

    if not reference:
        return HttpResponse(status=400)

    transactpay = TransactPay()

    try:
        result = transactpay.verify_transaction(reference)
    except TransactPayError:
        logger.warning("TransactPay webhook verify failed. Ref=%s", reference)
        return HttpResponse(status=200)

    verified_data = result.get("data", {})

    if (
        result.get("status") == "success"
        and result.get("statusCode") == "00"
        and verified_data.get("status") == "Successful"
        and verified_data.get("currencyName") == "NGN"
        and verified_data.get("orderReference") == reference
    ):
        _credit_wallet_once(reference, verified_data.get("totalAmountCharged"))

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


def _credit_wallet_once(reference, amount_naira):
    """
    Idempotent credit: only apply once, only if the amount matches.
    TransactPay's Verify API returns amount in standard currency units
    (naira, 2dp) - not kobo - so it's compared directly here using
    Decimal to avoid floating-point precision issues.
    """
    with transaction.atomic():
        try:
            txn = WalletTransaction.objects.select_for_update().get(reference=reference)
        except WalletTransaction.DoesNotExist:
            logger.warning("Credit attempted for unknown reference=%s", reference)
            return

        if txn.status == "success":
            return  # already credited, do nothing

        if amount_naira is None:
            txn.status = "failed"
            txn.save(update_fields=["status"])
            return

        verified_amount = Decimal(str(amount_naira))

        if verified_amount != txn.amount:
            logger.warning(
                "Wallet amount mismatch. Ref=%s Stored=%s Verified=%s",
                reference,
                txn.amount,
                verified_amount,
            )
            txn.status = "failed"
            txn.save(update_fields=["status"])
            return

        txn.status = "success"
        txn.save(update_fields=["status"])

        wallet = txn.wallet
        Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + txn.amount)
