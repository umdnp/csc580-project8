"""Export a GitHub Project backlog to a Markdown table.

The exporter reads issues from a GitHub Project, keeps only issues belonging to
the requested repository, and writes them in this order:

    Epic
        Story
            Task
        Story
            Task

Epic and story ordering comes from titles such as ``[Epic 1]`` and
``[Story 1.2]``. Issues that do not follow that naming convention are written
at the bottom in creation order. Story checklist items are exported as tasks.

The table also includes each issue's Estimate, assignees, Status, and Iteration
from the GitHub Project.

USAGE
-----

    python export_backlog.py \
        --repo umdnp/csc580-project8 \
        --project-owner umdnp \
        --project-number 4

Optional output file:

    python export_backlog.py \
        --repo umdnp/csc580-project8 \
        --project-owner umdnp \
        --project-number 4 \
        --output docs/backlog.md

Authentication is read from GH_TOKEN, GITHUB_TOKEN, or the current ``gh auth``
session. The default output file is ``backlog.md``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# Project field names expected by this repository.
DEFAULT_OUTPUT = "backlog.md"

ESTIMATE_FIELD = "Estimate"
STATUS_FIELD = "Status"
ITERATION_FIELD = "Iteration"

API_ROOT = "https://api.github.com"
GRAPHQL_URL = f"{API_ROOT}/graphql"
API_VERSION = "2026-03-10"

EPIC_RE = re.compile(r"^\[Epic\s+(\d+)\]\s+(.+)$", re.IGNORECASE)
STORY_RE = re.compile(r"^\[Story\s+(\d+(?:\.\d+)+)\]\s+(.+)$", re.IGNORECASE)
TASK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.+?)\s*$")


# -----------------------------------------------------------------------------
# Data models and GitHub API access
# -----------------------------------------------------------------------------

class GitHubError(RuntimeError):
    """Raised when GitHub access or project retrieval fails."""

    pass


@dataclass
class Task:
    """A Markdown checklist task extracted from an issue body."""

    text: str
    checked: bool


@dataclass
class IssueItem:
    """An issue plus the GitHub Project fields needed for the export."""

    number: int
    title: str
    body: str
    url: str
    created_at: str
    assignees: list[str]
    estimate: str = "—"
    status: str = "—"
    iteration: str = "—"
    tasks: list[Task] = field(default_factory=list)
    parent_number: int | None = None
    epic_number: int | None = None
    story_parts: tuple[int, ...] | None = None

    @property
    def kind(self) -> str:
        """Return the issue type inferred from its title."""
        if self.epic_number is not None:
            return "Epic"
        if self.story_parts is not None:
            return "Story"
        return "Issue"


class GitHubClient:
    """Small GitHub REST/GraphQL client used by the exporter."""

    def __init__(self, token: str, repository: str):
        """Create a client for the requested OWNER/REPOSITORY."""
        self.token = token
        self.repository = repository
        try:
            self.owner, self.repo = repository.split("/", 1)
        except ValueError as exc:
            raise GitHubError("--repo must use OWNER/REPOSITORY format") from exc

    def request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        *,
        allow_404: bool = False,
    ) -> Any:
        """Send one authenticated request to the GitHub API."""
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "csc580-backlog-exporter",
                "X-GitHub-Api-Version": API_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if allow_404 and exc.code == 404:
                return None
            try:
                detail = json.loads(raw).get("message", raw)
            except json.JSONDecodeError:
                detail = raw
            raise GitHubError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(
                f"Could not connect to GitHub while requesting {url}: {exc.reason}"
            ) from exc

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Run a GraphQL query and surface GraphQL errors as GitHubError."""
        result = self.request(
            "POST",
            GRAPHQL_URL,
            {"query": query, "variables": variables},
        )
        errors = result.get("errors") or []
        if errors:
            messages = "; ".join(error.get("message", "Unknown GraphQL error") for error in errors)
            raise GitHubError(f"GraphQL: {messages}")
        return result["data"]

    def verify_repository(self) -> None:
        """Confirm that the repository exists and is accessible."""
        self.request("GET", f"{API_ROOT}/repos/{self.repository}")

    def get_parent_number(self, issue_number: int) -> int | None:
        """Return the parent issue number for a sub-issue, if one exists."""
        parent = self.request(
            "GET",
            f"{API_ROOT}/repos/{self.repository}/issues/{issue_number}/parent",
            allow_404=True,
        )
        return parent["number"] if parent else None



# -----------------------------------------------------------------------------
# Authentication and command-line arguments
# -----------------------------------------------------------------------------

