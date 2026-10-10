# CSC 580 Group 8 – Meeting Minutes

**Date:** October 5, 2026  
**Time:** Approximately 6:00 PM EDT  
**Duration:** Approximately 1 hour 8 minutes  
**Attendees:** Jim Prantzalos, Vaisnavii Mohanraj, Kyle Cantrell  
**Absent:** Christian Heiney  
**Purpose:** Review and finalize the Sprint 1 deliverable, prepare the Sprint 2 backlog and assignments, and discuss improvements to the GitSkills scanner, validation approach, and project documentation.

## Main Topics of Discussion

- Reviewed the **Sprint 1 deliverable**, which is due October 7.
  - The team compared the deliverable package against the Sprint 1 requirements.
  - Jim prepared a submission document that maps each required Sprint 1 item to the corresponding project artifact or documentation.
  - Kyle and Vaisnavii reviewed the document and indicated that it appeared to cover the required material.
  - The retrospective is included as part of the Sprint 1 deliverable.
  - Jim will obtain Christian's review before submitting the final package for the group.

- Reviewed the initial **Sprint 2 backlog** and story assignments.
  - Sprint 2 begins after the October 7 Sprint 1 deadline.
  - Team members should review the new stories and assign themselves to work they are comfortable completing.
  - Kyle selected work involving automated testing and manual validation.
  - A sample/manual-review story was identified as a useful starting point for Christian because it requires becoming familiar with the GitSkills format, database contents, and representative artifacts.
  - Preliminary analysis, reproducible tables and figures, end-to-end integration, reporting, and the Sprint 2 retrospective were also reviewed as upcoming work areas.
  - Team members should raise questions before beginning a story if its requirements or dependencies are unclear.

- Discussed the importance of identifying **blockers and dependencies** early.
  - Team members should use Discord to ask questions when a story or implementation detail is unclear.
  - Dependencies on another team member's work should be communicated as soon as they are identified.
  - Where appropriate, temporary stubs or simplified implementations can be used to avoid blocking other work while a full implementation is being completed.

- Reviewed Vaisnavii's local **DuckDB and notebook setup on macOS**.
  - Vaisnavii successfully configured DuckDB and reproduced the existing notebook results.
  - The primary issue involved resolving the local database path from within VS Code.
  - A temporary hard-coded path worked, but the team wants shared notebooks to remain portable and avoid machine-specific path changes.
  - The intended configuration is to use the `GITSKILLS_DB` environment variable to identify the local database.
  - The discussion covered the difference between temporary shell environment variables and persistent user environment configuration.
  - Vaisnavii will retry the setup using a persistent shell/profile configuration so the variable is available when VS Code initializes its notebook environment.
  - Jim offered to help troubleshoot the VS Code environment if the problem continues.

- Discussed priorities for improving the **Sprint 2 scanner**.
  - The current scanner primarily detects whether security-sensitive commands or behaviors are present in the base and derived artifacts.
  - This can miss important changes when the same command exists in both artifacts but one of its parameters changes.
  - For example, a `curl` command may exist in both artifacts while the target URL changes in the derived artifact.
  - The scanner should therefore evolve beyond simple command-token presence and consider meaningful changes to command parameters or other security-sensitive values.
  - Scanner refinement should occur early in Sprint 2 so later validation and analysis are based on useful and defensible detection results.
  - Jim and Kyle expect to focus on improving this portion of the scanner during the early Sprint 2 work.

- Discussed how to handle **sibling artifacts** associated with a skill.
  - The team considered whether all sibling files, including Markdown, JSON, scripts, and other file types, should be scanned for introduced risk.
  - Markdown and data files can contain URLs or other potentially sensitive values, but scanning all such content could create a large number of false positives when the files are not directly executable.
  - The team favored keeping the initial scope focused on **executable or execution-relevant sibling files** rather than scanning every sibling artifact indiscriminately.
  - Before finalizing the exact scope, the team will examine the file extensions present in sibling artifacts and determine which types should be included.
  - Kyle added a task under **Story 5.2** to inventory sibling file types/extensions.
  - Any intentional exclusions should be documented in the project's threats-to-validity discussion, including the rationale for limiting the scan scope.

- Reviewed possible additions to the **scanner detection rules**.
  - Manual review identified behaviors not currently represented by the initial rules, including use of the `bun` package manager and potentially additional network protocols.
  - The team discussed whether bare IP addresses should be treated as risky behavior.
  - A bare IP address by itself was not considered sufficient evidence of a security-sensitive network action; protocol or execution context would provide a stronger signal.
  - Existing network rules detect HTTP/HTTPS patterns, while other protocols such as FTP may need to be evaluated based on the data.
  - The team does not want to continually add rules without evidence that they are useful.
  - Representative GitSkills artifacts should be manually inspected to identify recurring behaviors that the current scanner misses.
  - Proposed rule additions should be raised in the team discussion so the group can decide whether the behavior is common and important enough to include.
  - The goal is to balance scanner coverage with simplicity and avoid unnecessary false positives.

- Emphasized the need for **team-wide manual data exploration**.
  - All team members should spend time examining real GitSkills artifact content rather than relying only on the existing scanner implementation.
  - Manual inspection should be used to identify:
    - Security-sensitive patterns not covered by the current rules.
    - Common commands, package managers, protocols, credential references, and file operations.
    - Cases where an existing rule is too broad or too narrow.
    - Potential false positives.
  - Findings from manual exploration should feed back into scanner-rule refinement and the project's validation methodology.

