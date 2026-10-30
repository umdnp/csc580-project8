#!/usr/bin/env python3
"""Create the Sprint 3 epic/story hierarchy in GitHub.

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
MILESTONE_TITLE = "Sprint 3"
MILESTONE_DUE_ON = "2026-11-18T23:59:59Z"
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
        return f"<!-- sprint3-backlog:{self.key} -->"

    def body(self) -> str:
        lines = [self.marker, "", self.summary]
        if self.estimate is not None:
            lines.extend(["", f"**Estimate:** {self.estimate} points", "", "**This story is complete when:**", ""])
            lines.extend(f"- [ ] {task}" for task in self.checklist)
        return "\n".join(lines)


BACKLOG = (
    BacklogItem(
        "V",
        "[Epic 9] Complete validation and error analysis",
        "epic",
        "We need to finish the manual validation started in Sprint 2, evaluate the errors, and correct problems supported by the evidence.",
    ),
    BacklogItem(
        "A",
        "[Epic 10] Finalize our research results",
        "epic",
        "We need to complete the analysis, check how sensitive the findings are to our comparison and sample choices, and produce final reproducible evidence.",
    ),
    BacklogItem(
        "R",
        "[Epic 11] Complete the research report and reproducibility",
        "epic",
        "We need to finish the report, explain the limitations, and make sure another user can reproduce our main results.",
    ),
    BacklogItem(
        "G",
        "[Epic 12] Prepare the Sprint 3 release and demonstration",
        "epic",
        "We need to prepare the research artifacts and presentation, complete the Sprint 3 review, and document what we learned.",
    ),
    BacklogItem(
        "V1",
        "[Story 9.1] Confirm the final research sample and validation scope",
        "story",
        "I need to establish which data and analysis settings we will use for our final results and manual validation.",
        (
            "I confirmed the 30-family Sprint 2 cohort and recorded its selection rationale and approval status.",
            "I recorded the dataset version, family list, similarity policy, edge setting, random seed, and code revision for the baseline analysis.",
            "I preserved the existing Sprint 2 outputs and review samples before making further changes.",
            "I confirmed which validation samples and review criteria will be used for the final evaluation.",
            "I documented any changes to the sample or analysis scope and why they were necessary.",
        ),
        3,
        "V",
    ),
    BacklogItem(
        "V2",
        "[Story 9.2] Complete independent manual validation",
        "story",
        "I need to finish reviewing the validation samples and record agreed judgments about our relationships and security findings.",
        (
            "I completed independent reviews of the saved directed-pair and relationship-pair validation samples.",
            "I checked the source artifacts and recorded relatedness, direction, coverage, and risk-indicator judgments where applicable.",
            "I included flagged, unflagged, incomplete, and uncertain cases instead of reviewing only positive findings.",
            "I resolved reviewer disagreements or recorded cases that could not be assessed reliably.",
            "I saved the completed adjudicated annotations using the existing validation protocol.",
            "I verified that the annotations match the frozen sample and analysis settings.",
        ),
        5,
        "V",
    ),
    BacklogItem(
        "V3",
        "[Story 9.3] Evaluate validation results and correct confirmed defects",
        "story",
        "I need to evaluate the validation evidence, explain the errors, and fix problems that affect our results.",
        (
            "I generated the supported validation counts and metrics from the completed annotations.",
            "I identified false positives, missed detections, uncertain cases, and recurring failure modes.",
            "I documented manually inspected examples that explain important findings and errors.",
            "I corrected confirmed defects affecting our results, added regression tests, and documented any unresolved issues.",
            "I reran affected analysis steps when a fix changed the reported results.",
            "I documented remaining limitations and the effect of validation on our conclusions.",
        ),
        3,
        "V",
    ),
    BacklogItem(
        "A1",
        "[Story 10.1] Complete the final research analysis",
        "story",
        "I need to produce the final results for our research question using the reviewed method and documented sample.",
        (
            "I retained the 30-family analysis as our baseline and recorded any changes from Sprint 2.",
            "I ran the finalized pipeline and reported the artifacts, relationships, and directed comparisons analyzed.",
            "I summarized introduced or changed security-sensitive behavior by risk indicator and family.",
            "I reported incomplete, ambiguous, or excluded comparisons separately where appropriate.",
            "I incorporated the validation findings and distinguished detected indicators from confirmed security incidents.",
            "I saved results with the settings and source information needed to reproduce them.",
        ),
        3,
        "A",
    ),
    BacklogItem(
        "A2",
        "[Story 10.2] Test primary-edge scanning and random family samples",
        "story",
        "I need to check whether primary-edge scanning is faster and whether a random sample changes our findings without expanding the implementation unnecessarily.",
        (
            "I benchmarked primary-only and all-directed-edge scanning on the same 30 families and recorded their execution times.",
            "I compared risk-indicator coverage by family, indicator type, and directed comparison, and explained the tradeoffs.",
            "I recorded whether primary-only scanning offered enough benefit to use for the additional analysis.",
            "If primary-only scanning was worthwhile, I selected 100 eligible families at random using documented criteria and a saved seed, reusing `family_picker` logic if practical and not selecting for detected indicators.",
            "If the 100-family run was feasible, I analyzed that sample using primary edges and saved the selected families and results.",
            "I ran two additional seeded 100-family samples if time and runtime allowed, or documented why we stopped after the first.",
            "I compared the completed random-sample runs using family-level and comparison-level measures, reporting averages and variation only when supported.",
        ),
        5,
        "A",
    ),
    BacklogItem(
        "A3",
        "[Story 10.3] Generate final reproducible tables and figures",
        "story",
        "I need to generate the final tables and figures that support our results and make them reproducible.",
        (
            "I generated tables for the final sample, directed comparisons, risk indicators, and validation results.",
            "I included the primary-versus-all-edge comparison and random-sample findings where available.",
            "I generated final figures using the repository pipeline rather than manually edited data.",
            "I included sample sizes, denominators, and labels needed to interpret the evidence.",
            "I saved the outputs under the appropriate results and figures directories.",
            "I verified that the report's figures and tables agree with the generated results.",
        ),
        3,
        "A",
    ),
    BacklogItem(
        "R1",
        "[Story 11.1] Complete the research report",
        "story",
        "I need to finish our research report using the final results, validation evidence, and documented method.",
        (
            "I updated the background, research question, dataset, method, and implementation sections where needed.",
            "I incorporated the final results, validation evidence, robustness checks, and generated figures.",
            "I explained competing interpretations and the implications of our findings.",
            "I completed the discussion, related work, conclusion, and future-work sections.",
            "I reviewed citations, references, and report appendices for accuracy and completeness.",
            "I generated a complete draft and separated observed results from our interpretation.",
        ),
        5,
        "R",
    ),
    BacklogItem(
        "R2",
        "[Story 11.2] Finalize threats to validity and limitations",
        "story",
        "I need to explain the limits of our evidence and how they affect the conclusions we can draw.",
        (
            "I documented selection bias from the purposeful cohort and any limits of the random family samples.",
            "I described measurement error, false positives, missed detections, and incomplete source evidence.",
            "I explained uncertainty in artifact relatedness, direction, and historical provenance.",
            "I discussed confounding, alternative explanations, and dependence among comparisons from the same families.",
            "I addressed reproducibility and whether the results can be generalized beyond the analyzed samples.",
            "I updated `THREATS_TO_VALIDITY.md` and the corresponding report section.",
        ),
        3,
        "R",
    ),
    BacklogItem(
        "R3",
        "[Story 11.3] Verify end-to-end reproducibility",
        "story",
        "I need to confirm that a new user can follow our instructions and reproduce the primary results.",
        (
            "I updated `README.md` with setup, dataset preparation, execution, and output instructions.",
            "I verified the documented dependency installation and pipeline steps from a clean environment or equivalent check.",
            "I regenerated the primary results, tables, and figures using the documented configuration.",
            "I verified that the research report builds from its committed sources.",
            "I documented any remaining requirements, external dependencies, or reproducibility limits.",
        ),
        3,
        "R",
    ),
    BacklogItem(
        "G1",
        "[Story 12.1] Prepare the documented Sprint 3 release",
        "story",
        "I need to prepare a traceable repository version containing our completed Sprint 3 research artifacts.",
        (
            "I confirmed that the code, tests, results, figures, report sources, and required documentation are committed.",
            "I linked major work to issues, commits, pull requests, or documented research decisions.",
            "I checked that published outputs do not expose credentials or unsafe dataset content.",
            "I reviewed the AI-use log and recorded team contributions for Sprint 3.",
            "I created a documented Sprint 3 Git tag or release with its contents and known limitations.",
        ),
        2,
        "G",
    ),
    BacklogItem(
        "G2",
        "[Story 12.2] Prepare the final demonstration and presentation",
        "story",
        "I need to prepare a clear demonstration of our research question, method, results, and limitations.",
        (
            "I created presentation materials covering our research question, motivation, and dataset.",
            "I explained the artifact comparison and security-analysis pipeline.",
            "I selected representative examples and prepared a working demonstration of the implementation.",
            "I included the final results, validation evidence, sensitivity checks, and supporting figures.",
            "I explained the main limitations without treating risk indicators as confirmed vulnerabilities.",
            "I assigned presentation responsibilities and rehearsed the demonstration.",
        ),
        3,
        "G",
    ),
    BacklogItem(
        "G3",
        "[Story 12.3] Complete Sprint 3 review and retrospective",
        "story",
        "I need to document our Sprint 3 process, review the completed work, and identify improvements for the final submission.",
        (
            "I created the `Sprint 3` milestone and added the backlog to our GitHub Project.",
            "I assigned story owners, estimates, statuses, and iterations.",
            "I recorded planning, progress check-ins, decisions, and blockers under `docs/meeting-notes/`.",
            "I linked major work to reviewed pull requests where appropriate.",
            "I documented the Sprint 3 review and checked the deliverables against the assignment.",
            "I completed the retrospective and identified our most important process improvement.",
            "I recorded work remaining for the November 30–December 4 finalization and presentation period.",
        ),
        3,
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
                "User-Agent": "sprint3-backlog-importer",
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
                "description": "Sprint 3: analysis, integration, and communication",
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
    parser = argparse.ArgumentParser(description="Import the CSC 580 Sprint 3 backlog into GitHub.")
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
    print(f"Milestone:  {MILESTONE_TITLE} ({milestone_status}; due November 18, 2026)")
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
    print(f"Created or reused {len(BACKLOG)} issues: 4 epics and 12 story sub-issues.")
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
