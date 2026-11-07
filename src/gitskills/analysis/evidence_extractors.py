"""Small source-construct extractors; no rule evaluation or code execution."""

from __future__ import annotations

import posixpath
import re
import shlex
from dataclasses import dataclass

from .evidence_models import ExtractionStatus


@dataclass(frozen=True, slots=True)
class SourceSpan:
    kind: str
    start: int
    end: int
    status: ExtractionStatus = ExtractionStatus.COMPLETE
    values: tuple[tuple[str, str], ...] = ()


_URL = re.compile(r"https?://[^\s<>()\"']+", re.IGNORECASE)
_API = re.compile(r"(?:\b(?:requests|httpx|axios|fs(?:\.promises)?)\.[\w]+|"
                  r"\b(?:fetch|axios|open)|\.[\w]+)\s*\(")
_COMMAND = re.compile(
    r"(?<![\w.-])(?:\./(?:[\w.-]+/)*[\w.-]+\.(?:sh|bash|py|js|mjs|ps1)|"
    r"sudo|su|exec|curl|wget|python(?:\d+(?:\.\d+)*)?|bash|sh|zsh|fish|"
    r"node|bun|uvx?|npm|npx|pnpm|yarn|pip\d*|docker|pwsh|powershell|cmd\.exe|"
    r"rm|mv|cp|mkdir|touch|cat|less|more|chmod|chown|setfacl|systemctl|"
    r"service|crontab|apt(?:-get)?|dnf|yum|brew|"
    r"Invoke-WebRequest|Invoke-RestMethod|Remove-Item|Move-Item|Copy-Item|"
    r"Set-Content|Add-Content|Get-Content)\b",
    re.IGNORECASE,
)
_MARKDOWN_LINK = re.compile(r"\[([^\]\n]*)\]\((https?://[^\s)]+)\)", re.IGNORECASE)

# Explicit Markdown statements linking an action to this URL are stronger
# evidence than an ordinary URL reference. Never infer command internals.
_DESCRIBED_DOWNLOAD = re.compile(
    r"\b(?:download(?:s|ed|ing)?|fetch(?:es|ed|ing)?|retrieve(?:s|d|ing)?)\b"
    r"(?:\s+[^.!?;\n]{0,140}?)?\s+\b(?:from|at|via)\s*$", re.I,
)
_DESCRIBED_OUTBOUND = re.compile(
    r"\b(?:upload(?:s|ed|ing)?|send(?:s|ing)?|post(?:s|ed|ing)?|transmit(?:s|ted|ting)?)\b"
    r"(?:\s+[^.!?;\n]{0,140}?)?\s+\bto\s*$", re.I,
)
_TABLE_TRANSFER = re.compile(
    r"^(?P<verb>downloads?|fetch(?:es)?|retrieves?|uploads?|sends?|posts?|transmits?)\s+"
    r"(?!(?:url|link|page|docs?|documentation)\b)\S.{1,120}$", re.I,
)
_TRANSFER_WARNING = re.compile(
    r"\b(?:never|(?:do|does|did|will|must|should)\s+not|don't|doesn't|"
    r"won't|shouldn't|can't|cannot|avoid)\b", re.I,
)
_TRANSFER_REFERENCE = re.compile(
    r"\b(?:download|downloads|upload|uploads|fetch)\s+"
    r"(?:url|link|page|site|instructions?|docs?|documentation|endpoint)\b|"
    r"\b(?:how\s+to|instructions\s+(?:for|to)|example\s+of)\s+"
    r"(?:\w+\s+){0,3}(?:download|fetch|retrieve|upload|send)\b", re.I,
)


