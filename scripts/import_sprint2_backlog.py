#!/usr/bin/env python3
"""Create the Sprint 2 epic/story hierarchy in GitHub.

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
MILESTONE_TITLE = "Sprint 2"
MILESTONE_DUE_ON = "2026-10-28T23:59:59Z"
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
        return f"<!-- sprint2-backlog:{self.key} -->"

    def body(self) -> str:
        lines = [self.marker, "", self.summary]
        if self.estimate is not None:
            lines.extend(["", f"**Estimate:** {self.estimate} points", "", "**This story is complete when:**", ""])
            lines.extend(f"- [ ] {task}" for task in self.checklist)
        return "\n".join(lines)


BACKLOG = (
    BacklogItem(
        "A",
        "[Epic 5] Complete the core analysis method",
        "epic",
        "We need to complete the core comparison and security analysis methods and run them together as a reproducible end-to-end workflow.",
    ),
    BacklogItem(
        "V",
        "[Epic 6] Test and validate the analysis method",
        "epic",
        "We need to test the important parts of the method and validate the results so we can explain why they should be trusted and where they may fail.",
    ),
    BacklogItem(
        "P",
        "[Epic 7] Produce preliminary results",
        "epic",
        "We need to run the completed method on the approved sample and produce reproducible preliminary evidence for our research question.",
    ),
    BacklogItem(
        "R",
        "[Epic 8] Complete the Sprint 2 research package",
        "epic",
        "We need to update the research artifacts, manage the Sprint 2 repository work, complete peer review, and document what we learned.",
    ),
    BacklogItem(
        "A1",
        "[Story 5.1] Complete the artifact comparison method",
        "story",
        "I need to complete the method for identifying and comparing related artifacts.",
        (
            "I identified artifacts that are candidates for comparison.",
            "I determined whether candidate artifacts are sufficiently related to compare.",
            "I retained the information needed to trace each comparison to its source artifacts.",
            "I handled artifacts that cannot be reliably compared.",
            "I added tests for the important comparison functions.",
            "I documented how to run the comparison method on the approved sample.",
        ),
        5,
        "A",
    ),
    BacklogItem(
        "A2",
        "[Story 5.2] Complete the security analysis method",
        "story",
        "I need to complete the method for detecting and recording the security-sensitive behavior in our threat model.",
        (
            "I completed the detection rules for our threat categories.",
            "I recorded the rule, category, match count, and evidence for detected signals.",
            "I handled missing or malformed content without stopping the analysis.",
            "I confirmed that dataset content is never executed.",
            "I added tests for the important security-analysis functions.",
            "I documented how to run the security analysis on the approved sample.",
        ),
        5,
        "A",
    ),
    BacklogItem(
        "A3",
        "[Story 5.3] Complete security-change comparisons",
        "story",
        "I need to compare security signals across related artifacts and record the changes supported by the analysis.",
        (
            "I compared security signals across related artifacts.",
            "I identified introduced, removed, and retained security-sensitive behavior where supported.",
            "I recorded evidence for each reported change.",
            "I handled comparisons where change direction cannot be reliably determined.",
            "I added tests for security-change comparisons.",
            "I generated structured comparison output for the analysis pipeline.",
        ),
        5,
        "A",
    ),
    BacklogItem(
        "A4",
        "[Story 5.4] Integrate the end-to-end analysis pipeline",
        "story",
        "I need to connect the core analysis steps into one reproducible workflow.",
        (
            "I documented the approved Sprint 2 sample.",
            "I connected data loading, extraction, comparison, security analysis, and result generation.",
            "I ran the complete workflow on the approved sample.",
            "I reported or skipped invalid records with a reason.",
            "I verified that results are traceable to source records.",
            "I saved generated results under `results/`.",
            "I documented how to run the complete pipeline.",
            "I reproduced the workflow from a clean environment using the documented instructions.",
        ),
        5,
        "A",
    ),
    BacklogItem(
        "V1",
        "[Story 6.1] Expand automated test coverage",
        "story",
        "I need to expand automated testing across the important functions in our Sprint 2 analysis.",
        (
            "I added tests for important parsing and transformation functions.",
            "I added tests for important matching and comparison functions.",
            "I added tests for important security-analysis functions.",
            "I included positive, negative, and edge cases where appropriate.",
            "I added regression tests for defects found during Sprint 2.",
            "I verified that the full test suite runs using the documented setup.",
        ),
        5,
        "V",
    ),
    BacklogItem(
        "V2",
        "[Story 6.2] Define the validation sample and protocol",
        "story",
        "I need to define a repeatable manual validation process and representative sample.",
        (
            "I defined how records are selected for manual validation.",
            "I created a sample with representative positive, negative, and ambiguous cases.",
            "I defined the labels or judgments reviewers will record.",
            "I documented instructions for reviewing each validation item.",
            "I defined how disagreements or uncertain cases will be recorded.",
            "I stored the validation sample and protocol in the repository.",
        ),
        3,
        "V",
    ),
    BacklogItem(
        "V3",
        "[Story 6.3] Perform manual validation",
        "story",
        "I need to manually review the validation sample and compare it with the pipeline results.",
        (
            "I manually reviewed the selected validation sample.",
            "I recorded the expected result for each reviewed item.",
            "I compared manual judgments with the comparison and security-analysis results.",
            "I recorded false positives, false negatives, and ambiguous cases.",
            "I preserved representative examples for the report.",
            "I saved the completed validation results in the repository.",
        ),
        3,
        "V",
    ),
    BacklogItem(
        "V4",
        "[Story 6.4] Evaluate validation results and limitations",
        "story",
        "I need to evaluate the validation evidence and document where the method may fail.",
        (
            "I summarized the validation results using appropriate counts or metrics.",
            "I identified the main failure modes found during validation.",
            "I documented likely causes of false positives and false negatives.",
            "I updated the method where supported by validation evidence.",
            "I documented remaining limitations in `THREATS_TO_VALIDITY.md`.",
            "I recorded significant changes to the method or scope.",
        ),
        3,
        "V",
    ),
    BacklogItem(
        "P1",
        "[Story 7.1] Generate preliminary analysis results",
        "story",
        "I need to run the completed analysis and summarize preliminary evidence for our research question.",
        (
            "I ran the analysis pipeline on the approved Sprint 2 sample.",
            "I reported the number of artifacts analyzed and excluded.",
            "I summarized detected security signals by threat category.",
            "I summarized the artifact comparisons produced by the analysis.",
            "I summarized security-sensitive changes across comparable artifacts.",
            "I separated observed results from interpretations about risk or intent.",
            "I saved the preliminary results under `results/`.",
        ),
        5,
        "P",
    ),
    BacklogItem(
        "P2",
        "[Story 7.2] Generate reproducible tables and figures",
        "story",
        "I need to generate reproducible preliminary evidence from the analysis output.",
        (
            "I generated at least one preliminary results table.",
            "I generated at least one preliminary figure.",
            "I included the sample sizes and denominators needed to interpret the results.",
            "I saved tables under `results/` and figures under `figures/`.",
            "I documented how to regenerate the tables and figures.",
            "I verified that the evidence can be regenerated without manual editing.",
        ),
        3,
        "P",
    ),
    BacklogItem(
        "R1",
        "[Story 8.1] Update the research report",
        "story",
        "I need to update the research report with our Sprint 2 work and preliminary results.",
        (
            "I updated the background to reflect the current research scope.",
            "I documented the artifact comparison method.",
            "I documented the security analysis and change-detection method.",
            "I documented the implementation and end-to-end pipeline.",
            "I documented the testing and validation approach.",
            "I added the preliminary Sprint 2 results and generated evidence.",
            "I documented important limitations found during Sprint 2.",
            "I separated observed results from interpretation.",
        ),
        5,
        "R",
    ),
    BacklogItem(
        "R2",
        "[Story 8.2] Manage Sprint 2 repository and review requirements",
        "story",
        "I need to keep Sprint 2 work organized, traceable, and properly reviewed in GitHub.",
        (
            "I created the `Sprint 2` milestone and added the Sprint 2 backlog to the GitHub Project.",
            "I assigned each story an owner, estimate, status, iteration, and milestone.",
            "I linked major Sprint 2 work to its story and pull request.",
            "I included purpose, testing, and generated outputs in applicable pull requests.",
            "I had at least one Sprint 2 pull request reviewed by another team member before merging.",
            "I confirmed that Sprint 2 code, tests, results, and research artifacts are committed.",
            "I updated `README.md` where Sprint 2 changed setup, execution, outputs, or project documentation.",
        ),
        3,
        "R",
    ),
    BacklogItem(
        "R3",
        "[Story 8.3] Complete Sprint 2 review and retrospective",
        "story",
        "I need to document our Sprint 2 process, what changed, and what should continue into Sprint 3.",
        (
            "I recorded Sprint 2 planning and progress check-ins under `docs/meeting-notes/`.",
            "I documented the Sprint 2 review.",
            "I documented the Sprint 2 retrospective.",
            "I recorded changes to the research question, method, scope, or interpretation.",
            "I recorded significant decisions, blockers, and unresolved limitations.",
            "I updated `ai-use-log.md` for Sprint 2 work.",
            "I identified work that should continue into Sprint 3.",
            "I updated the Sprint 3 backlog based on Sprint 2 findings.",
        ),
        3,
        "R",
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
                "User-Agent": "sprint2-backlog-importer",
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
                "description": "Sprint 2: implementation and validation",
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
    parser = argparse.ArgumentParser(description="Import the CSC 580 Sprint 2 backlog into GitHub.")
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
    print(f"Milestone:  {MILESTONE_TITLE} ({milestone_status}; due October 28, 2026)")
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
    print(f"Created or reused {len(BACKLOG)} issues: 4 epics and 13 story sub-issues.")
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
