# CSC 580 Group 8 – Meeting Minutes

**Date:** October 11, 2026  
**Time:** 2:00 PM ET / 1:00 PM CT  
**Duration:** Approximately 57 minutes  
**Attendees:** Jim Prantzalos, Vaisnavii Mohanraj, Kyle Cantrell, Christian Heiney  
**Purpose:** Review Sprint 2 stories and dependencies, clarify team assignments, discuss scanner and validation refinements, and identify work needed for the Sprint 2 analysis and report.

## Main Topics of Discussion

- Vaisnavii facilitated the meeting and led the team through the Sprint 2 backlog.
  - Team members reviewed each story, current progress, dependencies, and assigned work.
  - Assignees were encouraged to raise concerns if a story was unclear or did not fit their expected workload.

- Reviewed the **artifact comparison and lineage work**.
  - The comparison process depends on identifying a reasonable base artifact and derived artifact before running the security scan.
  - The methodology for ordering related artifacts and determining likely progression is already documented in the project's RDRs.
  - Much of this work was completed during Sprint 1.
  - Remaining work primarily involves confirming test coverage, representative samples, and method documentation.

- Reviewed the **Sprint 2 scanner refinement work**.
  - Sprint 1 detection primarily identified the presence and count of matched command or behavior patterns.
  - Sprint 2 needs to capture additional **evidentiary information** so meaningful changes can be identified even when the same command appears in both artifacts.
  - Examples include:
    - A `curl` command remaining present while its target URL changes.
    - A URL remaining present while its path or other security-sensitive value changes.
    - Commands being replaced by different commands that happen to produce the same rule-match count.
  - The scanner should therefore preserve enough matched content or parameters to explain what changed between the base and derived artifacts.

- Reviewed additions Kyle has already made to the scanner rules.
  - Additional package-manager commands were added after manual review identified tools such as `bun`.
  - Windows/PowerShell equivalents were added for behaviors previously covered primarily by Linux-oriented commands, including `Invoke-WebRequest`.
  - A new file-system rule was added for **read access**, which had not been represented in the original rule set.
  - Kyle also ran the current rules against the larger set of candidate artifact pairs and produced Parquet/CSV outputs for further inspection.
  - The expanded scan results can be used to help identify representative validation samples and additional rule gaps.

- Reaffirmed the need for **team-wide manual inspection of GitSkills artifacts**.
  - All team members should review actual `SKILL.md` content and identify security-sensitive behaviors that the current scanner may not detect.
  - Potential gaps should be raised in Discord for discussion before new rules are added.
  - Manual inspection will help determine whether the scanner is sufficiently broad without continually expanding rules based only on hypothetical cases.

- Reviewed Vaisnavii's **Sprint 2 analysis-pipeline story**.
  - The Sprint 2 pipeline will build on the Sprint 1 approach but use the Sprint 2 sample and refined scanner.
  - This work depends on completion of the preceding scanner and sample-selection work.
  - Vaisnavii will attempt to use the shared `GITSKILLS_DB` environment-variable approach on macOS so the notebook remains portable across team members' environments.
  - If necessary, the team will help resolve platform-specific setup issues rather than maintaining separate notebook implementations.

- Reviewed the **automated-testing work**.
  - Kyle has added `pytest` support to the repository and has already added several tests.
  - Tests can be run across the repository with `uv run pytest`.
  - Additional test coverage will be added as the refined scanner and analysis outputs stabilize.

- Discussed **story dependencies in GitHub Projects**.
  - Several Sprint 2 stories cannot be completed until scanner, sample-selection, or analysis work is available.
  - The team discovered that GitHub issue relationships can represent stories as **blocked by** other issues.
  - These relationships will be used where helpful to make the expected work sequence more visible.
  - A temporary issue occurred when changing one relationship caused a sub-issue to appear as a top-level issue; Jim will review the GitHub Project configuration and correct it.

- Reviewed Christian's **validation-sample and protocol work**.
  - Christian is still becoming familiar with the Sprint 1 project artifacts, repository terminology, and local development environment.
  - The validation story requires defining how records will be selected for manual review and documenting the manual-validation process.
  - The team reviewed existing resources that provide background for this work, including:
    - Project READMEs.
    - Research Decision Records under `docs/decisions/`.
    - The similarity/grouping strategy.
    - Artifact grouping and duplicate filtering.
    - `Skilltrace`/family-analysis tooling for viewing related artifacts and differences.
  - Kyle will help Christian establish a working environment and walk through the Sprint 1 sampling approach as a starting point for the Sprint 2 sample.
  - Christian will raise unclear requirements or terminology in Discord so the team can clarify and refine the story tasks as needed.

- Discussed the **manual-validation workflow**.
  - Kyle has already been reviewing candidate samples generated from the broader scan results.
  - He has used `Skilltrace` to inspect artifact families and compare examples with many or few scanner matches.
  - Once the Sprint 2 validation sample is finalized, Kyle will perform the fuller manual validation against that sample.

- Clarified the relationship between the **end-to-end pipeline, manual validation, and preliminary analysis**.
  - The automated pipeline and the manual-validation process should operate on the **same sample** so their results can be compared directly.
  - The end-to-end notebook should:
    - Load the selected artifacts or artifact pairs.
    - Establish the base/derived relationship as needed.
    - Run the refined scanner.
    - Record the scanner findings.
    - Compare the automated findings with the manually inspected expectations.
  - The analysis should identify whether expected behavior was detected, whether false positives occurred, and whether expected findings were missed.
  - The pipeline should use the reusable project libraries directly from the notebook rather than duplicating command-line implementation logic.

