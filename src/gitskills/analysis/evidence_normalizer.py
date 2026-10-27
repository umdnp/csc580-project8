"""Conservative, construct-specific comparison forms for static source evidence."""

from __future__ import annotations

import re

from .evidence_models import Evidence


_URL = re.compile(r"^(https?)://([^/?#]+)(.*)$", re.IGNORECASE | re.DOTALL)


def _normalize_url(url: str) -> str:
    """Fold URL scheme/host case without changing paths, queries or credentials."""

    match = _URL.fullmatch(url)
    if not match:
        return url
    scheme, authority, rest = match.groups()
    userinfo, sep, hostport = authority.rpartition("@")
    if not sep:
        hostport = authority
    if hostport.startswith("[") and "]" in hostport:
        close = hostport.index("]")
        hostport = hostport[:close + 1].lower() + hostport[close + 1:]
    else:
        host, colon, port = hostport.partition(":")
        hostport = host.lower() + (colon + port if colon else "")
    return f"{scheme.lower()}://{userinfo + sep if sep else ''}{hostport}{rest}"


def _normalize_spacing(source: str, *, call: bool = False) -> str:
    """Ignore unquoted layout differences without rewriting quoted arguments.

    For shell commands, a backslash-newline is a continuation; inside quotes
    it joins adjacent characters and outside quotes it separates tokens only
    when the source did so. API calls additionally ignore whitespace around
    common call delimiters.
    """

    pieces: list[tuple[str, bool]] = []
    quote: str | None = None
    position = 0
    while position < len(source):
        char = source[position]
        if char == "\\":
            match = re.match(r"\\\r?\n[ \t]*", source[position:])
            if match:
                # Shell continuation removes the newline; existing spaces
                # before/after it still determine token separation.
                position += match.end()
                continue
            if position + 1 < len(source):
                pieces.append((source[position:position + 2], True))
                position += 2
                continue
        if quote:
            pieces.append((char, True))
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
            pieces.append((char, True))
        else:
            pieces.append((char, False))
        position += 1

    output: list[str] = []
    pending_space = False
    for char, quoted in pieces:
        if not quoted and char.isspace():
            pending_space = bool(output)
            continue
        if pending_space:
            if not (call and (output[-1] in "(),=" or char in "(),=")):
                output.append(" ")
            pending_space = False
        output.append(char)
    return "".join(output)



class EvidenceNormalizer:
    """Normalize comparable constructs without altering the original evidence."""

    def normalize(self, evidence: Evidence) -> str:
        kind = evidence.kind
        raw = evidence.raw_text
        if kind == "shell_command":
            return _normalize_spacing(raw)
        if kind == "api_call":
            return _normalize_spacing(raw, call=True)
        if kind == "shell_code_block":
            language = dict(evidence.values).get("language", "")
            return f"shell_fence:{language.lower()}"
        if kind == "url_reference":
            return _normalize_url(raw.strip())
        if kind == "markdown_link":
            values = dict(evidence.values)
            destination = _normalize_url(values.get("destination", ""))
            label = values.get("label", "").strip()
            # Ordinary link-label wording is presentation, but a displayed URL
            # is itself relevant evidence when it differs from the destination.
            label_url = _normalize_url(label) if _URL.fullmatch(label) else ""
            return f"destination:{destination}\nlabel_url:{label_url}"
        return raw.strip()
