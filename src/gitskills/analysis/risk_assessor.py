"""Conservative, static review indicators for changed GitSkills evidence."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping
from urllib.parse import urlsplit

from .evidence_models import Evidence, ExtractionStatus
from .external_instructions import InstructionRole, instruction_role
from .models import AnalysisComparison
from .risk_models import IndicatorStatus, RiskAssessment, RiskIndicator

_URL = re.compile(r"https?://[^\s<>()\"']+", re.I)
_SCRIPT = r"[\w./-]+\.(?:sh|bash|py|js|mjs|ps1)"
_DIRECT_SCRIPT = re.compile(r"^\s*(\./" + _SCRIPT + r")(?=\s|$)", re.I)
_INTERPRETER_SCRIPT = re.compile(
    r"^\s*(?:python[\d.]*|bash|sh|zsh|node|pwsh)\s+((?:\./|\.\./|scripts/|bin/)"
    + _SCRIPT + r")(?=\s|$)", re.I,
)
_SENSITIVE = re.compile(
    r"(?:^|[/\\])(?:\.aws/credentials|\.ssh/(?:id_rsa|id_ed25519|authorized_keys|config)|"
    r"\.env(?:\.[\w.-]+)?|etc/(?:shadow|sudoers|passwd|ssh/sshd_config)|"
    r"\.kube/config)(?:$|[\s'\"/\\])", re.I,
)
_CREDENTIAL = re.compile(
    r"\b(?:[A-Z][A-Z0-9_]*_(?:TOKEN|API_KEY|SECRET|PASSWORD)|"
    r"api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)\b|"
    r"\bAuthorization\s*:\s*(?:Bearer|Basic)\b", re.I,
)
_WARNING = re.compile(
    r"\b(?:never|do\s+not|don't|must\s+not|should\s+not|avoid|warning\s*:\s*do\s+not)\s+"
    r"(?:\w+\s+){0,4}(?:run|execute|invoke|use|follow|download|install|send|post|read|open|delete|remove)\b",
    re.I,
)
_BYPASS = re.compile(r"(?<!\S)(?:-k|--insecure|--no-check-certificate)(?=\s|$)|\bverify\s*=\s*False\b", re.I)
_TRANSFER = re.compile(
    r"\brequests\.(?:post|put|patch)\s*\([^)]*\b(?:data|json|files)\s*=|"
    r"\bcurl\b[^\n]*(?:\s(?:--data(?:-[\w-]+)?|--form|--upload-file|-d|-F|-T)(?=\s|=))",
    re.I | re.S,
)
_FILE_ACTION = re.compile(r"\b(?:cat|less|more|Get-Content|open|read_text|read_bytes|"
                          r"readFile|readFileSync|write_text|write_bytes|write|"
                          r"rm|Remove-Item|mv|Move-Item|cp|Copy-Item|Set-Content|Add-Content)\b", re.I)
_SYSTEM_CHANGE = re.compile(
    r"\b(?:chmod|chown|setfacl)\s+\S+|"
    r"\bsystemctl\s+(?:enable|disable|start|stop|restart|mask|unmask|edit)\b|"
    r"\bservice\s+\S+\s+(?:start|stop|restart|reload)\b|"
    r"\bcrontab\s+(?!-l\b)\S+", re.I,
)
_INSTALL = re.compile(r"\b(?:pip\d*|npm|apt(?:-get)?|dnf|yum|brew)\s+(?:install|i)\b", re.I)
_INSTALL_SOURCE = re.compile(
    r"(?:--index-url|--extra-index-url|--registry|--find-links)\s*(?:=|\s)\s*([^\s]+)", re.I,
)
_ACQUIRE = re.compile(r"\b(?:curl|wget)\b.*(?:\s(?:-o|--output|--output-document)\s+\S+\.(?:sh|py|js)|"
                      r"https?://[^\s]+\.(?:sh|py|js)(?=\s|$))", re.I | re.S)


def _values(e: Evidence, key: str) -> tuple[str, ...]:
    return tuple(value for field, value in e.values if field == key)


def _urls(e: Evidence) -> tuple[str, ...]:
    values = _values(e, "url") or _values(e, "destination")
    if values:
        return values
    return tuple(url.rstrip(".,;!?]`") for url in _URL.findall(e.raw_text))


def _host(url: str) -> str | None:
    try:
        return urlsplit(url).hostname
    except ValueError:
        return None


def _operation(e: Evidence) -> str | None:
    if e.kind == "api_call":
        return next(iter(_values(e, "call")), "").lower() or None
    if e.kind != "shell_command":
        return None
    cmd = next(iter(_values(e, "command")), "").lower()
    if cmd in {"sudo", "su"}:
        m = re.search(r"\b(?:sudo|su)\s+(\S+)", e.raw_text, re.I)
        cmd = m.group(1).lower() if m else cmd
    # Keep the interpreter at the end of a remote-execution pipeline as a
    # separate operation from a plain download command.
    if "EXT-001" in e.rule_ids:
        return cmd + "|shell"
    return cmd or None


def _group(e: Evidence) -> tuple[str, str, str] | None:
    operation = _operation(e)
    if not operation or e.kind not in {"api_call", "shell_command"}:
        return None
    return (e.filename.replace("\\", "/"), e.kind, operation)


def _pair_changes(changes) -> dict[Evidence, Evidence]:
    """Pair only unique same-operation changes; never guess among peers."""
    old: dict[tuple[str, str, str], list[Evidence]] = defaultdict(list)
    new: dict[tuple[str, str, str], list[Evidence]] = defaultdict(list)
    for e in changes.removed:
        if e.extraction_status == ExtractionStatus.COMPLETE and (key := _group(e)):
            old[key].append(e)
    for e in changes.added:
        if e.extraction_status == ExtractionStatus.COMPLETE and (key := _group(e)):
            new[key].append(e)
    pairs = {}
    for key, items in new.items():
        previous = old.get(key, ())
        if len(items) == len(previous) == 1:
            a, b = items[0], previous[0]
            if a.context.heading and b.context.heading and a.context.heading != b.context.heading:
                continue
            pairs[a] = b
    return pairs


def _context_status(e: Evidence) -> IndicatorStatus | None:
    line = e.context.nearby_text or ""
    if _WARNING.search(line):
        return None  # An explicit warning is not an instruction to do it.
    if e.extraction_status != ExtractionStatus.COMPLETE or e.context.kind in {
        "source_comment", "code_comment", "blockquote", "markdown_heading",
    }:
        return IndicatorStatus.UNCERTAIN
    if e.kind == "shell_command" and e.context.kind == "markdown_prose":
        # Non-command prose may match simple words such as curl or rm.
        if not re.match(r"^(?:\s*(?:[-*]\s+)?(?:`)?(?:sudo\s+)?(?:curl|wget|rm|python|"
                        r"bash|sh|pip|npm|chmod|systemctl|cat|./))\b", line, re.I):
            if not re.search(r"\b(?:run|execute|install|use|invoke)\s+(?:the\s+)?", line, re.I):
                return IndicatorStatus.UNCERTAIN
    return IndicatorStatus.SUPPORTED


def _new(e: Evidence, previous: tuple[Evidence, ...]) -> bool:
    # Occurrence-count increases alone are not new security behavior.
    return not any(p.filename == e.filename and p.kind == e.kind and
                   p.normalized_text == e.normalized_text for p in previous)


def _script(e: Evidence) -> str | None:
    if e.kind != "shell_command" or "CMD-002" not in e.rule_ids:
        return None
    for pattern in (_DIRECT_SCRIPT, _INTERPRETER_SCRIPT):
        match = pattern.match(e.raw_text)
        if match:
            return match.group(1).replace("\\", "/").removeprefix("./")
    return None


def _delete_flags(text: str) -> frozenset[str]:
    """Recognize recursive/force deletion independently of option order."""
    result: set[str] = set()
    for flag in re.findall(r"(?<!\S)-([a-z]+)(?=\s|$)", text, re.I):
        if "r" in flag.lower():
            result.add("recursive")
        if "f" in flag.lower():
            result.add("force")
    if re.search(r"--recursive|\b-Recurse\b", text, re.I):
        result.add("recursive")
    if re.search(r"--force|\b-Force\b", text, re.I):
        result.add("force")
    return frozenset(result)


def _source_change(e: Evidence) -> str | None:
    if not _INSTALL.search(e.raw_text):
        return None
    match = _INSTALL_SOURCE.search(e.raw_text)
    return match.group(0).strip().lower() if match else None


def _sensitive_target(e: Evidence) -> str | None:
    if not _FILE_ACTION.search(e.raw_text):
        return None
    match = _SENSITIVE.search(e.raw_text.replace("\\", "/"))
    return match.group().strip(" \"'\t/\n") if match else None


class RiskAssessor:
    """Identify evidence-backed reasons for manual security review."""

    def assess(
        self,
        comparison: AnalysisComparison,
        *,
        base_script_hashes: Mapping[str, str] | None = None,
        derived_script_hashes: Mapping[str, str] | None = None,
    ) -> RiskAssessment:
        """Evaluate only stored static evidence; never fetch or execute scripts."""
        previous = comparison.base.evidence
        changes = comparison.evidence_changes
        pairs = _pair_changes(changes)
        base_hashes = {k.replace("\\", "/").removeprefix("./"): v
                       for k, v in (base_script_hashes or {}).items()}
        derived_hashes = {k.replace("\\", "/").removeprefix("./"): v
                          for k, v in (derived_script_hashes or {}).items()}
        results: list[RiskIndicator] = []
        recorded: set[tuple[str, str, int | None, str]] = set()

        def add(indicator: str, reason: str, e: Evidence, *,
                old: Evidence | None = None,
                status: IndicatorStatus | None = None) -> None:
            contextual = _context_status(e)
            if contextual is None:
                return
            resolved = (IndicatorStatus.UNCERTAIN if status == IndicatorStatus.UNCERTAIN
                        or contextual == IndicatorStatus.UNCERTAIN else IndicatorStatus.SUPPORTED)
            key = (indicator, e.filename, e.start_offset, e.raw_text)
            if key in recorded:
                return
            recorded.add(key)
            results.append(RiskIndicator(indicator, reason, (e,), (old,) if old else (), resolved))

        original_network_hosts = {
            host for e in previous if self._network(e)
            for url in _urls(e) if (host := _host(url))
        }
        for e in changes.added:
            if not _new(e, previous):
                continue
            old = pairs.get(e)
            text = e.raw_text
            rules = set(e.rule_ids)
            is_network = self._network(e)
            urls = _urls(e)

            if "EXT-001" in rules and not (old and "EXT-001" in old.rule_ids):
                ambiguous = any("EXT-001" in p.rule_ids and p.filename == e.filename
                                for p in changes.removed)
                add("RI-001", "Direct download-to-interpreter operation introduced"
                    if not ambiguous else "Download-to-interpreter operation changed without clear correspondence",
                    e, old=old, status=IndicatorStatus.UNCERTAIN if ambiguous else None)
            if old and "EXT-001" in rules and "EXT-001" in old.rule_ids and urls != _urls(old):
                add("RI-002", "Source URL of remotely executed code changed", e, old=old)
            if is_network:
                if any(host not in original_network_hosts for url in urls
                       if (host := _host(url))):
                    add("RI-003", "New network-operation hostname observed", e, old=old)
                if _TRANSFER.search(text) and not (old and _TRANSFER.search(old.raw_text)):
                    add("RI-003", "Explicit outbound payload transfer introduced", e, old=old)
                if _BYPASS.search(text) and not (old and _BYPASS.search(old.raw_text)):
                    add("RI-004", "Certificate verification bypass introduced", e, old=old)
                if old and any(urlsplit(a).scheme == "http" and
                               urlsplit(b).scheme == "https" for a in urls for b in _urls(old)):
                    add("RI-004", "Network operation changed from HTTPS to HTTP", e, old=old)
            if "EXT-002" in rules and _INSTALL.search(text):
                was_install = old is not None and _INSTALL.search(old.raw_text)
                possible_replacement = any(
                    p.filename == e.filename and _group(p) == _group(e)
                    and _INSTALL.search(p.raw_text) for p in changes.removed
                )
                if not was_install and not possible_replacement:
                    add("RI-005", "External package installation introduced", e, old=old)
                elif was_install and _source_change(e) != _source_change(old):
                    add("RI-005", "Explicit package source or registry changed", e, old=old)
            if is_network and "EXT-001" not in rules and _ACQUIRE.search(text) and not (old and _ACQUIRE.search(old.raw_text)):
                add("RI-005", "External script acquisition introduced", e, old=old)
            if "FS-001" in rules and re.search(r"\b(?:rm|Remove-Item)\s+", text, re.I):
                if not old or not re.search(r"\b(?:rm|Remove-Item)\s+", old.raw_text, re.I):
                    uncertain = any(p.filename == e.filename and _group(p) == _group(e)
                                    and re.search(r"\b(?:rm|Remove-Item)\s+", p.raw_text, re.I)
                                    for p in changes.removed)
                    add("RI-006", "Destructive file operation introduced"
                        if not uncertain else "Destructive operation changed without clear correspondence",
                        e, old=old, status=IndicatorStatus.UNCERTAIN if uncertain else None)
                elif _delete_flags(text) - _delete_flags(old.raw_text):
                    add("RI-006", "Deletion scope or force options expanded", e, old=old)
                elif "SYS-001" in rules and "SYS-001" not in old.rule_ids:
                    add("RI-006", "File deletion gained elevated privileges", e, old=old)
            if "FS-001" in rules and "SYS-001" in rules and not (old and "SYS-001" in old.rule_ids):
                add("RI-006", "Privileged file operation introduced", e, old=old)
            target = _sensitive_target(e)
            prior_target = _sensitive_target(old) if old else None
            new_credential_read = (
                "FS-003" in rules and "CRED-002" in rules and bool(target)
                and (old is None or target != prior_target or "FS-003" not in old.rule_ids)
            )
            if new_credential_read:
                add("RI-007", "Read operation newly targets a recognized credential file", e, old=old)
            if is_network and "CRED-001" in rules and _CREDENTIAL.search(text):
                before_credential = bool(old and _CREDENTIAL.search(old.raw_text))
                before_hosts = {_host(u) for u in _urls(old)} if old else set()
                current_hosts = {_host(u) for u in urls}
                if not before_credential or before_hosts != current_hosts:
                    reason = (
                        "Outbound network operation introduces a credential reference"
                        if not before_credential else
                        "Credential-bearing network operation changes destination"
                    )
                    add("RI-007", reason, e, old=old)
            if "SYS-002" in rules and _SYSTEM_CHANGE.search(text):
                add("RI-008", "System or permissions modification introduced or changed", e, old=old)
            if rules & {"FS-001", "FS-002", "FS-003"} and target and (
                target != prior_target or not old or
                (rules & {"FS-002", "FS-003"}) != (set(old.rule_ids) & {"FS-002", "FS-003"})
            ):
                add("RI-009", "File operation newly targets a recognized sensitive path", e, old=old)

            script = _script(e)
            if script:
                prior_scripts = [p for p in previous if p.filename == e.filename and _script(p)]
                if not prior_scripts:
                    add("RI-010", "Local script invocation introduced", e)
                elif old and (old_script := _script(old)) and old_script != script:
                    before_hash = base_hashes.get(old_script)
                    after_hash = derived_hashes.get(script)
                    if before_hash and after_hash and before_hash != after_hash:
                        add("RI-010", "Invoked local script has different known content", e, old=old)
                    elif not (before_hash and after_hash):
                        add("RI-010", "Local script target changed; sibling content unavailable", e,
                            old=old, status=IndicatorStatus.UNCERTAIN)
                elif old is None:
                    add("RI-010", "Local script invocation changed without clear correspondence", e,
                        status=IndicatorStatus.UNCERTAIN)

        self._external_instructions(comparison, add)

        # Identical invocation evidence may still reference a modified sibling.
        base_scripts = {_script(e): e for e in previous if _script(e)}
        for e in comparison.derived.evidence:
            script = _script(e)
            if script and script in base_scripts and base_hashes.get(script) and derived_hashes.get(script):
                if base_hashes[script] != derived_hashes[script]:
                    add("RI-010", "Invoked sibling script content changed", e, old=base_scripts[script])
        incomplete = any(e.extraction_status != ExtractionStatus.COMPLETE
                         for result in (comparison.base, comparison.derived)
                         for e in result.evidence)
        return RiskAssessment(
            indicators=tuple(results),
            coverage="incomplete" if incomplete else "complete",
            coverage_notes=("Partial or unsupported evidence extraction",) if incomplete else (),
        )

    @staticmethod
    def _external_instructions(comparison: AnalysisComparison, add) -> None:
        """Evaluate changed URL roles, including unchanged URLs with new directives."""
        def references(evidence: tuple[Evidence, ...]) -> list[Evidence]:
            return [e for e in evidence if e.kind in {"url_reference", "markdown_link"}
                    and "NET-001" in e.rule_ids and e.filename.lower().endswith(".md")
                    and e.context.kind in {"markdown_prose", "markdown_link"}]

        earlier = references(comparison.base.evidence)
        later = references(comparison.derived.evidence)
        for current in later:
            role = instruction_role(current)
            url = _urls(current)
            if not url:
                continue
            same_url = [e for e in earlier if e.filename == current.filename and _urls(e) == url]
            if any(instruction_role(e) == InstructionRole.DEPENDENCY for e in same_url):
                continue  # An existing directive (or repeated occurrence) is not new behavior.
            if same_url:
                old = same_url[0] if len(same_url) == 1 else None
                if any(instruction_role(e) == InstructionRole.UNCERTAIN for e in same_url):
                    # Earlier wording might already have been a directive.
                    if role == InstructionRole.DEPENDENCY:
                        add("RI-011", "External instruction role became explicit; prior wording uncertain",
                            current, old=old, status=IndicatorStatus.UNCERTAIN)
                    continue
                if role == InstructionRole.DEPENDENCY:
                    add("RI-011", "External reference became an explicit instruction dependency",
                        current, old=old)
                elif role == InstructionRole.UNCERTAIN:
                    add("RI-011", "Changed URL context is ambiguous", current, old=old,
                        status=IndicatorStatus.UNCERTAIN)
                continue

            # An unrelated added URL must not be guessed to replace an old one.
            prior_directives = [e for e in earlier if e.filename == current.filename
                                and instruction_role(e) == InstructionRole.DEPENDENCY
                                and e.context.heading == current.context.heading
                                and not any(d.filename == e.filename and _urls(d) == _urls(e)
                                            and instruction_role(d) == InstructionRole.DEPENDENCY
                                            for d in later)]
            new_directives = [e for e in later if e.filename == current.filename
                              and e.context.heading == current.context.heading
                              and instruction_role(e) == InstructionRole.DEPENDENCY
                              and not any(b.filename == e.filename and _urls(b) == _urls(e)
                                          and instruction_role(b) == InstructionRole.DEPENDENCY
                                          for b in earlier)]
            prior = (prior_directives[0] if len(prior_directives) == len(new_directives) == 1
                     else None)
            if role == InstructionRole.DEPENDENCY:
                add("RI-011", "External instruction source changed" if prior else
                    "External instruction dependency introduced", current, old=prior)
            elif role == InstructionRole.UNCERTAIN:
                # Only report new ambiguous references, not already-known URLs.
                add("RI-011", "Possible external instruction reference is ambiguous",
                    current, status=IndicatorStatus.UNCERTAIN)

    @staticmethod
    def _network(e: Evidence) -> bool:
        if "NET-002" not in e.rule_ids or e.kind not in {"shell_command", "api_call"}:
            return False
        if e.kind == "api_call":
            return (_operation(e) or "").startswith("requests.")
        return bool(re.match(r"^\s*(?:curl|wget|Invoke-WebRequest|Invoke-RestMethod)\b", e.raw_text, re.I))