def described_network_operation(text: str, start: int) -> str | None:
    """Recognize a transfer explicitly attached to a URL on the same line."""
    left = text.rfind("\n", 0, start) + 1
    prefix = text[left:start].rstrip(" `\t")
    if _TRANSFER_WARNING.search(prefix) or _TRANSFER_REFERENCE.search(prefix):
        return None

    # Markdown tables often use an operation in one cell and its destination
    # in the adjacent cell: | Downloads template ZIP | `https://...` |
    if "|" in prefix:
        # A trailing separator precedes the URL cell; look at the immediately
        # preceding (operation) cell, never a different table column.
        before_url = prefix[:-1] if prefix.endswith("|") else prefix
        cell = before_url.rsplit("|", 1)[-1].strip()
        match = _TABLE_TRANSFER.fullmatch(cell)
        if match:
            return "outbound" if match.group("verb").lower().startswith(
                ("upload", "send", "post", "transmit")
            ) else "download"
        return None

    # Require a clear verb and destination preposition, rather than merely
    # "Download URL", "download link", or "see this download page".
    if _DESCRIBED_DOWNLOAD.search(prefix):
        return "download"
    if _DESCRIBED_OUTBOUND.search(prefix):
        return "outbound"
    return None


_REDIRECT = re.compile(r"(?:[0-9]?>/dev/null|[0-9]?>&[0-9])$")


def _and_steps(line: str) -> list[str] | None:
    """Split an explicit single-line && chain without crossing quoted text."""
    if "\n" in line or "\r" in line:
        return None
    parts: list[str] = []
    quote: str | None = None
    escaped = False
    beginning = 0
    i = 0
    while i < len(line):
        char = line[i]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif line[i:i + 2] == "&&":
            parts.append(line[beginning:i].strip())
            i += 1
            beginning = i + 1
        elif char in ";|":
            return None
        i += 1
    if quote or escaped:
        return None
    parts.append(line[beginning:].strip())
    return parts if len(parts) in (2, 3) and all(parts) else None


def _tokens(command: str) -> list[str] | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    # Ignore only simple output suppression, never arbitrary shell syntax.
    while tokens and _REDIRECT.fullmatch(tokens[-1]):
        tokens.pop()
    return tokens


def _literal_path(path: str) -> str | None:
    if (not path or path == "-" or re.search(r"[\s$*?`{}()<>|;&]", path)
            or path.startswith("-")):
        return None
    return posixpath.normpath(path)


def staged_download_execution(line: str) -> bool:
    """Recognize a literal download followed by execution of that same file."""
    parts = _and_steps(line)
    if not parts:
        return False
    steps = [_tokens(part) for part in parts]
    if any(not tokens for tokens in steps):
        return False
    download = steps[0]
    client = download[0].lower()
    if client not in {"curl", "wget"}:
        return False
    options = {"wget": ("-O", "--output-document"),
               "curl": ("-o", "--output")}[client]
    output: str | None = None
    for i, token in enumerate(download[1:], start=1):
        if token in options and i + 1 < len(download):
            output = download[i + 1]
        elif any(token.startswith(option + "=") for option in options):
            output = token.split("=", 1)[1]
    path = _literal_path(output or "")
    if not path or sum(bool(re.fullmatch(r"https?://\S+", t, re.I)) for t in download) != 1:
        return False

    following = steps[1:]
    if len(following) == 2:
        chmod = following.pop(0)
        if (len(chmod) != 3 or chmod[:2] != ["chmod", "+x"]
                or _literal_path(chmod[2]) != path):
            return False
    execute = following[0]
    if execute[0].startswith(("./", "../", "/")):
        return _literal_path(execute[0]) == path
    if execute[0] in {"bash", "sh", "zsh", "python", "python3", "node"}:
        return len(execute) >= 2 and _literal_path(execute[1]) == path
    return False


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


