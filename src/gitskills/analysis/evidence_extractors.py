"""Small source-construct extractors; no rule evaluation or code execution."""

from __future__ import annotations

import re
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
_API = re.compile(r"(?:\b(?:requests|fs(?:\.promises)?)\.[\w]+|\bopen|\.[\w]+)\s*\(")
_COMMAND = re.compile(
    r"(?<![\w.-])(?:\./(?:[\w.-]+/)*[\w.-]+\.(?:sh|bash|py|js|mjs|ps1)|"
    r"sudo|su|curl|wget|python(?:\d+(?:\.\d+)*)?|bash|sh|zsh|"
    r"node|bun|uvx?|npm|npx|pnpm|yarn|pip\d*|docker|pwsh|powershell|cmd\.exe|"
    r"rm|mv|cp|mkdir|touch|cat|less|more|chmod|chown|setfacl|systemctl|"
    r"service|crontab|apt(?:-get)?|dnf|yum|brew|"
    r"Invoke-WebRequest|Invoke-RestMethod|Remove-Item|Move-Item|Copy-Item|"
    r"Set-Content|Add-Content|Get-Content)\b",
    re.IGNORECASE,
)
_MARKDOWN_LINK = re.compile(r"\[([^\]\n]*)\]\((https?://[^\s)]+)\)", re.IGNORECASE)


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
        status = (ExtractionStatus.PARTIAL if quote or "$(" in raw or raw.rstrip().endswith("\\")
                  else ExtractionStatus.COMPLETE)
        if complex_shell and "`" in raw:
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
