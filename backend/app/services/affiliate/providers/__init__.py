"""
Affiliate Network Providers
"""
from app.services.affiliate.providers.ebay_provider import EbayAffiliateProvider
from app.services.affiliate.providers.amazon_provider import (
    AmazonAffiliateProvider,
    generate_amazon_affiliate_link,
    AMAZON_DOMAINS,
)

__all__ = [
    "EbayAffiliateProvider",
    "AmazonAffiliateProvider",
    "generate_amazon_affiliate_link",
    "AMAZON_DOMAINS",
]