class ShellExtractor:
    """Recover common shell commands and pipelines around existing matches."""

    @staticmethod
    def referenced_command(text: str, start: int, end: int) -> SourceSpan | None:
        """Separate explanatory command mentions/templates from executable syntax.

        Only use this for CMD-002 matches. Rule detections remain unchanged,
        and other technical constructs on the same line are still extracted.
        """
        matched = text[start:end]
        if not re.fullmatch(r"(?:PowerShell|pwsh|cmd\.exe)", matched, re.I):
            return None
        line_end = text.find("\n", end)
        if line_end == -1:
            line_end = len(text)
        following = text[end:line_end]
        # "These are PowerShell commands" and "PowerShell commands:" are
        # descriptions, not commands with incomplete arguments.
        if re.match(r"\s+commands?\b(?!\.(?:ps1|cmd|bat|exe)\b)", following, re.I):
            return SourceSpan("command_reference", start, end,
                              values=(("reference", matched),))
        # A self-contained placeholder is a complete template/reference,
        # not a partly recovered runnable PowerShell command.
        template = re.match(r"\s+-Command\s+([\"'])(?:\.{3}|…|<[^>\n]+>)\1", following, re.I)
        if template:
            return SourceSpan("command_template", start, end + template.end(),
                              values=(("interpreter", matched), ("placeholder", "true")))
        return None

    def extract(self, text: str, start: int, end: int) -> SourceSpan:
        left = text.rfind("\n", 0, start) + 1
        right_break = text.find("\n", end)
        right = len(text) if right_break < 0 else right_break

        # Explicit backslash continuations only; do not parse adjacent lines.
        for _ in range(8):
            if left == 0:
                break
            previous_end = left - 1
            previous_start = text.rfind("\n", 0, previous_end) + 1
            if not text[previous_start:previous_end].rstrip().endswith("\\"):
                break
            left = previous_start
        for _ in range(8):
            if right >= len(text) or not text[left:right].rstrip().endswith("\\"):
                break
            next_break = text.find("\n", right + 1)
            right = len(text) if next_break < 0 else next_break

        # Recognize statement separators outside quoting; a single pipe is
        # deliberately retained so download-and-execute stays one construct.
        boundaries = [left]
        quote: str | None = None
        escaped = False
        complex_shell = False
        pos = left
        while pos < right:
            char = text[pos]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "`":
                # Inline Markdown backticks are dealt with as wrappers below.
                complex_shell = True
            elif char == "#" and pos >= start and pos > left and text[pos - 1].isspace():
                # A trailing shell comment is context, not command evidence.
                right = pos
                break
            elif char in ";&|" and (
                char == ";" or text[pos:pos + 2] in ("&&", "||")
            ):
                step = 2 if text[pos:pos + 2] in ("&&", "||") else 1
                boundaries.extend((pos, pos + step))
                pos += step - 1
            pos += 1
        boundaries.append(right)
        boundaries = sorted(set(boundaries))
        segment_start = left
        segment_end = right
        if not staged_download_execution(text[left:right].strip()):
            for a, b in zip(boundaries, boundaries[1:]):
                if a <= start < b:
                    segment_start, segment_end = a, b
                    break
        # Earlier invocations on the same pipeline or privilege prefixes belong
        # to the same command, while prose before the first command does not.
        preceding = text[segment_start:start]
        candidates = list(_COMMAND.finditer(preceding))
        if candidates:
            segment_start += candidates[0].start()
        else:
            segment_start = start
        # Text in Markdown inline code is bounded by backticks, not the line.
        tick = text.find("`", start, segment_end)
        if tick >= 0:
            segment_end = tick
        segment_start, segment_end = _trim_span(text, segment_start, segment_end)
        if segment_end <= segment_start:
            return SourceSpan("shell_command", start, end, ExtractionStatus.PARTIAL)

        raw = text[segment_start:segment_end]
        command = _COMMAND.search(raw)
        values: list[tuple[str, str]] = []
        if command:
            values.append(("command", command.group(0)))
            if command.end() < len(raw):
                values.append(("arguments", raw[command.end():].strip()))
        urls = _URL.findall(raw)
        values.extend(("url", url.rstrip(".,;!?]")) for url in urls)
        # COMPLETE describes recovery of the source construct, not the
        # ability to evaluate its dynamic arguments. Balanced substitutions
        # such as $(dirname "$REPORT_PATH") remain complete evidence.
        status = (ExtractionStatus.PARTIAL if quote or raw.rstrip().endswith("\\")
                  or raw.count("$(") > raw.count(")")
                  else ExtractionStatus.COMPLETE)
        if complex_shell and "`" in raw and raw.count("`") % 2:
            status = ExtractionStatus.PARTIAL
        # A detected command mentioned in explanatory prose is not necessarily
        # a complete invocation (e.g., "use curl to download files").
        if re.match(r"^(?:curl|wget|python|bash|sh)\s+(?:to|for|when|and)\b", raw, re.I):
            status = ExtractionStatus.PARTIAL
            segment_end = min(segment_end, start + max(end - start, 1))
            values = [("command", text[start:segment_end].strip())]
        return SourceSpan("shell_command", segment_start, segment_end, status, tuple(values))


