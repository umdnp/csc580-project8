"""Turn existing rule matches into source evidence without changing detection."""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, replace

from .evidence_extractors import (
    ApiCallExtractor,
    ReferenceExtractor,
    ShellExtractor,
    SourceSpan,
    UrlExtractor,
)
from .evidence_models import Evidence, EvidenceContext, ExtractionStatus
from .evidence_normalizer import EvidenceNormalizer
from .models import RuleMatch


@dataclass(frozen=True, slots=True)
class _LineInfo:
    start: int
    content: str
    language: str | None
    heading: str | None
    in_fence: bool
    fence_marker: bool


class _SourceContext:
    """Index Markdown structure only when at least one match needs context."""

    def __init__(self, text: str, filename: str) -> None:
        self._markdown = filename.replace("\\", "/").lower().endswith(".md")
        self._lines: list[_LineInfo] = []
        self._starts: list[int] = []
        heading: str | None = None
        fence: str | None = None
        language: str | None = None
        offset = 0
        for line in text.splitlines(keepends=True):
            stripped = line.strip()
            fence_match = re.match(r"^\s*(`{3,}|~{3,})([^\r\n]*)", line) if self._markdown else None
            was_open = fence is not None
            opening_or_closing = False
            if fence_match and not was_open:
                fence = fence_match.group(1)
                info = fence_match.group(2).strip()
                language = info.split(maxsplit=1)[0].lower() if info else None
                opening_or_closing = True
            elif (fence_match and was_open and
                  fence_match.group(1)[0] == fence[0] and
                  len(fence_match.group(1)) >= len(fence) and
                  not fence_match.group(2).strip()):
                opening_or_closing = True
            elif self._markdown and not was_open:
                title = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
                if title:
                    heading = title.group(1)
            self._starts.append(offset)
            self._lines.append(_LineInfo(offset, line.rstrip("\r\n"), language, heading,
                                         fence is not None, opening_or_closing))
            offset += len(line)
            if opening_or_closing and was_open:
                fence = None
                language = None
        if not self._lines:
            self._starts.append(0)
            self._lines.append(_LineInfo(0, "", None, None, False, False))

    def at(self, position: int, span: SourceSpan, filename: str) -> EvidenceContext:
        index = max(0, bisect.bisect_right(self._starts, position) - 1)
        line = self._lines[index]
        stripped = line.content.lstrip()
        if span.kind == "shell_code_block":
            kind = "code_fence"
        elif span.kind == "markdown_link" and not line.in_fence:
            kind = "markdown_link"
        elif self._markdown:
            if line.in_fence:
                comment_prefix = "//" if line.language in {"js", "javascript", "ts", "typescript"} else "#"
                kind = "code_comment" if stripped.startswith(comment_prefix) else "code_block"
            elif stripped.startswith(">"):
                kind = "blockquote"
            elif re.match(r"^#{1,6}\s", stripped):
                kind = "markdown_heading"
            elif _inside_inline_code(line.content, position - line.start):
                kind = "inline_code"
            else:
                kind = "markdown_prose"
        else:
            if filename.lower().endswith((".sh", ".bash", ".zsh", ".py", ".rb", ".yaml", ".yml")):
                kind = "source_comment" if stripped.startswith("#") else "source_code"
            elif filename.lower().endswith((".js", ".ts")):
                kind = "source_comment" if stripped.startswith("//") else "source_code"
            else:
                kind = "source_text"
        nearby = line.content.strip()[:160]
        if (self._markdown and span.kind in {"url_reference", "markdown_link"}
                and kind in {"markdown_prose", "markdown_link"}):
            nearby = self._url_context(index)
        return EvidenceContext(kind=kind, language=line.language, heading=line.heading,
                               nearby_text=nearby)

    def _url_context(self, index: int) -> str:
        """Keep a short, connected Markdown sentence, not an entire document."""
        current = self._lines[index].content.strip()
        if index == 0:
            return current[:320]
        previous = self._lines[index - 1]
        preceding = previous.content.strip()
        if previous.in_fence or previous.fence_marker or preceding.startswith(("#", ">")):
            return current[:320]
        if not preceding and index >= 2:
            earlier = self._lines[index - 2]
            earlier_text = earlier.content.strip()
            if (not earlier.in_fence and not earlier.fence_marker and
                    earlier_text.endswith(":") and not earlier_text.startswith(("#", ">"))):
                return (earlier_text + " " + current)[:320]
        # Wrapped instructions frequently end in "at" or "from" just before
        # the URL. Do not pull in unrelated preceding paragraphs.
        if (preceding and (re.search(r"(?:at|from|in|on|:)\s*$", preceding, re.I)
                           or current.lower().startswith(("at http", "at [", "from http", "from [")))):
            return (preceding + " " + current)[:320]
        return current[:320]


def _inside_inline_code(line: str, relative_position: int) -> bool:
    return line[:max(0, relative_position)].count("`") % 2 == 1


