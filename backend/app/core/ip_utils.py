"""
IP Utility Functions
Proxy-aware client IP extraction with CIDR trust validation.
"""
import ipaddress
from typing import Optional
from fastapi import Request


def is_trusted_proxy(ip_str: str, trusted_cidrs: list[str]) -> bool:
    """Return True if ip_str falls within any trusted CIDR range."""
    if not trusted_cidrs:
        return False
    try:
        ip = ipaddress.ip_address(ip_str)
        for cidr in trusted_cidrs:
            try:
                if ip in ipaddress.ip_network(cidr, strict=False):
                    return True
            except ValueError:
                continue
    except ValueError:
        pass
    return False


def get_real_client_ip(request: Request, trusted_cidrs: list[str]) -> str:
    """
    Extract real client IP.
    X-Forwarded-For is only trusted when the connecting IP is in trusted_cidrs.
    Takes the leftmost (client) IP from X-Forwarded-For.
    Falls back to request.client.host.
    Returns 'unknown' if nothing is available.
    """
    connecting_ip = request.client.host if request.client else None

    if connecting_ip and is_trusted_proxy(connecting_ip, trusted_cidrs):
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            real_ip = forwarded_for.split(",")[0].strip()
            if real_ip:
                return real_ip

    return connecting_ip or "unknown"
