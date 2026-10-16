from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from typing import Any

from infrai_client import InfraiClient


@dataclass(frozen=True)
class CreatorDomainRequest:
    domain: str
    target: str
    webhook_url: str
    webhook_secret: str = "local-example-secret"


def onboard_creator_domain(request: CreatorDomainRequest, client: InfraiClient) -> dict[str, Any]:
    """Register a zone, publish its CNAME, and subscribe to verification events."""
    zone = client.request("POST", "/v1/dns/domain/add", body={"domain": request.domain})
    zone_id = zone["data"]["zone_id"]
    client.request("PUT", "/v1/dns/record/upsert", body={
        "zone_id": zone_id, "record_type": "CNAME", "name": "@",
        "content": request.target, "ttl": 300, "metadata": {"purpose": "creator storefront"},
    })
    client.request("POST", "/v1/dns/domain/verify", body={"domain": request.domain})
    client.request("POST", "/v1/account/webhooks/register", body={
        "url": request.webhook_url, "events": ["dns.domain.verified"],
        "description": "Notify the storefront when its domain is verified",
        "secret": request.webhook_secret,
    })
    return {"domain": request.domain, "zone_id": zone_id, "status": "verification_requested"}


def verification_message(payload: dict[str, Any]) -> str:
    return f"{payload['domain']} is ready for creator traffic"


def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