- Discussed using **Mermaid diagrams** to document the project pipeline and scanner.
  - Kyle generated Mermaid flowcharts from the source code to visualize the pipeline.
  - The diagrams include areas such as database loading, lineage/base-derived decisions, and scanner execution flow.
  - The team agreed that visual explanations would be useful for documentation and could also support the final presentation.
  - Mermaid diagrams should be stored with the documentation they explain:
    - In a notebook when directly supporting notebook analysis.
    - In an appropriate README when documenting a specific pipeline.
    - In a Markdown document under `docs/` when providing a broader explanation of scanner or pipeline behavior.
  - Kyle will share/add the generated Mermaid diagrams for team review.

- Briefly discussed the **final project presentation**.
  - The exact presentation format has not yet been confirmed.
  - The team expects that visualizations and pipeline diagrams will be useful regardless of whether the final submission is a slide deck, a recorded presentation, or another format.

- Discussed unclear instructions for newly posted **course assignments** outside the group project.
  - The team reviewed the newly posted ATM use-case/class-diagram assignment and could not identify clear supporting instructions for the expected deliverable.
  - The team also discussed a separate "buy a product" scenario that appears to be configured as a group submission but has no clear due date or instructions.
  - Vaisnavii will contact the instructor for clarification on both items and share the response with the team.

## Decisions and Outcomes

- The Sprint 1 deliverable appears to cover the required material and will be submitted after final team confirmation.
- The Sprint 1 retrospective will be included as part of the Sprint 1 deliverable package.
- Sprint 2 backlog work will begin after the October 7 Sprint 1 deadline, with team members reviewing and claiming stories based on interest and availability.
- Team members should communicate blockers, dependencies, and unclear requirements early rather than proceeding on assumptions.
- Shared notebooks and code should use the `GITSKILLS_DB` environment variable rather than machine-specific hard-coded database paths.
- The scanner will be refined to detect meaningful changes within security-sensitive commands and values, not only the introduction or removal of command tokens.
- Initial sibling-artifact scanning will focus on executable or execution-relevant files rather than all sibling content.
- The team will inventory sibling file extensions before finalizing which sibling artifact types are included in the scan.
- Intentional exclusions from sibling-artifact analysis will be documented as scope limitations and threats to validity.
- Scanner rules will be expanded based on evidence from representative GitSkills artifacts rather than by attempting to enumerate every possible command, protocol, or security indicator in advance.
- A bare IP address alone will not be treated as a sufficient security-risk indicator without additional protocol or execution context.
- All team members will participate in manual artifact inspection to help identify scanner gaps, false positives, and candidate rules.
- Mermaid diagrams will be added to the repository where they improve documentation of the scanner or pipeline and may later be reused in presentation materials.
- Vaisnavii will seek instructor clarification on the ATM use-case/class-diagram assignment and the "buy a product" scenario.

## Action Items

### Jim

- [x] Reach out to Christian for a final review of the Sprint 1 deliverable.
- [x] Submit the Sprint 1 deliverable after final team confirmation.
- [x] Help troubleshoot the `GITSKILLS_DB`/VS Code environment issue if it continues.
- [x] Work with Kyle on early Sprint 2 scanner refinements, including detection of meaningful parameter/value changes.

### Vaisnavii

- [ ] Retry the local notebook configuration using a persistent `GITSKILLS_DB` environment setting rather than a hard-coded local path.
- [ ] Review the Sprint 2 backlog and claim additional stories as appropriate.
- [ ] Manually inspect representative GitSkills artifacts and raise candidate scanner rules, missed behaviors, or false-positive concerns with the team.
- [ ] Email the instructor for clarification on the ATM use-case/class-diagram assignment and the "buy a product" scenario.
- [ ] Share the instructor's response with the team.

### Kyle

- [ ] Continue work on the Sprint 2 automated-testing and manual-validation stories.
- [ ] Work with Jim on refining the scanner to capture security-sensitive parameter/value changes.
- [ ] Inventory sibling artifact file extensions as part of Story 5.2 and use the results to help define the supported scan scope.
- [ ] Share/add the Mermaid scanner and pipeline diagrams to the repository for team review.
- [ ] Continue manual inspection of GitSkills artifacts and raise potential rule additions with the team.

### Christian

- [ ] Review the Sprint 1 deliverable and provide any final feedback.
- [ ] Review the assigned Sprint 2 sample/manual-review work and become familiar with the GitSkills format and dataset.
- [ ] Participate in manual artifact review and scanner-rule refinement during Sprint 2.

### All Team Members

- [ ] Review the Sprint 2 backlog and confirm or claim assigned work.
- [ ] Inspect representative GitSkills artifacts and identify recurring security-sensitive behaviors not covered by the current rules.
- [ ] Raise proposed scanner-rule additions or exclusions in the team discussion before implementation.
- [ ] Communicate blockers, dependencies, or unclear story requirements through Discord as soon as they are identified.
- [ ] Help refine the scanner early in Sprint 2 so later validation and analysis are based on a defensible detection approach.
