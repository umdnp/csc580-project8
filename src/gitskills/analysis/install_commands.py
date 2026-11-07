"""Identify and match dependency-install commands without inferring manifest contents."""

from __future__ import annotations

import re
import shlex
from collections import defaultdict

from .evidence_models import Evidence, ExtractionStatus

INSTALL_PATTERN = re.compile(
    r"\b(?:pip\d*|npm|apt(?:-get)?|dnf|yum|brew)\s+(?:install|i|ci)\b|"
    r"\b(?:pnpm|yarn|bun)\s+(?:add|install)\b", re.I,
)
_INSTALL_SOURCE = re.compile(
    r"(?P<option>--index-url|--extra-index-url|--registry|--find-links)"
    r"\s*(?:=|\s)\s*(?P<value>[^\s]+)", re.I,
)
_JS_PACKAGE = re.compile(r"(?:@[\w.-]+/)?[\w.-]+(?:@[\w.*^~+-]+)?")
_WORKSPACE_FLAGS = {"--workspace", "-w", "--filter", "-F"}
_WORKSPACE_EQUALS = re.compile(r"^(?:--workspace|--filter)=(.+)$")
_DIRECT_PACKAGE_SOURCE = re.compile(
    r"(?:^|@)(?:git\+)?(?:https?|ssh|git|file)://|^git@[^\s:]+:|^github:", re.I,
)
INSTALL_ARGUMENT_VALUES = {
    "--registry", "--index-url", "--extra-index-url", "--find-links",
    "--prefix", "--cache-dir", "--config", "--cwd",
    "--workspace", "-w", "--filter", "-F",
}


def _js_install_key(e: Evidence) -> tuple[str, str | None, tuple[str, ...], tuple[str, ...]] | None:
    """Identify explicit JavaScript package installs, independent of package manager."""
    if e.kind != "shell_command" or "EXT-002" not in e.rule_ids:
        return None
    try:
        parts = shlex.split(e.raw_text)
    except ValueError:
        return None
    if len(parts) < 3:
        return None
    manager, action = parts[0].lower(), parts[1].lower()
    if not ((manager == "npm" and action in {"install", "i"}) or
            (manager in {"bun", "pnpm", "yarn"} and action in {"add", "install"})):
        return None

    packages: list[str] = []
    index = 2
    while index < len(parts):
        item = parts[index]
        if item == "--registry":
            if index + 1 >= len(parts) or not parts[index + 1].strip():
                return None
            index += 2
            continue
        if item.startswith("--registry=") and len(item) > len("--registry="):
            index += 1
            continue
        if item in _WORKSPACE_FLAGS:
            if index + 1 >= len(parts):
                return None
            index += 2
            continue
        if _WORKSPACE_EQUALS.match(item) or re.match(r"^-[wF](?:=)?\S+", item):
            index += 1
            continue
        # Other flags, variables, source URLs or compound syntax are not
        # assumed equivalent across package managers.
        if item.startswith("-") or not _JS_PACKAGE.fullmatch(item):
            return None
        name, delimiter, _version = item.rpartition("@")
        packages.append(name if delimiter and name else item)
        index += 1
    if not packages:
        return None
    return (e.filename.replace("\\", "/"), e.context.heading,
            tuple(sorted(packages)), _workspace_scope(e))


def _pair_install_changes(changes, identity, *,
                          allow_scope_change: bool = False) -> dict[Evidence, Evidence]:
    """Prefer exact source matches and only infer unique workspace replacements."""
    previous: dict[tuple, list[Evidence]] = defaultdict(list)
    for evidence in changes.removed:
        if evidence.extraction_status == ExtractionStatus.COMPLETE and (key := identity(evidence)):
            previous[key].append(evidence)
    pairs: dict[Evidence, Evidence] = {}
    for evidence in changes.added:
        if evidence.extraction_status != ExtractionStatus.COMPLETE or not (key := identity(evidence)):
            continue
        candidates = previous.get(key)
        if candidates:
            source = _source_change(evidence)
            counterpart = next((old for old in candidates if _source_change(old) == source),
                               candidates[0])
            pairs[evidence] = counterpart
            candidates.remove(counterpart)
    if not allow_scope_change:
        return pairs

    matched_old = set(pairs.values())
    old_unpaired: dict[tuple, list[Evidence]] = defaultdict(list)
    new_unpaired: dict[tuple, list[Evidence]] = defaultdict(list)
    for evidence in changes.removed:
        if evidence not in matched_old and (key := identity(evidence)):
            old_unpaired[key[:3]].append(evidence)
    for evidence in changes.added:
        if evidence not in pairs and (key := identity(evidence)):
            new_unpaired[key[:3]].append(evidence)
    for key, items in new_unpaired.items():
        if len(items) == len(old_unpaired.get(key, ())) == 1:
            pairs[items[0]] = old_unpaired[key][0]
    return pairs


def _js_install_pairs(changes) -> dict[Evidence, Evidence]:
    return _pair_install_changes(changes, _js_install_key, allow_scope_change=True)


