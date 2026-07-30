import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TransactPayError(Exception):
    """Raised when TransactPay cannot be reached or returns an unusable response."""


class TransactPay:
    BASE_URL = "https://payment-api-service.transactpay.ai"
    TIMEOUT = 30

    def __init__(self):
        self.headers = {
            "api-key": settings.TRANSACTPAY_SECRET_KEY,
            "Content-Type": "application/json",
        }

    def verify_transaction(self, reference):
        """
        Verify a transaction directly with TransactPay.

        The wallet is NEVER credited from frontend callbacks.
        Every successful payment must be verified here first.

        Raises:
            TransactPayError: if the request fails, times out, or the
                response cannot be parsed as JSON.
        """
        try:
            response = requests.post(
                f"{self.BASE_URL}/payment/order/verify",
                json={"reference": reference},
                headers=self.headers,
                timeout=self.TIMEOUT,
            )
        except requests.Timeout as exc:
            logger.warning("TransactPay verify timed out. Ref=%s", reference)
            raise TransactPayError("Verification request timed out.") from exc
        except requests.RequestException as exc:
            logger.warning("TransactPay verify request failed. Ref=%s Error=%s", reference, exc)
            raise TransactPayError("Verification request failed.") from exc

        logger.info("Verify Status: %s", response.status_code)
        logger.info("Verify Response: %s", response.text)

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise TransactPayError(
                f"TransactPay returned HTTP {response.status_code}."
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            logger.warning("TransactPay returned non-JSON response. Ref=%s", reference)
            raise TransactPayError("Verification response was not valid JSON.") from exc
