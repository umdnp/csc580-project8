"""Conservative redaction of source excerpts at reporting boundaries.

This is output hygiene, not a secret scanner: unrecognized secrets may remain.
Raw evidence is retained internally for accurate comparisons.
"""

from __future__ import annotations

import re


REDACTED = "[REDACTED]"
_SECRET_NAME = (
    r"(?:api[_-]?key|access[_-]?key|secret[_-]?key|private[_-]?key|"
    r"client[_-]?secret|access[_-]?token|refresh[_-]?token|auth[_-]?token|"
    r"id[_-]?token|session[_-]?token|session[_-]?id|token|password|passwd|secret|"
    r"x[_-]?api[_-]?key|credential)"
)
# Match a quoted value (including spaces) or an unquoted shell/URL value.
_VALUE = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s;,&)\]}'"`]+)'''
_PEM = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_BEARER = re.compile(r"(?i)(\b(?:Bearer|Basic)\s+)([A-Za-z0-9_~+./=-]+)")
_ASSIGNMENT = re.compile(
    rf"(?i)(\b{_SECRET_NAME}\b\s*[:=]\s*)(?!\[REDACTED\])({_VALUE})"
)
_FLAG = re.compile(
    rf"(?i)(?<!\w)(--?{_SECRET_NAME})(\s*=\s*|\s+)(?!\[REDACTED\])({_VALUE})"
)
_HEADER = re.compile(
    rf"(?i)(\b(?:Authorization|X-API-Key|X-Auth-Token|Cookie|Set-Cookie|Proxy-Authorization)\s*:\s*)"
    rf"(?!Bearer\b|Basic\b|\[REDACTED\])({_VALUE})"
)
_URL_QUERY = re.compile(
    rf"(?i)([?&;]{_SECRET_NAME}=)([^&#\s]+)"
)
_URL_USERINFO = re.compile(r"(https?://)([^/@\s]+)@", re.IGNORECASE)
_CURL_CREDENTIALS = re.compile(r"(?i)(?<!\w)(-u|--user)(\s+|=)([^\s]+)")
_KNOWN_TOKENS = re.compile(
    r"\b(?:AKIA[0-9A-Z]{16}|(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{8,}|"
    r"sk-[A-Za-z0-9_-]{12,})\b"
)


def redact_text(text: str) -> str:
    """Mask recognizable secret values without changing the source evidence."""

    if not text:
        return text
    text = _PEM.sub(REDACTED, text)
    text = _URL_USERINFO.sub(lambda m: f"{m[1]}{REDACTED}@", text)
    text = _URL_QUERY.sub(lambda m: f"{m[1]}{REDACTED}", text)
    text = _BEARER.sub(lambda m: f"{m[1]}{REDACTED}", text)
    text = _HEADER.sub(lambda m: f"{m[1]}{REDACTED}", text)
    text = _ASSIGNMENT.sub(lambda m: f"{m[1]}{REDACTED}", text)
    text = _FLAG.sub(lambda m: f"{m[1]}{m[2]}{REDACTED}", text)
    text = _CURL_CREDENTIALS.sub(lambda m: f"{m[1]}{m[2]}{REDACTED}", text)
    text = _KNOWN_TOKENS.sub(REDACTED, text)
    return text


def safe_excerpt(text: str, *, limit: int = 200) -> str:
    """Redact *before* truncation, avoiding partial credential disclosure."""

    safe = " ".join(redact_text(text).split())
    if len(safe) > limit:
        return safe[: limit - 3] + "..."
    return safe