def _workspace_scope(e: Evidence) -> tuple[str, ...]:
    """Return explicit workspace selectors, without assuming manifest contents."""
    try:
        parts = shlex.split(e.raw_text)
    except ValueError:
        return ()
    scopes: list[str] = []
    index = 2
    while index < len(parts):
        part = parts[index]
        if part in _WORKSPACE_FLAGS:
            if index + 1 < len(parts):
                scopes.append(parts[index + 1])
                index += 2
                continue
        match = _WORKSPACE_EQUALS.match(part)
        if match:
            scopes.append(match.group(1))
        elif re.match(r"^-[wF](?:=)?\S+", part):
            scopes.append(re.sub(r"^-[wF]=?", "", part))
        index += 1
    return tuple(sorted(scopes))


def _direct_install_sources(e: Evidence) -> tuple[str, ...]:
    """Recognize literal package URLs and VCS targets, not inferred downloads."""
    try:
        parts = shlex.split(e.raw_text)
    except ValueError:
        return ()
    if len(parts) < 3:
        return ()
    sources: list[str] = []
    skip_value = False
    for part in parts[2:]:
        if skip_value:
            skip_value = False
            continue
        if part in {"--registry", "--index-url", "--extra-index-url", "--find-links",
                    "--workspace", "--filter", "-w", "-F", "--prefix", "--cache-dir",
                    "--config", "--cwd"}:
            skip_value = True
            continue
        if part.startswith(("--registry=", "--index-url=", "--extra-index-url=",
                            "--find-links=", "--workspace=", "--filter=")):
            continue
        if _DIRECT_PACKAGE_SOURCE.search(part):
            sources.append(part)
    return tuple(sources)


def _direct_install_identity(e: Evidence) -> tuple[str, str | None, str, str] | None:
    """Group source-URL installs by a named package or remote artifact."""
    sources = _direct_install_sources(e)
    if len(sources) != 1 or e.kind != "shell_command" or "EXT-002" not in e.rule_ids:
        return None
    try:
        parts = shlex.split(e.raw_text)
    except ValueError:
        return None
    source = sources[0]
    manager = parts[0].lower()
    if manager in {"npm", "yarn", "pnpm", "bun"}:
        family = "javascript"
    elif re.fullmatch(r"pip\d*", manager):
        family = "python"
    else:
        family = manager
    explicit = re.match(
        r"^((?:@[\w.-]+/)?[\w.-]+)@(?:git\+)?(?:https?|ssh|git|file)://",
        source, re.I,
    )
    if explicit:
        identity = explicit.group(1)
    else:
        egg = re.search(r"(?:#|&)egg=([\w.-]+)", source)
        if egg:
            identity = egg.group(1)
        else:
            # Strip VCS revision, query and fragment before taking the artifact name.
            location = source.split("#", 1)[0].split("?", 1)[0]
            filename = location.rsplit("/", 1)[-1]
            identity = re.sub(r"(?<=\.git)@[^/]+$", "", filename)
            if not identity or (
                "." not in identity and location.count("/") < 3
            ):
                return None
    return (e.filename.replace("\\", "/"), e.context.heading, family, identity.lower())


def _direct_install_pairs(changes) -> dict[Evidence, Evidence]:
    return _pair_install_changes(changes, _direct_install_identity)


def _manifest_install_key(e: Evidence) -> tuple[str, str | None, str, tuple[str, ...]] | None:
    """Pair project installs across managers without inventing package targets."""
    if e.kind != "shell_command" or "EXT-004" not in e.rule_ids:
        return None
    try:
        parts = shlex.split(e.raw_text)
    except ValueError:
        return None
    if len(parts) < 2:
        return None
    manager = parts[0].lower()
    if manager in {"npm", "bun", "pnpm", "yarn"}:
        kind = "javascript-project"
    elif re.fullmatch(r"pip\d*", manager):
        # A Python local-project install should not be equated with JS installs.
        kind = "python-project"
    else:
        return None
    return (e.filename.replace("\\", "/"), e.context.heading, kind,
            _workspace_scope(e) if kind == "javascript-project" else ())


def _manifest_install_pairs(changes) -> dict[Evidence, Evidence]:
    return _pair_install_changes(changes, _manifest_install_key, allow_scope_change=True)


def _source_change(e: Evidence) -> str | None:
    """Fingerprint explicit registry, direct URL, and local project inputs."""
    if not INSTALL_PATTERN.search(e.raw_text):
        return None
    sources = [match.group("option").lower() + "=" +
               match.group("value").strip("\"'") for match in _INSTALL_SOURCE.finditer(e.raw_text)]
    sources.extend("direct=" + direct for direct in _direct_install_sources(e))
    if "EXT-004" in e.rule_ids and re.match(r"^pip\d*\s+install\b", e.raw_text, re.I):
        try:
            arguments = shlex.split(e.raw_text)[2:]
        except ValueError:
            arguments = []
        for index, argument in enumerate(arguments):
            if (argument in {"-r", "--requirement", "-e", "--editable"}
                    and index + 1 < len(arguments)):
                source = "requirements" if argument in {"-r", "--requirement"} else "project"
                sources.append(source + "=" + arguments[index + 1])
                break
            if re.match(r"^-(?:r|e)\S+", argument):
                sources.append(("requirements" if argument[1] == "r" else "project") +
                               "=" + argument[2:])
                break
        else:
            for argument in arguments:
                if argument in {".", ".."} or argument.startswith(("./", "../")):
                    sources.append("project=" + argument)
                    break
    return "|".join(sorted(set(sources))) or None


