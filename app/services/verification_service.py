"""Email verification: syntax, MX, disposable check."""
import re
import socket
from typing import Tuple
from functools import lru_cache

EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

# Common disposable email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "sharklasers.com", "guerrillamailblock.com", "grr.la",
    "guerrillamail.info", "spam4.me", "trashmail.com", "dispostable.com",
    "maildrop.cc", "getnada.com", "fakeinbox.com", "tempr.email",
    "discard.email", "spamgourmet.com", "mailnull.com", "spamgourmet.org",
    "10minutemail.com", "minutemailbox.com", "mintemail.com",
}

ROLE_PREFIXES = {
    "admin", "info", "support", "sales", "noreply", "no-reply",
    "webmaster", "postmaster", "contact", "hello", "team",
    "office", "abuse", "security", "billing", "help",
}


def check_syntax(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


@lru_cache(maxsize=2048)
def check_mx(domain: str) -> bool:
    try:
        import dns.resolver
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        # Fallback: basic socket-level domain check
        try:
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False


def is_disposable(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return domain in DISPOSABLE_DOMAINS


def is_role_account(email: str) -> bool:
    local = email.split("@")[0].lower()
    return local in ROLE_PREFIXES


def compute_score(syntax_ok: bool, mx_ok: bool, disposable: bool, role: bool) -> int:
    score = 0
    if syntax_ok:
        score += 30
    if mx_ok:
        score += 40
    if not disposable:
        score += 20
    if not role:
        score += 10
    return score


def verify_email(email: str) -> dict:
    syntax_ok = check_syntax(email)
    domain = email.split("@")[-1]
    mx_ok = check_mx(domain) if syntax_ok else False
    disposable = is_disposable(email)
    role = is_role_account(email)
    score = compute_score(syntax_ok, mx_ok, disposable, role)
    return {
        "syntax_ok": syntax_ok,
        "mx_ok": mx_ok,
        "smtp_ok": None,  # SMTP check requires Reacher/self-hosted service
        "is_disposable": disposable,
        "is_role_account": role,
        "score": score,
    }
