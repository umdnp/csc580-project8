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
            elif self.inline_code_bounds(position) is not None:
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

    def inline_code_bounds(self, position: int) -> tuple[int, int] | None:
        """Return Markdown inline-code content bounds enclosing a source position."""
        index = max(0, bisect.bisect_right(self._starts, position) - 1)
        line = self._lines[index]
        if not self._markdown or line.in_fence or line.fence_marker:
            return None
        relative = position - line.start
        runs = list(re.finditer(r"`+", line.content))
        i = 0
        while i < len(runs):
            opening = runs[i]
            j = i + 1
            while j < len(runs) and len(runs[j].group()) != len(opening.group()):
                j += 1
            if j >= len(runs):
                i += 1
                continue
            closing = runs[j]
            if opening.end() <= relative < closing.start():
                return line.start + opening.end(), line.start + closing.start()
            i = j + 1
        return None

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
            candidates.append(self._candidate(text, match, contexts))
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
            context = contexts.at(candidate.start, candidate, filename)
            status = candidate.status
            if (status == ExtractionStatus.PARTIAL and
                    candidate.kind == "shell_command" and
                    context.kind == "code_block" and
                    context.language in {"make", "makefile", "gnumake"}):
                raw = text[candidate.start:candidate.end]
                masked = re.sub(r"\$\([A-Za-z_][A-Za-z0-9_]*\)", "MAKE_VAR", raw)
                # Only simple Make variables qualify; Make functions and
                # potentially executable or ambiguous syntax remain partial.
                if masked != raw and "$(" not in masked:
                    probe = self._shell.extract(masked, 0, len(masked))
                    if (probe.status == ExtractionStatus.COMPLETE and
                            probe.start == 0 and probe.end == len(masked)):
                        status = ExtractionStatus.COMPLETE
            results.append(Evidence(
                kind=candidate.kind,
                raw_text=text[candidate.start:candidate.end],
                normalized_text=text[candidate.start:candidate.end],
                rule_ids=tuple(sorted(ids)),
                filename=filename,
                source_id=source_id,
                start_offset=candidate.start,
                end_offset=candidate.end,
                context=context,
                extraction_status=status,
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
            match_end -= len(fragment) - len(fragment.rstrip(".,;!?]`"))
        return start <= match.start_offset and match_end <= end

    @staticmethod
    def _valid_offsets(text: str, match: RuleMatch) -> bool:
        return (match.start_offset is not None and match.end_offset is not None
                and 0 <= match.start_offset < match.end_offset <= len(text))

    def _candidate(
        self, text: str, match: RuleMatch, contexts: _SourceContext,
    ) -> SourceSpan:
        start, end = match.start_offset, match.end_offset
        assert start is not None and end is not None
        if match.rule_id == "CMD-001":
            opener = re.match(r"[ ]{0,3}(?:`{3,}|~{3,})[ \t]*([A-Za-z]+)", text[start:end])
            language = opener.group(1).lower() if opener else ""
            return SourceSpan("shell_code_block", start, end, values=(("language", language),))
        matched = text[start:end]
        if (re.match(r"(?:requests\.|httpx\.|axios(?:\.|\s*\()|fetch\s*\(|"
                     r"fs(?:\.promises)?\.|subprocess\.|os\.system\s*\(|"
                     r"open\s*\(|\.[\w]+\s*\()", matched, re.I)
                or match.rule_id == "FS-002"):
            return self._api.extract(text, start, end)
        if match.rule_id == "CMD-002":
            reference = self._shell.referenced_command(text, start, end)
            if reference is not None:
                return reference
        if match.rule_id in {"CMD-002", "NET-002", "FS-001", "FS-003", "EXT-001", "EXT-002", "SYS-001", "SYS-002"}:
            bounds = contexts.inline_code_bounds(start)
            if bounds is not None and end <= bounds[1]:
                # Isolate a command from neighboring backtick spans and prose.
                # Otherwise an apostrophe or earlier command on the same
                # Markdown line can corrupt extraction and completeness.
                left, right = bounds
                span = self._shell.extract(text[left:right], start - left, end - left)
                return replace(span, start=span.start + left, end=span.end + left)
            return self._shell.extract(text, start, end)
        if match.rule_id == "NET-001":
            return self._url.extract(text, start, end)
        if match.rule_id in {"CRED-001", "CRED-002"}:
            kind = "credential_file" if match.rule_id == "CRED-002" else "credential_reference"
            return self._reference.extract(text, start, end, kind=kind)
        return SourceSpan("unresolved_match", start, end, ExtractionStatus.UNSUPPORTED)
