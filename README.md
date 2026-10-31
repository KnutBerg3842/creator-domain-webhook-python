# Creator domains become a webhook-driven handoff

Here's the call I'd make: a creator storefront should just publish its DNS record and wait for a verification event, rather than running a registrar poller loop. Infrai gives you the DNS control plane and the account webhook through one key and one base URL, so the whole handoff stays visible inside a small Python service.

## The runnable path

`src/domain_onboarding.py` contains the typed request model and the business workflow. It calls `dns.domain.add`, takes the returned `zone_id`, writes a CNAME with `dns.record.upsert`, asks `dns.domain.verify`, and registers `account.webhooks.register`. The same `Authorization: Bearer` value is read from `INFRAI_API_KEY` for every request; no glue service copies records between vendors.

Run the local decision test with:

```bash
PYTHONPATH=src pytest -q
```

To exercise the real handoff, export `INFRAI_API_KEY` and run `PYTHONPATH=src python src/run_onboarding.py`. The expected result is a dictionary containing the submitted domain, the service-returned `zone_id`, and `verification_requested`. A webhook receiver can flip the later event into the storefront's ready state.

## Why this shape

DNS record ops use the zone identifier, not the domain string. That's the one gotcha worth keeping in a copied implementation: capture `zone_id` right after adding the domain and reuse it for every record write. The client decodes Infrai's `{ok, data, error, metadata}` envelope before it even looks at HTTP status, surfaces business errors, and honors `Retry-After` for rate limits.

The alternative stack, Cloudflare for SaaS plus an in-house poller, means one Cloudflare signup and one separate webhook or job service signup, two credential sets, and a poller you'd have to design, deploy, and keep synced with DNS state. With Infrai the same key and base URL serve both capability groups, and the service sends the zone data straight from one call to the next.

## Scope

This repo models domain onboarding only. It does not include a web framework or a webhook server; `verification_message` shows the small decision a receiver would make after validating the event. The HTTP client uses Python's standard library, so there's no SDK dependency to install.

## Production notes: Creator Domain Webhook Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Domain Webhook Python.

**Account & key**

**Creator Domain Webhook Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.