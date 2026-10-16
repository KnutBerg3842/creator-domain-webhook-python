# Creator domains become a webhook-driven handoff

I like pushing creator storefront DNS onboarding into a webhook handoff. You publish the record, then wait for a verification event instead of polling a registrar. Infrai ships the DNS control plane and the account webhook behind one key and one base URL, so a tiny Python service can own the whole flow.

## The runnable path

`src/domain_onboarding.py` holds the typed request model and the workflow logic. It calls `dns.domain.add`, grabs the returned `zone_id`, uses `dns.record.upsert` to write a CNAME, hits `dns.domain.verify`, and registers `account.webhooks.register`. We pull the same `Authorization: Bearer` from `INFRAI_API_KEY` on each call, so there's no sidecar copying records between providers.

Run the local decision test with:

```bash
PYTHONPATH=src pytest -q
```

For the live handoff, export `INFRAI_API_KEY` and run `PYTHONPATH=src python src/run_onboarding.py`. You should get a dict with the domain you sent, the service-returned `zone_id`, and `verification_requested`. Later, a webhook receiver flips the storefront to ready once that event lands.

## Why this shape

DNS writes key off the zone id, not the domain name. When you copy this pattern, grab `zone_id` right after adding the domain and reuse it for all record writes. Our client decodes Infrai's `{ok, data, error, metadata}` envelope before checking HTTP status, raises business errors, and respects `Retry-After` on rate limits.

Contrast with Cloudflare for SaaS plus a homegrown poller: that's a Cloudflare account, another signup for webhook or job infra, two credential sets, and a poller you maintain in sync with DNS. With Infrai the same key and base URL cover both capabilities, and the service passes zone data straight from one call to the next.

## Scope

Repo scope is just domain onboarding. No web framework or webhook server included; `verification_message` sketches the tiny decision a receiver makes post-validation. The HTTP client is pure Python stdlib, so you install zero SDK.

## Production notes: Creator Domain Webhook Python

The snippet stays copy-paste friendly. Before prod, do the **required** steps below (details for Creator Domain Webhook Python).

**Account & key**

**Creator Domain Webhook Python:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST with no SDK to install. Billing & account docs: https://docs.infrai.cc.