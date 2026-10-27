import base64
import json
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from seminare.users.models import PushSubscription

logger = logging.getLogger(__name__)


def generate_vapid_keys() -> tuple[str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    private_raw = key.private_numbers().private_value.to_bytes(32, "big")
    private_key = base64.urlsafe_b64encode(private_raw).rstrip(b"=").decode()
    raw_public = key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_key = base64.urlsafe_b64encode(raw_public).rstrip(b"=").decode()
    logger.info("Generated VAPID keys: %s, %s", public_key, private_key)
    return public_key, private_key


def get_vapid_keys() -> tuple[str, str]:
    public = settings.VAPID_PUBLIC_KEY
    private = settings.VAPID_PRIVATE_KEY
    if public and private:
        return public, private

    if not settings.DEBUG:
        return "", ""

    public, private = generate_vapid_keys()
    return public, private


def _signing_key(private: str):
    if "BEGIN" not in private:
        return private

    from py_vapid import Vapid

    return Vapid.from_pem(private.encode())


def send_web_push(subscription: PushSubscription, payload: dict) -> None:
    from pywebpush import WebPushException, webpush

    _public, private = get_vapid_keys()
    if not private:
        raise ImproperlyConfigured("Web push is not configured")

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=json.dumps(payload),
            vapid_private_key=_signing_key(private),
            vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            ttl=60 * 60 * 24,
        )
    except WebPushException as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in (404, 410):
            subscription.delete()
            return
        logger.warning("Web push failed for %s: %s", subscription.endpoint, exc)
