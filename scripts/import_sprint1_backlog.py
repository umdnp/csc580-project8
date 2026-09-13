#!/usr/bin/env python3
"""Create the Sprint 1 epic/story hierarchy in GitHub.

The script uses Python's standard library for GitHub API requests. It obtains an
authentication token from GH_TOKEN, GITHUB_TOKEN, or the current `gh auth`
session. Run with --dry-run first; no third-party Python packages are required.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_REPOSITORY = "umdnp/csc580-project8"
DEFAULT_PROJECT_OWNER = "umdnp"
DEFAULT_PROJECT_NUMBER = 4
MILESTONE_TITLE = "Sprint 1"
MILESTONE_DUE_ON = "2026-10-07T23:59:59Z"
API_ROOT = "https://api.github.com"
GRAPHQL_URL = f"{API_ROOT}/graphql"


@dataclass(frozen=True)
class BacklogItem:
    key: str
    title: str
    label: str
    summary: str
    checklist: tuple[str, ...] = ()
    estimate: int | None = None
    parent_key: str | None = None

    @property
    def marker(self) -> str:
        return f"<!-- sprint1-backlog:{self.key} -->"

    def body(self) -> str:
        lines = [self.marker, "", self.summary]
        if self.estimate is not None:
            lines.extend(["", f"**Estimate:** {self.estimate} points", "", "**This story is complete when:**", ""])
            lines.extend(f"- [ ] {task}" for task in self.checklist)
        return "\n".join(lines)


BACKLOG = (
    BacklogItem(
        "R",
        "[Epic 1] Define our research foundation",
        "epic",
        "We need to agree on exactly what we are studying, what we will measure, and how we will describe the results without overstating what they mean.",
    ),
    BacklogItem(
        "D",
        "[Epic 2] Establish our GitSkills data foundation",
        "epic",
        "We need to obtain the data, find out which comparisons it supports, and create a sample that we can use during Sprint 1.",
    ),
    BacklogItem(
        "P",
        "[Epic 3] Produce our first security result",
        "epic",
        "We need to run a small but complete analysis from the source data through a reproducible result. We do not need to finish the full Sprint 2 analyzer yet.",
    ),
    BacklogItem(
        "G",
        "[Epic 4] Set up our repository and Scrum process",
        "epic",
        "We need to make our work reproducible, reviewable, and easy to follow in GitHub.",
    ),
    BacklogItem(
        "R1",
        "[Story 1.1] Finalize the research question and measures",
        "story",
        "I need to turn Question 4 into a specific research question that we can answer with the available GitSkills data.",
        (
            "I identified Question 4 as our selected MSR-inspired topic in `RESEARCH_QUESTION.md`.",
            "I documented our final research question, motivation, and expected contribution.",
            "I defined the unit of analysis, population, sample, variables, and outcome measures.",
            "I explained that a risk signal is not proof that a skill is malicious or exploitable.",
            "I recorded at least one simpler or competing explanation for the results we might find.",
            "I documented what we will complete in Sprint 1 and what we are leaving for later sprints.",
        ),
        3,
        "R",
    ),
    BacklogItem(
        "R2",
        "[Story 1.2] Define the threat model and initial rule categories",
        "story",
        "I need to define the security-related behaviors we plan to detect and be clear about the limits of those detections.",
        (
            "I defined command execution, file-system access, network access, credential-related instructions, and bundled or invoked scripts in `THREAT_MODEL.md`.",
            "I included at least one example and one likely false positive for each category.",
            "I documented that we will treat the dataset as untrusted and will not execute any commands or scripts from it.",
            "I recorded what our analysis cannot determine and what is outside the scope of this project.",
        ),
        2,
        "R",
    ),
    BacklogItem(
        "D1",
        "[Story 2.1] Acquire and document the GitSkills dataset",
        "story",
        "I need to make the dataset available to our group and document the parts of it that we will use.",
        (
            "I documented how to obtain the data, which version we used, and any access or licensing restrictions in `data/README.md`.",
            "I documented the fields we need, their data types, and short examples in `DATA_DICTIONARY.md`.",
            "I recorded missing or incomplete fields that could affect our research question.",
            "I made sure large or restricted source files are excluded from Git and can be obtained by following our instructions.",
        ),
        3,
        "D",
    ),
    BacklogItem(
        "D2",
        "[Story 2.2] Choose the comparison approach and Sprint 1 sample",
        "story",
        "I need to confirm how we can identify an earlier version or source skill before we spend time building the full analysis.",
        (
            "I checked whether the data supports successive versions, reused source-and-copy pairs, or both.",
            "I selected the simplest comparison approach that the data can support.",
            "I created a small Sprint 1 sample and documented how the records were selected.",
            "I confirmed that the sample contains enough comparable records to run the first pipeline.",
            "If the data is not sufficient, I documented a fallback and got approval before continuing.",
            "I recorded the decision and its limitations under `docs/decisions/`.",
        ),
        2,
        "D",
    ),
    BacklogItem(
        "D3",
        "[Story 2.3] Build the data-loading and extraction pipeline",
        "story",
        "I need to build a repeatable way to load our sample and extract the fields needed for the analysis.",
        (
            "I created a command or documented notebook that loads the sample without executing anything from the dataset.",
            "I extracted the identifiers, content, repository information, and comparison fields needed for Question 4.",
            "I reported or skipped invalid records with a clear reason.",
            "I saved the normalized output as CSV, JSON, or Parquet.",
            "I added setup and run instructions to `README.md`.",
            "I added at least one automated test or fixture that verifies the loader and extraction logic.",
        ),
        5,
        "D",
    ),
    BacklogItem(
        "P1",
        "[Story 3.1] Build a basic risk-signal detector",
        "story",
        "I need to build a small rule-based detector that lets us test the approach on our Sprint 1 sample.",
        (
            "I implemented rules for at least two of our threat categories.",
            "I recorded the artifact, rule, category, and matched text for every finding.",
            "When two artifacts can be compared, I identified whether a signal appears to be newly introduced.",
            "I organized the rules so we can revise or add to them in Sprint 2.",
            "I added a few positive and negative examples that show the rules working as expected.",
            "I confirmed that the detector does not execute commands, run scripts, or open URLs found in the dataset.",
        ),
        5,
        "P",
    ),
    BacklogItem(
        "P2",
        "[Story 3.2] Generate one exploratory result",
        "story",
        "I need to run the Sprint 1 pipeline and create a result that we can show during the sprint review.",
        (
            "I ran the loader, extractor, and basic detector on our approved sample.",
            "I generated at least one table or visualization from code.",
            "I included the sample size and detection counts for the categories we implemented.",
            "I manually checked and annotated at least two findings as examples.",
            "I saved the output under `results/` or `figures/`.",
            "I confirmed that the result can be regenerated by following the instructions in `README.md`.",
        ),
        3,
        "P",
    ),
    BacklogItem(
        "P3",
        "[Story 3.3] Document our initial risks and limitations",
        "story",
        "I need to document the main reasons our first result could be incomplete or misleading.",
        (
            "I documented the main measurement, missing-data, and generalizability concerns in `THREATS_TO_VALIDITY.md`.",
            "I described likely false positives and false negatives.",
            "I identified a Sprint 2 improvement or an explicit limitation for each major risk.",
            "I made sure we describe the findings as static risk signals rather than confirmed vulnerabilities.",
        ),
        2,
        "P",
    ),
    BacklogItem(
        "G1",
        "[Story 4.1] Set up the repository and GitHub Project",
        "story",
        "I need to set up the repository and the minimum GitHub workflow we need for Sprint 1.",
        (
            "I confirmed that everyone who needs access can open the repository.",
            "I created the required folders and root files listed in the assignment.",
            "I documented the dependencies and one clear way to set up and run the project.",
            "I created the `Sprint 1` milestone and the Project views we will use.",
            "I enabled branch protection or documented the equivalent pull-request review process we will follow.",
            "I added all Sprint 1 epics and stories to the Project with an owner, estimate, status, and milestone.",
        ),
        3,
        "G",
    ),
    BacklogItem(
        "G2",
        "[Story 4.2] Complete our Sprint 1 process requirements",
        "story",
        "I need to make sure our planning, progress checks, review, and retrospective are recorded in the repository.",
        (
            "I recorded sprint planning, brief progress check-ins, the sprint review, and the retrospective under `docs/meeting-notes/`.",
            "I linked at least one pull request to a story and had it reviewed by a group member other than the author.",
            "I recorded important scope or design decisions under `docs/decisions/`.",
            "I updated `ai-use-log.md` with how we used AI tools and how we checked the output.",
            "I recorded what we learned during Sprint 1 and what we changed in the Sprint 2 backlog.",
        ),
        2,
        "G",
    ),
)


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str, repository: str):
        self.token = token
        self.repository = repository
        try:
            self.owner, self.repo = repository.split("/", 1)
        except ValueError as exc:
            raise GitHubError("--repo must use the OWNER/REPOSITORY format") from exc

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> Any:
        url = f"{API_ROOT}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "sprint1-backlog-importer",
                "X-GitHub-Api-Version": "2026-03-10",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            if allow_404 and exc.code == 404:
                return None
            try:
                detail = json.loads(raw).get("message", raw)
            except json.JSONDecodeError:
                detail = raw
            raise GitHubError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not connect to GitHub: {exc.reason}") from exc

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = {"query": query, "variables": variables}
        result = self.request("POST", "/graphql", payload)
        if result.get("errors"):
            messages = "; ".join(error.get("message", "Unknown GraphQL error") for error in result["errors"])
            raise GitHubError(f"GraphQL: {messages}")
        return result["data"]

    def verify_repository(self) -> None:
        self.request("GET", f"/repos/{self.repository}")

    def verify_labels(self) -> None:
        labels: set[str] = set()
        page = 1
        while True:
            batch = self.request(
                "GET",
                f"/repos/{self.repository}/labels",
                query={"per_page": 100, "page": page},
            )
            labels.update(label["name"] for label in batch)
            if len(batch) < 100:
                break
            page += 1
        missing = {"epic", "story"} - labels
        if missing:
            names = ", ".join(sorted(missing))
            raise GitHubError(f"Create the following repository label(s), then rerun the script: {names}")

    def find_milestone(self) -> dict[str, Any] | None:
        page = 1
        while True:
            batch = self.request(
                "GET",
                f"/repos/{self.repository}/milestones",
                query={"state": "all", "per_page": 100, "page": page},
            )
            for milestone in batch:
                if milestone["title"] == MILESTONE_TITLE:
                    return milestone
            if len(batch) < 100:
                return None
            page += 1

    def create_milestone(self) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/repos/{self.repository}/milestones",
            {
                "title": MILESTONE_TITLE,
                "description": "Sprint 1: research framing and data foundation",
                "due_on": MILESTONE_DUE_ON,
            },
        )

    def marker_issues(self) -> dict[str, dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        page = 1
        while True:
            batch = self.request(
                "GET",
                f"/repos/{self.repository}/issues",
                query={"state": "all", "per_page": 100, "page": page},
            )
            for issue in batch:
                if "pull_request" in issue:
                    continue
                body = issue.get("body") or ""
                for item in BACKLOG:
                    if item.marker in body:
                        if item.key in found:
                            raise GitHubError(f"More than one issue contains the backlog marker for {item.key}.")
                        found[item.key] = issue
            if len(batch) < 100:
                return found
            page += 1

    def create_issue(self, item: BacklogItem, milestone_number: int) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/repos/{self.repository}/issues",
            {
                "title": item.title,
                "body": item.body(),
                "labels": [item.label],
                "milestone": milestone_number,
            },
        )

    def ensure_issue_metadata(
        self, issue: dict[str, Any], item: BacklogItem, milestone_number: int
    ) -> dict[str, Any]:
        if issue["state"] != "open":
            raise GitHubError(
                f"Existing backlog issue #{issue['number']} ({item.key}) is closed. "
                "Reopen or delete it before rerunning the importer."
            )
        labels = {label["name"] for label in issue.get("labels", [])}
        milestone = issue.get("milestone")
        correct_milestone = milestone and milestone["number"] == milestone_number
        correct_title = issue["title"] == item.title
        if item.label in labels and correct_milestone and correct_title:
            return issue
        labels.add(item.label)
        return self.request(
            "PATCH",
            f"/repos/{self.repository}/issues/{issue['number']}",
            {
                "title": item.title,
                "labels": sorted(labels),
                "milestone": milestone_number,
            },
        )

    def get_parent(self, child_number: int) -> dict[str, Any] | None:
        return self.request(
            "GET",
            f"/repos/{self.repository}/issues/{child_number}/parent",
            allow_404=True,
        )

    def link_sub_issue(
        self,
        parent_number: int,
        child_database_id: int,
        *,
        replace_parent: bool = False,
    ) -> None:
        self.request(
            "POST",
            f"/repos/{self.repository}/issues/{parent_number}/sub_issues",
            {
                "sub_issue_id": child_database_id,
                "replace_parent": replace_parent,
            },
        )

    def project_and_items(self, login: str, number: int) -> tuple[str, str, set[str]]:
        query = """
        query($login: String!, $number: Int!, $after: String) {
          user(login: $login) {
            projectV2(number: $number) {
              id
              title
              items(first: 100, after: $after) {
                nodes {
                  content {
                    ... on Issue { id url }
                  }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
        """
        after: str | None = None
        project_id = ""
        project_title = ""
        issue_node_ids: set[str] = set()
        while True:
            data = self.graphql(query, {"login": login, "number": number, "after": after})
            user = data.get("user")
            project = user and user.get("projectV2")
            if not project:
                raise GitHubError(f"Could not find user Project {login}/{number}.")
            project_id = project["id"]
            project_title = project["title"]
            items = project["items"]
            for node in items["nodes"]:
                content = node.get("content")
                if content and content.get("id"):
                    issue_node_ids.add(content["id"])
            page_info = items["pageInfo"]
            if not page_info["hasNextPage"]:
                return project_id, project_title, issue_node_ids
            after = page_info["endCursor"]

    def add_to_project(self, project_id: str, issue_node_id: str) -> bool:
        mutation = """
        mutation($project: ID!, $content: ID!) {
          addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
            item { id }
          }
        }
        """
        payload = {
            "query": mutation,
            "variables": {"project": project_id, "content": issue_node_id},
        }
        result = self.request("POST", "/graphql", payload)
        errors = result.get("errors") or []
        if not errors:
            return True
        messages = "; ".join(error.get("message", "Unknown GraphQL error") for error in errors)
        if "already exists in this project" in messages.lower():
            return False
        raise GitHubError(f"GraphQL: {messages}")


def get_token() -> str:
    for variable in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(variable):
            return os.environ[variable]
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
    parser = argparse.ArgumentParser(description="Import the CSC 580 Sprint 1 backlog into GitHub.")
    parser.add_argument("--repo", default=os.environ.get("GH_REPO", DEFAULT_REPOSITORY))
    parser.add_argument("--project-owner", default=DEFAULT_PROJECT_OWNER)
    parser.add_argument("--project-number", type=int, default=DEFAULT_PROJECT_NUMBER)
    parser.add_argument("--dry-run", action="store_true", help="Validate access and show the plan without changing GitHub.")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    return parser.parse_args()


def print_plan(args: argparse.Namespace, project_title: str, milestone: dict[str, Any] | None) -> None:
    epics = sum(item.label == "epic" for item in BACKLOG)
    stories = sum(item.label == "story" for item in BACKLOG)
    milestone_status = "reuse existing" if milestone else "create"
    print(f"Repository: {args.repo}")
    print(f"Project:    {project_title} (https://github.com/users/{args.project_owner}/projects/{args.project_number})")
    print(f"Milestone:  {MILESTONE_TITLE} ({milestone_status}; due October 7, 2026)")
    print(f"Issues:     {epics} epics and {stories} story sub-issues")
    print("Tasks:      Markdown checklists inside story descriptions")
    print("Labels:     epic and story (checklist items cannot receive the task label)")


def run() -> None:
    args = parse_args()
    token = get_token()
    client = GitHubClient(token, args.repo)

    client.verify_repository()
    client.verify_labels()
    milestone = client.find_milestone()
    if milestone and milestone["state"] != "open":
        raise GitHubError(f"The existing {MILESTONE_TITLE} milestone is closed. Reopen it before importing.")
    project_id, project_title, project_items = client.project_and_items(
        args.project_owner, args.project_number
    )
    existing = client.marker_issues()

    print_plan(args, project_title, milestone)
    if existing:
        print(f"Existing:   {len(existing)} marked backlog issue(s) will be reused")

    if args.dry_run:
        print("\nDry run completed. No GitHub data was changed.")
        return

    if not args.yes:
        answer = input("\nContinue with the import? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Import cancelled.")
            return

    if milestone is None:
        milestone = client.create_milestone()
        print(f"\nCreated milestone: {MILESTONE_TITLE}")
    else:
        print(f"\nUsing existing milestone: {MILESTONE_TITLE}")

    issues: dict[str, dict[str, Any]] = {}
    for item in BACKLOG:
        if item.parent_key is not None:
            continue
        issue = existing.get(item.key)
        if issue:
            issue = client.ensure_issue_metadata(issue, item, milestone["number"])
            print(f"Using existing epic: {issue['html_url']}")
        else:
            issue = client.create_issue(item, milestone["number"])
            print(f"Created epic: {issue['html_url']}")
        issues[item.key] = issue
        if issue["node_id"] in project_items:
            print(f"  Already in project: {issue['html_url']}")
        else:
            added = client.add_to_project(project_id, issue["node_id"])
            project_items.add(issue["node_id"])
            action = "Added to project" if added else "Already in project (auto-added)"
            print(f"  {action}: {issue['html_url']}")

    for item in BACKLOG:
        if item.parent_key is None:
            continue
        issue = existing.get(item.key)
        if issue:
            issue = client.ensure_issue_metadata(issue, item, milestone["number"])
            print(f"Using existing story: {issue['html_url']}")
        else:
            issue = client.create_issue(item, milestone["number"])
            print(f"Created story: {issue['html_url']}")
        issues[item.key] = issue

        parent = issues[item.parent_key]
        current_parent = client.get_parent(issue["number"])
        if current_parent is None:
            client.link_sub_issue(parent["number"], issue["id"])
            print(f"  Linked under epic #{parent['number']}")
        elif current_parent["number"] == parent["number"]:
            print(f"  Already linked under epic #{parent['number']}")
        else:
            old_parent_number = current_parent["number"]
            client.link_sub_issue(
                parent["number"],
                issue["id"],
                replace_parent=True,
            )
            print(
                f"  Moved from old epic #{old_parent_number} "
                f"to epic #{parent['number']}"
            )

        if issue["node_id"] in project_items:
            print(f"  Already in project: {issue['html_url']}")
        else:
            added = client.add_to_project(project_id, issue["node_id"])
            project_items.add(issue["node_id"])
            action = "Added to project" if added else "Already in project (auto-added)"
            print(f"  {action}: {issue['html_url']}")

    print("\nImport completed successfully.")
    print(f"Created or reused {len(BACKLOG)} issues: 4 epics and 10 story sub-issues.")
    print("Next: assign story owners and set any Project fields such as Status or Estimate.")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nImport cancelled.", file=sys.stderr)
        raise SystemExit(130)
    except GitHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