def get_token() -> str:
    """Read a GitHub token from the environment or the current gh session."""
    for variable in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(variable)
        if token:
            return token

    try:
        result = subprocess.run(
            ["gh", "auth", "token", "--hostname", "github.com"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitHubError("GitHub CLI was not found. Install `gh` or set GH_TOKEN.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "No authenticated GitHub CLI session was found."
        raise GitHubError(f"Could not read the GitHub token: {detail}") from exc

    token = result.stdout.strip()
    if not token:
        raise GitHubError("The GitHub CLI returned an empty authentication token.")
    return token


def parse_args() -> argparse.Namespace:
    """Parse the repository, Project owner/number, and optional output path."""
    parser = argparse.ArgumentParser(
        description="Export a GitHub Project backlog to a hierarchical Markdown table.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  python export_backlog.py \\
    --repo umdnp/csc580-project8 \\
    --project-owner umdnp \\
    --project-number 4

Optional:
  --output docs/backlog.md
""",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in OWNER/REPOSITORY format.",
    )
    parser.add_argument(
        "--project-owner",
        required=True,
        help="User or organization that owns the GitHub Project.",
    )
    parser.add_argument(
        "--project-number",
        type=int,
        required=True,
        help="GitHub Project number.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output Markdown file (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()



# -----------------------------------------------------------------------------
# GitHub Project loading
# -----------------------------------------------------------------------------

def project_query(owner_type: str) -> str:
    """Build the GraphQL query used to read Project items and field values."""
    # One query returns both issue data and the Project-specific fields shown in the export.
    owner_field = "user" if owner_type == "user" else "organization"
    return f"""
    query($login: String!, $number: Int!, $after: String) {{
      {owner_field}(login: $login) {{
        projectV2(number: $number) {{
          id
          title
          url
          items(first: 100, after: $after) {{
            nodes {{
              id
              content {{
                __typename
                ... on Issue {{
                  number
                  title
                  body
                  url
                  createdAt
                  repository {{ nameWithOwner }}
                  assignees(first: 100) {{
                    nodes {{ login }}
                  }}
                }}
              }}
              fieldValues(first: 100) {{
                nodes {{
                  __typename
                  ... on ProjectV2ItemFieldNumberValue {{
                    number
                    field {{
                      ... on ProjectV2Field {{ name }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldSingleSelectValue {{
                    name
                    field {{
                      ... on ProjectV2SingleSelectField {{ name }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldIterationValue {{
                    title
                    field {{
                      ... on ProjectV2IterationField {{ name }}
                    }}
                  }}
                  ... on ProjectV2ItemFieldTextValue {{
                    text
                    field {{
                      ... on ProjectV2Field {{ name }}
                    }}
                  }}
                }}
              }}
            }}
            pageInfo {{ hasNextPage endCursor }}
          }}
        }}
      }}
    }}
    """


def get_project_page(
    client: GitHubClient,
    owner: str,
    number: int,
    owner_type: str,
    after: str | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Read one page of Project items for a user- or organization-owned Project."""
    data = client.graphql(
        project_query(owner_type),
        {"login": owner, "number": number, "after": after},
    )
    owner_data = data.get("user") if owner_type == "user" else data.get("organization")
    project = owner_data and owner_data.get("projectV2")
    if not project:
        return None, None
    return project, project["items"]


def load_project(
    client: GitHubClient,
    owner: str,
    number: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load all Project items, handling pagination and either owner type."""
    last_error: Exception | None = None

    # Projects can be owned by either a GitHub user or organization, so try both forms.
    for owner_type in ("user", "organization"):
        try:
            after: str | None = None
            project_meta: dict[str, Any] | None = None
            all_items: list[dict[str, Any]] = []

            while True:
                project, items = get_project_page(
                    client, owner, number, owner_type, after
                )
                if project is None or items is None:
                    break

                if project_meta is None:
                    project_meta = {
                        "id": project["id"],
                        "title": project["title"],
                        "url": project["url"],
                        "owner_type": owner_type,
                    }

                all_items.extend(items["nodes"])
                page_info = items["pageInfo"]
                if not page_info["hasNextPage"]:
                    return project_meta, all_items
                after = page_info["endCursor"]

        except GitHubError as exc:
            last_error = exc

    if last_error:
        raise GitHubError(
            f"Could not find Project {owner}/{number}. Last error: {last_error}"
        ) from last_error
    raise GitHubError(f"Could not find Project {owner}/{number}.")



# -----------------------------------------------------------------------------
# Project item parsing
# -----------------------------------------------------------------------------

def field_name(node: dict[str, Any]) -> str:
    """Return the name of a GitHub Project field-value node."""
    field_data = node.get("field") or {}
    return (field_data.get("name") or "").strip()


def format_number(value: float | int | None) -> str:
    """Format a numeric Project field without unnecessary decimal places."""
    if value is None:
        return "—"
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def project_field_value(
    field_values: list[dict[str, Any]],
    wanted_name: str,
) -> str:
    """Return a named Project field value in display-ready form."""
    wanted = wanted_name.casefold()

    for node in field_values:
        if field_name(node).casefold() != wanted:
            continue

        typename = node.get("__typename")
        if typename == "ProjectV2ItemFieldNumberValue":
            return format_number(node.get("number"))
        if typename == "ProjectV2ItemFieldSingleSelectValue":
            return node.get("name") or "—"
        if typename == "ProjectV2ItemFieldIterationValue":
            return node.get("title") or "—"
        if typename == "ProjectV2ItemFieldTextValue":
            return node.get("text") or "—"

    return "—"


def parse_tasks(body: str) -> list[Task]:
    """Extract checked and unchecked Markdown checklist items from an issue body."""
    tasks: list[Task] = []
    for line in (body or "").splitlines():
        match = TASK_RE.match(line)
        if not match:
            continue
        tasks.append(
            Task(
                text=match.group(2).strip(),
                checked=match.group(1).lower() == "x",
            )
        )
    return tasks


def parse_issue(
    item: dict[str, Any],
    *,
    estimate_field: str,
    status_field: str,
    iteration_field: str,
) -> IssueItem | None:
    """Convert one GitHub Project item into the normalized issue model."""
    content = item.get("content")
    if not content or content.get("__typename") != "Issue":
        return None

    values = item.get("fieldValues", {}).get("nodes", [])
    values = [value for value in values if value]

    assignees = [
        node["login"]
        for node in content.get("assignees", {}).get("nodes", [])
        if node and node.get("login")
    ]

    issue = IssueItem(
        number=content["number"],
        title=content["title"],
        body=content.get("body") or "",
        url=content["url"],
        created_at=content["createdAt"],
        assignees=assignees,
        estimate=project_field_value(values, estimate_field),
        status=project_field_value(values, status_field),
        iteration=project_field_value(values, iteration_field),
    )
    issue.tasks = parse_tasks(issue.body)

    epic_match = EPIC_RE.match(issue.title)
    if epic_match:
        issue.epic_number = int(epic_match.group(1))
        return issue

    story_match = STORY_RE.match(issue.title)
    if story_match:
        issue.story_parts = tuple(int(part) for part in story_match.group(1).split("."))
        return issue

    return issue



# -----------------------------------------------------------------------------
# Markdown output
# -----------------------------------------------------------------------------

def escape_cell(value: str) -> str:
    """Escape text so it is safe inside a Markdown table cell."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "<br>")
    )


def issue_link(issue: IssueItem) -> str:
    """Create the Markdown link used for an issue number."""
    return f"[#{issue.number}]({issue.url})"


def assignee_text(issue: IssueItem) -> str:
    """Format all issue assignees for the table."""
    if not issue.assignees:
        return "—"
    return ", ".join(f"@{login}" for login in issue.assignees)


def row(
    item_text: str,
    item_type: str,
    issue: IssueItem | None = None,
) -> str:
    """Render one Markdown table row for an epic, story, issue, or label row."""
    if issue is None:
        values = [
            item_text,
            item_type,
            "—",
            "—",
            "—",
            "—",
            "—",
        ]
    else:
        values = [
            item_text,
            item_type,
            issue_link(issue),
            issue.estimate,
            assignee_text(issue),
            issue.status,
            issue.iteration,
        ]

    return "| " + " | ".join(escape_cell(value) for value in values) + " |"


def task_row(task: Task) -> str:
    """Render one indented checklist task as a Markdown table row."""
    indent = "&nbsp;" * 12
    state = "☑" if task.checked else "☐"
    return row(f"{indent}{state} {task.text}", "Task")


def story_sort_key(issue: IssueItem) -> tuple[int, ...]:
    """Return numeric story parts so Story 1.2 sorts before Story 1.10."""
    return issue.story_parts or (sys.maxsize,)


def render_markdown(
    repository: str,
    project: dict[str, Any],
    issues: list[IssueItem],
) -> str:
    """Build the complete hierarchical Markdown backlog table."""
    # Build the hierarchy from the numbering convention, not from Project display order.
    epics = sorted(
        (issue for issue in issues if issue.epic_number is not None),
        key=lambda issue: issue.epic_number,
    )
    stories = [issue for issue in issues if issue.story_parts is not None]
    ordinary = [
        issue
        for issue in issues
        if issue.epic_number is None and issue.story_parts is None
    ]

    epic_by_number = {issue.epic_number: issue for issue in epics}
    grouped_story_numbers: set[int] = set()

    lines = [
        "# Backlog Export",
        "",
        f"**Repository:** `{repository}`  ",
        f"**Project:** [{project['title']}]({project['url']})  ",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "| Backlog item | Type | Issue | Estimate | Assigned to | Status | Iteration |",
        "| :--- | :--- | :---: | ---: | :--- | :--- | :--- |",
    ]

    for epic in epics:
        lines.append(row(f"**{epic.title}**", "Epic", epic))

        epic_number = epic.epic_number
        matching_stories = sorted(
            (
                story
                for story in stories
                if story.story_parts
                and story.story_parts[0] == epic_number
            ),
            key=story_sort_key,
        )

        for story in matching_stories:
            grouped_story_numbers.add(story.number)
            indent = "&nbsp;" * 4
            lines.append(row(f"{indent}**{story.title}**", "Story", story))
            lines.extend(task_row(task) for task in story.tasks)

    # Anything outside the Epic/Story naming convention is appended by creation date.
    leftovers = [
        story for story in stories if story.number not in grouped_story_numbers
    ]
    leftovers.extend(ordinary)
    leftovers.sort(key=lambda issue: issue.created_at)

    if leftovers:
        lines.append(
            row(
                "**Other project issues**",
                "",
                None,
            )
        )
        for issue in leftovers:
            lines.append(row(issue.title, issue.kind, issue))
            lines.extend(task_row(task) for task in issue.tasks)

    return "\n".join(lines) + "\n"



# -----------------------------------------------------------------------------
# Validation and program entry point
# -----------------------------------------------------------------------------

def validate_parent_links(
    client: GitHubClient,
    issues: list[IssueItem],
) -> None:
    """Warn when Story numbering and GitHub sub-issue parent links disagree."""
    epic_issue_by_number = {
        issue.epic_number: issue
        for issue in issues
        if issue.epic_number is not None
    }

    # The title determines display placement; this check warns if GitHub parent links disagree.
    for story in (issue for issue in issues if issue.story_parts):
        story.parent_number = client.get_parent_number(story.number)
        expected_epic_number = story.story_parts[0]
        expected_epic = epic_issue_by_number.get(expected_epic_number)

        if expected_epic is None:
            print(
                f"Warning: {story.title} has no matching [Epic {expected_epic_number}] "
                "in this project.",
                file=sys.stderr,
            )
            continue

        if story.parent_number is None:
            print(
                f"Warning: {story.title} is not linked as a sub-issue of "
                f"{expected_epic.title}.",
                file=sys.stderr,
            )
        elif story.parent_number != expected_epic.number:
            print(
                f"Warning: {story.title} is linked to issue #{story.parent_number}, "
                f"not expected epic issue #{expected_epic.number}.",
                file=sys.stderr,
            )


def run() -> None:
    """Load the Project, export repository issues, and write the Markdown file."""
    args = parse_args()

    print("Reading GitHub authentication...", flush=True)
    token = get_token()
    client = GitHubClient(token, args.repo)

    print(f"Connecting to GitHub and verifying repository {args.repo}...", flush=True)
    client.verify_repository()
    print("Repository access verified.", flush=True)

    print(
        f"Loading GitHub Project {args.project_owner}/{args.project_number}...",
        flush=True,
    )
    project, raw_items = load_project(
        client,
        args.project_owner,
        args.project_number,
    )
    print(
        f"Loaded project '{project['title']}' with {len(raw_items)} project item(s).",
        flush=True,
    )

    issues: list[IssueItem] = []
    skipped = 0

    for item in raw_items:
        content = item.get("content") or {}
        if content.get("__typename") != "Issue":
            skipped += 1
            continue

        repository = (content.get("repository") or {}).get("nameWithOwner")
        if repository != args.repo:
            continue

        issue = parse_issue(
            item,
            estimate_field=ESTIMATE_FIELD,
            status_field=STATUS_FIELD,
            iteration_field=ITERATION_FIELD,
        )
        if issue:
            issues.append(issue)

    print(
        f"Checking epic/story relationships for {len(issues)} repository issue(s)...",
        flush=True,
    )
    validate_parent_links(client, issues)

    print("Generating Markdown backlog...", flush=True)
    markdown = render_markdown(args.repo, project, issues)
    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)

    print(f"Project:    {project['title']}")
    print(f"Repository: {args.repo}")
    print(f"Issues:     {len(issues)}")
    if skipped:
        print(f"Skipped:    {skipped} non-issue project item(s)")
    print(f"Output:     {output_path}")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nExport cancelled.", file=sys.stderr)
        raise SystemExit(130)
    except GitHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
