#!/usr/bin/env python3
"""Shared anonymization for docs captures (T-220).

Policy (see captures/README.md):
- IPv4 addresses outside the RFC 5737 test ranges / loopback are mapped
  deterministically to 192.0.2.1..N (first-appearance order, stable across
  re-captures of the same input set).
- Relay tokens (rt_/rs_/adm_/... full form) are cut to their ellipsis form.
- Own domains (rpon.eu and subdomains) become example.com.
- Node ids (short uppercase codes) are NOT credentials and stay readable.
"""

import re

IPV4_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
# Real tokens carry entropy; suffix must contain a digit. This keeps config
# key names (rt_refresh_interval_seconds) and placeholder shapes (adm_xxx…)
# out of the match.
TOKEN_RE = re.compile(r"\b((?:rt|rs|adm)_[A-Za-z0-9_-]{6,})\b")


def _has_digit_suffix(m: "re.Match[str]") -> bool:
    return any(c.isdigit() for c in m.group(1)[4:])
DOMAIN_RE = re.compile(r"\b([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.rpon\.eu)\b")

ALLOWED_IP_PREFIXES = (
    "192.0.2.",
    "198.51.100.",
    "203.0.113.",
    "127.",
    "0.0.0.0",
)


def is_public_or_private(ip: str) -> bool:
    """True if the IP is NOT already a documentation-safe address."""
    return not ip.startswith(ALLOWED_IP_PREFIXES)


def anonymize_text(text: str) -> str:
    """Map unsafe IPs deterministically, redact tokens, swap own domains."""
    ip_map: dict[str, str] = {}

    def map_ip(m: re.Match[str]) -> str:
        ip = m.group(1)
        if not is_public_or_private(ip):
            return ip
        if ip not in ip_map:
            ip_map[ip] = f"192.0.2.{len(ip_map) + 1}"
        return ip_map[ip]

    text = DOMAIN_RE.sub("example.com", text)
    text = TOKEN_RE.sub(
        lambda m: (
            m.group(1)[: m.group(1).index("_") + 1] + "…"
            if _has_digit_suffix(m)
            else m.group(1)
        ),
        text,
    )
    text = IPV4_RE.sub(map_ip, text)
    return text