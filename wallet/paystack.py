# wallet/paystack.py
import requests
from django.conf import settings


class Paystack:
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    def initialize_transaction(self, email, amount_naira, reference, callback_url):
        payload = {
            "email": email,
            "amount": int(amount_naira * 100),  # Paystack expects kobo
            "reference": reference,
            "callback_url": callback_url,
        }
        response = requests.post(
            f"{self.BASE_URL}/transaction/initialize",
            json=payload,
            headers=self.headers,
        )
        return response.json()

    def verify_transaction(self, reference):
        response = requests.get(
            f"{self.BASE_URL}/transaction/verify/{reference}",
            headers=self.headers,
        )
        return response.json()