- Discussed **preliminary Sprint 2 results and report integration**.
  - Preliminary evidence should summarize what the Sprint 2 analysis shows in relation to the research question.
  - Results should be reproducible from the notebook and should include the relevant tables or figures.
  - Kyle recommended adding Sprint 2 results directly to the research report rather than waiting until Sprint 3.
  - The team agreed that report development should begin during Sprint 2 so Sprint 3 can focus on refinement and completion rather than starting the report from scratch.
  - Kyle and Christian will work together on the research-report update.

- Reviewed **reproducibility documentation**.
  - Reproduction instructions should explain how to regenerate the Sprint 2 tables, figures, and analysis results.
  - Because Vaisnavii is building the analysis pipeline, the related reproducibility work was reassigned to her.
  - Another documentation-oriented story was shifted to maintain a reasonable distribution of work.

- Reviewed remaining **repository and retrospective work**.
  - Jim will handle the repository/review-requirement story.
  - Jim and Kyle will work together on the Sprint 2 retrospective.
  - Sprint 2 lessons and methodological changes should begin flowing into the report and project documentation as they occur.

- Discussed **clarity of backlog stories and tasks**.
  - Christian requested additional context for some stories because several terms depend on work and terminology established during Sprint 1.
  - The team discussed keeping stories focused on requirements rather than prescribing implementation details.
  - When a task is unclear, the assignee should post the specific story/task in Discord, ask for clarification, and update the GitHub description once the requirement is understood.
  - This approach allows the backlog to become clearer without over-specifying implementation choices.

## Decisions and Outcomes

- Sprint 2 scanner results will include **evidentiary information** needed to identify meaningful changes within matched commands or security-sensitive values, rather than relying only on rule-match counts.
- Scanner-rule refinement will continue to be informed by manual inspection of real GitSkills artifacts.
- The expanded rules will include relevant package-manager commands, Windows/PowerShell equivalents, and file-read behavior where appropriate.
- `pytest` will be used for automated repository testing, with tests runnable through `uv run pytest`.
- GitHub issue relationships will be used to document meaningful **blocked-by** dependencies between Sprint 2 stories.
- The Sprint 2 automated pipeline and manual validation will use the **same validation sample** so their results can be directly compared.
- The end-to-end analysis will be implemented through a notebook that reuses the project's existing Python libraries rather than duplicating CLI logic.
- The Sprint 2 analysis will compare scanner findings against manual inspection to identify expected detections, false positives, and missed findings.
- Sprint 2 preliminary results will begin to be incorporated into the research report rather than postponing report development until Sprint 3.
- Reproducibility documentation for the Sprint 2 analysis will be aligned with the analysis-pipeline work.
- Ambiguous backlog tasks will be clarified through Discord and updated in GitHub when additional context is needed.
- Team members should communicate blockers or setup problems early so another member can assist before the dependency affects later Sprint 2 work.
- **Sprint 2 is due October 28, 2026.**

## Action Items

### Jim

- [ ] Complete the remaining tests/sample checks and documentation for the artifact comparison/lineage method.
- [ ] Continue refining the Sprint 2 scanner with Kyle, including evidentiary comparison of matched values and parameters.
- [ ] Review and correct the GitHub Project issue/sub-issue relationship that changed while blocker relationships were being configured.
- [ ] Complete the Sprint 2 repository/review-requirement work.
- [ ] Work with Kyle on the Sprint 2 retrospective.

### Vaisnavii

- [ ] Build the Sprint 2 end-to-end analysis pipeline once the required scanner and sample-selection dependencies are available.
- [ ] Use the same validation sample as the manual-validation process so automated and manual results can be compared.
- [ ] Retry the shared `GITSKILLS_DB` environment-variable approach on macOS for the Sprint 2 notebook.
- [ ] Document the process needed to reproduce the Sprint 2 analysis outputs, tables, and figures.
- [ ] Review real GitSkills artifacts and raise potential scanner-rule gaps in Discord.

### Kyle

- [ ] Continue expanding and refining automated tests as the Sprint 2 scanner and pipeline stabilize.
- [ ] Continue scanner refinement with Jim, including evidence/value capture and rule expansion.
- [ ] Use the broader scan results and `Skilltrace` to help identify representative validation examples.
- [ ] Perform full manual validation after the Sprint 2 validation sample is finalized.
- [ ] Send Christian setup/sampling guidance and meet with him as needed to help establish a working environment and understand the Sprint 2 validation work.
- [ ] Work with Christian on updating the research report with Sprint 2 material.
- [ ] Work with Jim on the Sprint 2 retrospective.

### Christian

- [ ] Complete the local project environment setup and continue reviewing the Sprint 1 project documentation and RDRs.
- [ ] Work with Kyle to understand the Sprint 1 sampling approach and define the Sprint 2 validation sample/protocol.
- [ ] Document how records are selected for manual validation and how the manual-review process will be performed.
- [ ] Raise unclear story requirements or terminology in Discord and update assigned GitHub tasks after clarification.
- [ ] Work with Kyle on the Sprint 2 research-report update.
- [ ] Review real GitSkills artifacts and participate in identifying scanner-rule gaps.

### All Team Members

- [ ] Review representative `SKILL.md` artifacts and identify security-sensitive behaviors that may not be covered by the current scanner.
- [ ] Discuss proposed scanner-rule additions or changes in Discord before implementation.
- [ ] Use GitHub relationships where helpful to make Sprint 2 story dependencies visible.
- [ ] Communicate blockers, environment problems, or unclear requirements as soon as they are identified.
- [ ] Begin incorporating Sprint 2 findings and methodological lessons into the project documentation and report as work progresses.
