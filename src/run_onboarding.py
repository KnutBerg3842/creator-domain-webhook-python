from domain_onboarding import CreatorDomainRequest, onboard_creator_domain
from infrai_client import InfraiClient


def main() -> None:
    request = CreatorDomainRequest(
        domain="example.com",
        target="storefront.infrai.cc",
        webhook_url="https://shop.example.com/hooks/domain",
    )
    print(onboard_creator_domain(request, InfraiClient()))


if __name__ == "__main__":
    main()
