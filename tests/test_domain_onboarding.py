import hashlib
import hmac

from domain_onboarding import CreatorDomainRequest, onboard_creator_domain, verify_webhook


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, body=None, query=None):
        self.calls.append((method, path, body, query))
        if path == "/v1/dns/domain/add":
            return {"ok": True, "data": {"zone_id": "zone_123"}}
        return {"ok": True, "data": {}}


def test_onboarding_writes_records_with_returned_zone_and_subscribes():
    fake = FakeClient()
    result = onboard_creator_domain(CreatorDomainRequest("alice.test", "store.infrai.cc", "https://alice.test/hook"), fake)
    assert result["zone_id"] == "zone_123"
    assert fake.calls[1][2]["zone_id"] == "zone_123"
    assert [call[1] for call in fake.calls] == [
        "/v1/dns/domain/add", "/v1/dns/record/upsert", "/v1/dns/domain/verify", "/v1/account/webhooks/register"
    ]
    payload = b'{"domain":"alice.test"}'
    signature = hmac.new(b"local-example-secret", payload, hashlib.sha256).hexdigest()
    assert verify_webhook(payload, signature, "local-example-secret")