class UrlExtractor:
    """Recover bare URLs or a containing Markdown link without fetching it."""

    def extract(self, text: str, start: int, end: int) -> SourceSpan:
        left = text.rfind("\n", 0, start) + 1
        next_break = text.find("\n", end)
        right = len(text) if next_break < 0 else next_break
        for link in _MARKDOWN_LINK.finditer(text, left, right):
            if link.start() <= start < link.end():
                return SourceSpan(
                    "markdown_link", link.start(), link.end(),
                    values=(("label", link.group(1)), ("destination", link.group(2))),
                )
        # Regex matches can include sentence punctuation; keep source offsets
        # faithful to the URL rather than absorbing surrounding prose.
        raw = text[start:end]
        url = raw.rstrip(".,;!?]`")
        return SourceSpan("url_reference", start, start + len(url), values=(("url", url),))


class ApiCallExtractor:
    """Recover basic balanced function calls without evaluating expressions."""

    def extract(self, text: str, start: int, end: int) -> SourceSpan:
        opening = text.find("(", start, min(len(text), end + 16))
        if opening < 0:
            return SourceSpan("api_call", start, end, ExtractionStatus.PARTIAL)
        # Preserve simple call receivers, notably Path('file').write_text(...).
        call_start = start
        prefix = text[max(0, start - 256):start]
        receiver = re.search(
            r"(?:\b(?:Path|pathlib\.Path|open)\([^()\n]*\)|\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)$",
            prefix,
        )
        if receiver and text[start] == ".":
            call_start = start - len(prefix) + receiver.start()
        depth = 0
        quote: str | None = None
        escaped = False
        limit = min(len(text), opening + 4096)
        for pos in range(opening, limit):
            char = text[pos]
            if escaped:
                escaped = False
            elif char == "\\" and quote:
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    # A chained open(...).write(...) is one source expression.
                    if text[call_start:opening].strip() == "open":
                        chained = re.match(r"\.(?:write|write_text|write_bytes)\s*\(", text[pos + 1:])
                        if chained:
                            next_call = self.extract(text, pos + 1, pos + 1 + chained.end())
                            if next_call.status == ExtractionStatus.COMPLETE:
                                pos = next_call.end - 1
                    raw = text[call_start:pos + 1]
                    call_name = text[call_start:opening].strip()
                    values = [("call", call_name), ("arguments", text[opening + 1:pos])]
                    values.extend(("url", u.rstrip(".,;!?]")) for u in _URL.findall(raw))
                    literal_path = re.search(
                        r"\b(?:open|Path|pathlib\.Path|fs(?:\.promises)?\.readFile(?:Sync)?)\s*\(\s*([\"'])([^\"']+)\1",
                        raw,
                    )
                    if literal_path:
                        values.append(("path", literal_path.group(2)))
                    return SourceSpan("api_call", call_start, pos + 1, values=tuple(values))
        return SourceSpan("api_call", call_start, end, ExtractionStatus.PARTIAL)


class ReferenceExtractor:
    """Preserve exact standalone credential or path references."""

    def extract(self, text: str, start: int, end: int, *, kind: str) -> SourceSpan:
        return SourceSpan(kind, start, end, values=(("reference", text[start:end]),))
