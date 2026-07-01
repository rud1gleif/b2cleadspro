"""Email verification service.

Verification pipeline (in order of cost):
  1. Syntax check (regex)           — free, instant
  2. Disposable-domain check        — free, instant
  3. MX record lookup               — DNS, fast
  4. Reacher SMTP check (optional)  — self-hosted API, slow but accurate

Scoring:
  +40  syntax OK
  +20  not disposable
  +20  MX record found
  +20  Reacher SMTP confirmed deliverable
  -30  disposable
  -20  no MX record
  Clamped to [0, 100]
"""
import re
import socket
from typing import Optional
from loguru import logger
from app.services.disposable_service import is_disposable_domain

# Basic RFC-ish email regex
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    r"\.[a-zA-Z]{2,}$"
)


def _check_syntax(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def _check_mx(domain: str) -> bool:
    """Resolve MX record for domain. Falls back to A record."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(answers) > 0
    except Exception:
        pass
    # Fallback: try a basic socket connect
    try:
        socket.getaddrinfo(domain, 25, proto=socket.IPPROTO_TCP)
        return True
    except Exception:
        return False


def _check_reacher(email: str, reacher_url: str, api_key: Optional[str] = None) -> dict:
    """
    Call a self-hosted Reacher instance.
    Reacher API: POST /v0/check_email
    Docs: https://help.reacher.email/self-host-guide

    Returns dict with keys: is_reachable (str), smtp_error (str|None)
    """
    import httpx
    payload = {"to_email": email}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = httpx.post(
            f"{reacher_url.rstrip('/')}/v0/check_email",
            json=payload,
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "is_reachable": data.get("is_reachable", "unknown"),
                "smtp_error": str(data.get("smtp", {}).get("error") or ""),
            }
    except Exception as e:
        logger.debug(f"Reacher check failed for {email}: {e}")
    return {"is_reachable": "unknown", "smtp_error": None}


def verify_email(
    email: str,
    reacher_url: Optional[str] = None,
    reacher_api_key: Optional[str] = None,
    skip_smtp: bool = False,
) -> dict:
    """
    Full verification pipeline. Returns a dict with:
      - syntax_ok    (bool)
      - is_disposable (bool)
      - mx_ok        (bool)
      - smtp_ok      (bool | None)  — None if Reacher not used
      - is_reachable (str)          — 'safe'|'risky'|'invalid'|'unknown'
      - score        (int 0-100)
    """
    from app.config import settings

    result = {
        "syntax_ok": False,
        "is_disposable": False,
        "mx_ok": False,
        "smtp_ok": None,
        "is_reachable": "unknown",
        "score": 0,
    }

    email = email.strip().lower()

    # 1. Syntax
    if not _check_syntax(email):
        return result
    result["syntax_ok"] = True
    score = 40

    domain = email.split("@", 1)[1]

    # 2. Disposable check
    if is_disposable_domain(domain):
        result["is_disposable"] = True
        score -= 30
    else:
        score += 20

    # 3. MX check
    mx_ok = _check_mx(domain)
    result["mx_ok"] = mx_ok
    if mx_ok:
        score += 20
    else:
        score -= 20

    # 4. Reacher SMTP (optional)
    effective_reacher_url = reacher_url or getattr(settings, "reacher_url", None)
    effective_api_key = reacher_api_key or getattr(settings, "reacher_api_key", None)

    if effective_reacher_url and not skip_smtp and mx_ok and not result["is_disposable"]:
        reacher_result = _check_reacher(email, effective_reacher_url, effective_api_key)
        reachable = reacher_result["is_reachable"]
        result["is_reachable"] = reachable
        if reachable == "safe":
            result["smtp_ok"] = True
            score += 20
        elif reachable in ("risky", "unknown"):
            result["smtp_ok"] = None
        else:  # invalid
            result["smtp_ok"] = False
            score -= 15
    else:
        result["is_reachable"] = "safe" if (mx_ok and not result["is_disposable"]) else "unknown"

    result["score"] = max(0, min(100, score))
    return result


def batch_verify(emails: list[str], **kwargs) -> dict[str, dict]:
    """Verify a list of emails. Returns {email: verify_result}."""
    return {email: verify_email(email, **kwargs) for email in emails}