class EvidenceExtractor:
    """Recover each matching construct once and associate all covering rules."""

    def __init__(self) -> None:
        self._shell = ShellExtractor()
        self._url = UrlExtractor()
        self._api = ApiCallExtractor()
        self._reference = ReferenceExtractor()
        self._normalizer = EvidenceNormalizer()

    def extract(
        self,
        text: str,
        matches: tuple[RuleMatch, ...],
        *,
        filename: str = "SKILL.md",
        source_id: str | None = None,
    ) -> tuple[Evidence, ...]:
        if not matches:
            return ()
        contexts = _SourceContext(text, filename)
        candidates: list[SourceSpan] = []
        for match in matches:
            if not self._valid_offsets(text, match):
                continue
            candidates.append(self._candidate(text, match))
        # Prefer the complete containing construct, rather than one URL or
        # credential record for each regex match inside the same command.
        priority = {"shell_command": 0, "api_call": 1, "markdown_link": 2}
        candidates.sort(key=lambda c: (c.start, -c.end, priority.get(c.kind, 3)))
        selected: list[SourceSpan] = []
        furthest_end = -1
        for candidate in candidates:
            if candidate.end <= furthest_end:
                continue
            selected.append(candidate)
            furthest_end = candidate.end

        # Match-to-construct associations are computed only near the source
        # spans; a single long document need not be compared pairwise.
        located = sorted(
            ((i, match) for i, match in enumerate(matches) if self._valid_offsets(text, match)),
            key=lambda pair: pair[1].start_offset,
        )
        match_starts = [match.start_offset for _, match in located]
        assigned: set[int] = set()
        results: list[Evidence] = []
        for candidate in selected:
            ids: set[str] = set()
            index = bisect.bisect_left(match_starts, candidate.start)
            while index < len(located) and match_starts[index] < candidate.end:
                original_index, match = located[index]
                if (original_index not in assigned and
                        self._covers(text, candidate.start, candidate.end, match)):
                    ids.add(match.rule_id)
                    assigned.add(original_index)
                index += 1
            if not ids:
                continue
            results.append(Evidence(
                kind=candidate.kind,
                raw_text=text[candidate.start:candidate.end],
                normalized_text=text[candidate.start:candidate.end],
                rule_ids=tuple(sorted(ids)),
                filename=filename,
                source_id=source_id,
                start_offset=candidate.start,
                end_offset=candidate.end,
                context=contexts.at(candidate.start, candidate, filename),
                extraction_status=candidate.status,
                values=candidate.values,
            ))
        for index, match in enumerate(matches):
            if index in assigned:
                continue
            start = match.start_offset if match.start_offset is not None else 0
            end = match.end_offset if match.end_offset is not None else start
            if not self._valid_offsets(text, match):
                # No trustworthy location: keep the original matched text only.
                raw = match.matched_text or ""
                results.append(Evidence(
                    kind="unresolved_match", raw_text=raw, normalized_text=raw,
                    rule_ids=(match.rule_id,), filename=filename, source_id=source_id,
                    extraction_status=ExtractionStatus.UNSUPPORTED,
                ))
            else:
                results.append(Evidence(
                    kind="unresolved_match", raw_text=text[start:end],
                    normalized_text=text[start:end], rule_ids=(match.rule_id,),
                    filename=filename, source_id=source_id,
                    start_offset=start, end_offset=end,
                    context=contexts.at(start, SourceSpan("unresolved_match", start, end), filename),
                    extraction_status=ExtractionStatus.PARTIAL,
                ))
        results = [replace(item, normalized_text=self._normalizer.normalize(item))
                   for item in results]
        return tuple(sorted(results, key=lambda e: (e.start_offset if e.start_offset is not None else -1,
                                                  e.end_offset if e.end_offset is not None else -1)))

    @staticmethod
    def _covers(text: str, start: int, end: int, match: RuleMatch) -> bool:
        if match.start_offset is None or match.end_offset is None:
            return False
        match_end = match.end_offset
        if match.rule_id == "NET-001":
            # The original URL regex includes trailing punctuation such as a
            # semicolon separator. Preserve its count but attribute it to the
            # actual URL inside the extracted command.
            fragment = text[match.start_offset:match_end]
            match_end -= len(fragment) - len(fragment.rstrip(".,;!?]"))
        return start <= match.start_offset and match_end <= end

    @staticmethod
    def _valid_offsets(text: str, match: RuleMatch) -> bool:
        return (match.start_offset is not None and match.end_offset is not None
                and 0 <= match.start_offset < match.end_offset <= len(text))

    def _candidate(self, text: str, match: RuleMatch) -> SourceSpan:
        start, end = match.start_offset, match.end_offset
        assert start is not None and end is not None
        if match.rule_id == "CMD-001":
            language = text[start:end].lstrip("`").strip().lower()
            return SourceSpan("shell_code_block", start, end, values=(("language", language),))
        matched = text[start:end]
        if (re.match(r"(?:requests\.|fs(?:\.promises)?\.|open\s*\(|\.[\w]+\s*\()", matched, re.I)
                or match.rule_id == "FS-002"):
            return self._api.extract(text, start, end)
        if match.rule_id == "CMD-002":
            reference = self._shell.referenced_command(text, start, end)
            if reference is not None:
                return reference
        if match.rule_id in {"CMD-002", "NET-002", "FS-001", "FS-003", "EXT-001", "EXT-002", "SYS-001", "SYS-002"}:
            return self._shell.extract(text, start, end)
        if match.rule_id == "NET-001":
            return self._url.extract(text, start, end)
        if match.rule_id in {"CRED-001", "CRED-002"}:
            kind = "credential_file" if match.rule_id == "CRED-002" else "credential_reference"
            return self._reference.extract(text, start, end, kind=kind)
        return SourceSpan("unresolved_match", start, end, ExtractionStatus.UNSUPPORTED)
