"""Request protection helpers."""
import hmac
import secrets

# A new random token is created every time the server starts.
# It is placed inside the page's form and must come back with the POST.
# A malicious website cannot read it, so it cannot forge a valid request.
CSRF_TOKEN = secrets.token_urlsafe(32)


def csrf_valid(submitted: str) -> bool:
    return hmac.compare_digest(submitted or "", CSRF_TOKEN)
