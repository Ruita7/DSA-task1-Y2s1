"""Safaricom Daraja 3.0 M-Pesa Express (STK Push) integration.

Credentials are read from environment variables and are never stored in Git.
The integration is intended for Daraja sandbox testing until production
credentials and a production HTTPS callback are configured.
"""

import base64
import os
from datetime import datetime

import requests


class MpesaError(Exception):
    """Raised when a Daraja request cannot be completed."""


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise MpesaError(f"Missing M-Pesa configuration: {name}")
    return value


def base_url() -> str:
    return os.getenv(
        "MPESA_BASE_URL",
        "https://sandbox.safaricom.co.ke",
    ).rstrip("/")


def get_access_token() -> str:
    consumer_key = _required("MPESA_CONSUMER_KEY")
    consumer_secret = _required("MPESA_CONSUMER_SECRET")

    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode("utf-8")
    ).decode("utf-8")

    response = requests.get(
        f"{base_url()}/oauth/v1/generate",
        params={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {credentials}"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    token = data.get("access_token")
    if not token:
        raise MpesaError("Daraja did not return an access token.")
    return token


def _password_and_timestamp():
    shortcode = _required("MPESA_SHORTCODE")
    passkey = _required("MPESA_PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{shortcode}{passkey}{timestamp}".encode("utf-8")
    password = base64.b64encode(raw).decode("utf-8")
    return password, timestamp


def initiate_stk_push(phone_number: str, amount: float, account_reference: str):
    """Ask Daraja to send an M-Pesa payment prompt to the customer."""
    phone = phone_number.strip().replace("+", "")
    if phone.startswith("07"):
        phone = "254" + phone[1:]
    if not (phone.isdigit() and phone.startswith("254") and len(phone) == 12):
        raise MpesaError("Phone number must be in 2547XXXXXXXX format.")

    amount = max(1, int(round(float(amount))))
    token = get_access_token()
    password, timestamp = _password_and_timestamp()
    shortcode = _required("MPESA_SHORTCODE")
    callback_url = _required("MPESA_CALLBACK_URL")

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": os.getenv(
            "MPESA_TRANSACTION_TYPE", "CustomerPayBillOnline"
        ),
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": "Parking payment",
    }

    response = requests.post(
        f"{base_url()}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("ResponseCode") != "0":
        raise MpesaError(data.get("ResponseDescription", "STK Push failed."))

    return data
