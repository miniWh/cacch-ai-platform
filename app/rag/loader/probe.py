"""Link probe helper for source sites."""

from urllib.parse import urlparse

import httpx

from app.common.timeutil import now_app
from app.dao.models.source_site import SourceSite
from app.web.config import Settings


def _host_allowed(hostname: str, allowed_domains: list[str]) -> bool:
    host = hostname.lower().rstrip(".")
    for domain in allowed_domains:
        d = domain.lower().lstrip(".")
        if host == d or host.endswith(f".{d}"):
            return True
    return False


def probe_site(site: SourceSite, settings: Settings) -> tuple[str, str]:
    """
    Probe entry_url.

    Returns (site_status, probe_status_label).
    """
    now_status = site.status
    if not site.entry_url:
        return "pending_url", "skip"

    parsed = urlparse(site.entry_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "broken", "invalid_url"

    domains = [str(d) for d in (site.allowed_domains or [])]
    if domains and not _host_allowed(parsed.hostname, domains):
        return "broken", "domain_denied"

    try:
        with httpx.Client(
            timeout=settings.probe_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = client.head(site.entry_url)
            if response.status_code >= 400 or response.status_code == 405:
                response = client.get(site.entry_url)
        code = str(response.status_code)
        if 200 <= response.status_code < 400:
            # keep disabled if operator disabled; otherwise active
            if now_status == "disabled":
                return "disabled", code
            return "active", code
        return "broken", code
    except httpx.HTTPError as exc:
        return "broken", f"error:{exc.__class__.__name__}"


def apply_probe_result(
    site: SourceSite, site_status: str, probe_status: str
) -> SourceSite:
    site.status = site_status
    site.last_probe_status = probe_status
    site.last_probe_at = now_app()
    return site
