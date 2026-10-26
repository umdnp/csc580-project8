# CSC 580 Group 8 – Meeting Minutes

**Date:** October 25, 2026  
**Time:** 2:00 PM ET / 1:00 PM CT  
**Duration:** Approximately 1 hour 5 minutes  
**Attendees:** Jim Prantzalos, Vaisnavii Mohanraj, Kyle Cantrell  
**Absent:** Christian Heiney  
**Purpose:** Review the evidence-based scanner and Sprint 2 pipeline, finalize the validation/sample approach, review remaining Sprint 2 work, and prepare for the transition into Sprint 3.

## Main Topics of Discussion

- Reviewed the new **evidence-based scanner** and how it differs from the original rule-count approach.
  - The original scanner primarily identified whether a command, URL, file operation, or other rule match appeared in the base or derived artifact.
  - This was insufficient when the same command existed in both artifacts but its arguments or surrounding context changed.
  - The revised scanner collects supporting evidence around each match so the comparison can identify meaningful changes within the same command.
  - For example, changing `rm -rf temp` to a broader destructive target should be treated differently from simply observing that `rm` exists in both artifacts.
  - The revised comparison can therefore identify security-sensitive changes that would not appear as a simple rule-count increase.

- Reviewed the new **risk-indicator model**.
  - Evidence-based findings are filtered through a defined set of **11 risk indicators** representing changes the team considers especially relevant to the research question.
  - Examples discussed included:
    - Changes to URLs used in download-and-execute workflows.
    - Changes to the source of shell scripts or other executable content.
    - Changes from HTTPS to HTTP.
    - Changes to domains or executable file types.
  - The goal is to reduce noise by focusing on changes with stronger security implications rather than treating every textual change as equally risky.
  - An example comparison showed that the original rule-based scan flagged a much larger portion of the analyzed relationships, while evidence-based filtering reduced the findings to a smaller, more targeted set.

- Discussed **scope control for the risk indicators and scanner rules**.
  - The team agreed that the current 11 risk indicators are sufficient for the semester project.
  - Additional risk indicators will **not** be added before Sprint 3.
  - If manual review identifies additional behaviors that the current model does not capture, those cases should be documented under threats to validity and future work rather than continually expanding project scope.
  - Existing extraction logic may still be refined to reduce false positives or incomplete scans.
  - Examples discussed included:
    - Distinguishing local `pip` installs from potentially riskier external package installs.
    - Avoiding matches for words such as `more`, `less`, and `service` when they appear as ordinary prose rather than executable commands.
  - The emphasis will be on improving the quality of the current extraction logic rather than introducing new categories of risk.

- Discussed the expected focus of **Sprint 3**.
  - Sprint 3 will primarily focus on completing and refining the research report, interpreting the results, documenting limitations, and preparing final project artifacts.
  - Scanner issues discovered after the Sprint 2 implementation is finalized should generally be documented rather than triggering substantial new implementation work.
  - Additional scanner enhancements can be identified as future work.

- Reviewed **Git workflow practices** for the remainder of the project.
  - Team members should pull from `main` regularly while working on feature branches.
  - Keeping branches synchronized with the latest merged changes should reduce merge conflicts.
  - Conflicts that do occur will still require manual review to determine which changes should be retained.

- Demonstrated the updated **SkillTrace evidence-inspection workflow**.
  - `SkillTrace` now provides an **Inspect Evidence** view in addition to the original scan results.
  - Base and derived evidence is displayed side by side to make comparison easier.
  - The interface highlights content that was added, removed, or changed.
  - Supporting source context is included so reviewers can understand how a matched command or value is being used.
  - The original rule-match counts remain available for comparison, but the evidence view provides the more detailed context needed for validation.

- Reviewed how **manual validation** should use `SkillTrace`.
  - `SkillTrace` can be used to identify and inspect candidate findings, but the team should not treat its output as ground truth.
  - Manual reviewers should compare the actual base and derived content to verify that flagged findings represent real changes.
  - Reviewers should also look for security-sensitive changes that appear in the artifact diff but were **not** detected by the evidence-based scanner.
  - Manual validation should therefore identify:
    - Correctly detected findings.
    - False positives.
    - Missed findings or false negatives.
    - Cases where incomplete dataset content prevents a definitive comparison.

- Discussed limitations in **sibling-resource comparison**.
  - Sibling resources are supporting files used by a skill rather than the `SKILL.md` artifact itself.
  - A skill may preserve the same primary instructions while changing an associated script or resource.
  - Current sibling comparison works most reliably when corresponding files retain the same filename.
  - Renamed sibling files may not be matched even when their content is similar.
  - Some sibling records also lack fetched content, which can result in a **partial scan** because there is nothing available to compare.
  - The team agreed that attempting to solve renamed-sibling similarity matching is outside the current project scope.
  - This limitation should instead be documented in threats to validity.

- Reviewed **skill-family clustering and lineage inference**.
  - Skills are not treated as related simply because they share a name or description.
  - Content similarity is used to separate substantially different artifacts into different clusters.
  - Within a cluster, similarity, containment, and available chronology information are used to infer likely base/derived relationships.
  - Because the GitSkills dataset does not provide definitive copy provenance or complete historical versions, these relationships remain inferred rather than proven.
  - The pipeline distinguishes stronger **direct relationships** from weaker but potentially relevant **related relationships**.

- Discussed whether the final analysis should include both **direct and related edges**.
  - The current Sprint 2 pipeline scans both direct and related relationships within selected skill families.
  - This provides broader coverage but increases runtime and the number of comparisons.
  - The team may consider restricting the final Sprint 3 analysis to direct relationships if doing so allows a broader set of skill families to be analyzed more efficiently.
  - No final decision was made during the meeting; this remains a possible Sprint 3 refinement.

- Troubleshot Vaisnavii's **SkillTrace and DuckDB configuration**.
  - `SkillTrace` initially reported that DuckDB was unavailable.
  - The team reviewed DuckDB's connection limitations and confirmed that an existing DuckDB connection can interfere with another process attempting to open the same database.
  - Vaisnavii's immediate issue was resolved by supplying the correct local database path when starting `SkillTrace`.
  - The `GITSKILLS_DB` environment variable can be configured persistently so the database path does not need to be supplied each time.
  - If the `--db` command-line option is supplied, it overrides the environment-variable value.

- Reviewed the updated **Sprint 2 end-to-end pipeline**.
  - The Sprint 2 unit of analysis is now a **skill family and its inferred relationships**, rather than only individual base/derived artifact pairs as used during Sprint 1.
  - The pipeline scans the relationships within the selected families and aggregates the evidence-based findings.
  - Scan results are cached under the Sprint 2 results directory so previously completed family scans do not need to be repeated.
  - A rescan option is available when a full rerun is required.
  - Preserving cached scans allows the remaining pipeline steps to be regenerated much more quickly.

- Discussed the **Sprint 2 sample**.
  - The current working cohort contains approximately 20 selected skill families.
  - Jim is continuing to refine the sample so the final cohort provides broader representation across the 11 risk indicators.
  - Some risk indicators were not represented in the current sample, while others appeared much more frequently.
  - The goal is not necessarily an equal distribution, but the team would like the validation cohort to exercise a useful range of the defined indicators.
  - The final Sprint 2 sample was not yet locked at the time of the meeting.

- Reviewed the generated **manual-review artifacts**.
  - The pipeline generates validation-sample files and annotation templates for manual review.
  - Manual-review examples are selected reproducibly using a fixed/random seed.
  - The annotation fields and expected review process are documented in the end-to-end notebook.
  - Kyle can begin reviewing examples already present in the current sample.
  - Until the final cohort is locked, manual-review notes should be kept separately so they are not lost if the generated CSV files change.
  - Once the final sample is established, the completed review results can be transferred into the final annotation files.
  - The project also includes an adjudication process for comparing human annotations with scanner findings.

- Reviewed the remaining **Sprint 2 backlog**.
  - Most Sprint 2 implementation stories are complete or nearly complete.
  - The end-to-end pipeline now satisfies most of the pipeline requirements.
  - Finalizing the Sprint 2 sample remains one of the primary remaining items.
  - Threats-to-validity documentation has already been updated with several discovered false-positive, false-negative, and partial-scan cases.
  - Additional limitations discovered during manual review can still be added.

- Reviewed Vaisnavii's **Sprint 2 results and figure work**.
  - Existing pipeline outputs already contain many of the statistics, summaries, and figures needed for Stories 7.1 and 7.2.
  - Vaisnavii can begin creating a Sprint 2 results README before the final sample is locked and revise it once the sample is finalized.
  - The README should live with the Sprint 2 results rather than replacing the repository's existing pipeline/setup README.
  - Existing generated tables, figures, and notebook outputs should be referenced rather than recreated unnecessarily.

- Reviewed the **research report**.
  - Kyle has already added methodology and threats-to-validity material to the report.
  - The report should be updated to reflect the evidence-based scanner, extractors, and other Sprint 2 methodology changes.
  - The current report is substantially longer than necessary.
  - The team discussed reducing the main report to the most important research content and moving detailed tables, code snippets, or supporting material to appendices where appropriate.
  - Report refinement will become a major focus during Sprint 3.

- Reviewed final **Sprint 2 closeout work**.
  - Jim will update the main repository README with the latest project information.
  - The Sprint 2 retrospective has already been drafted.
  - The team expects to complete the remaining Sprint 2 work by the October 28 deadline.

- Briefly discussed other **course assignments**.
  - Vaisnavii created a draft persona in a shared Google Slides document for an upcoming assignment.
  - Kyle will review the persona draft.
  - Jim will review the related lecture and assignment requirements and then review or update the shared persona.
  - The team also noted a separate "buy a product" activity that still needs attention, although it does not appear to have the same immediate deadline.

## Decisions and Outcomes

- The project will use the current set of **11 evidence-based risk indicators** through Sprint 3 rather than continuing to expand the indicator set.
- Scanner refinement will focus on improving existing evidence extractors and reducing false positives or incomplete detections.
- Newly discovered unsupported cases will generally be documented as **threats to validity** or **future work** instead of expanding project scope.
- Sprint 3 will focus primarily on analysis, report refinement, limitations, final artifacts, and communication of results.
- `SkillTrace` will support manual validation, but scanner output must still be checked against the actual base/derived artifact content.
- Manual validation will explicitly consider false positives, false negatives, and partial scans.
- Renamed sibling-resource matching will remain outside the current implementation scope and will be documented as a limitation.
- Sprint 2 analysis will operate on **skill families and inferred relationships**, rather than only individual artifact pairs.
- Direct and related relationships will both remain in the current Sprint 2 pipeline; limiting final analysis to direct relationships remains a possible later optimization.
- Previously completed scans will be cached and reused by default to make pipeline reruns more efficient.
- The Sprint 2 sample will be refined to provide useful coverage across the defined risk indicators before it is finalized.
- Kyle may begin manual review on the current sample, but review notes should remain separate until the final annotation files are stable.
- Vaisnavii can begin the Sprint 2 results summary and figure documentation using the existing generated artifacts before the final sample is locked.
- The research report should be shortened and updated to reflect the Sprint 2 evidence-based methodology.
- **Sprint 2 remains due October 28, 2026.**

## Action Items

### Jim

- [ ] Finalize the Sprint 2 sample/cohort with broader representation across the defined risk indicators.
- [ ] Continue refining existing evidence extractors where manual inspection identifies false positives, false negatives, or incomplete scans.
- [ ] Complete the remaining Sprint 2 pipeline/sample work and check the finalized generated artifacts into the repository.
- [ ] Update threats-to-validity documentation with any additional limitations discovered during validation.
- [ ] Update the repository's main README with the latest Sprint 2 project information.
- [ ] Finalize the Sprint 2 retrospective and closeout work.
- [ ] Review the persona assignment lecture and the shared persona draft.

### Vaisnavii

- [ ] Begin the Sprint 2 results summary/README using the existing pipeline outputs and revise it after the final sample is locked.
- [ ] Reference the existing generated Sprint 2 statistics, tables, and figures rather than duplicating analysis logic.
- [ ] Complete the Sprint 2 figure/results documentation for Stories 7.1 and 7.2.
- [ ] Configure `GITSKILLS_DB` persistently if desired so `SkillTrace` and notebooks can locate the local database without repeatedly supplying the path.
- [ ] Continue reviewing the shared persona assignment and incorporate team feedback as needed.

### Kyle

- [ ] Begin manual review using the stable portion of the current Sprint 2 sample.
- [ ] Keep interim manual-review notes separate until the final sample and generated annotation files are finalized.
- [ ] Transfer completed review findings into the final annotation files once the sample is locked.
- [ ] Continue updating the research report with the Sprint 2 evidence-based scanner, methodology, and threats-to-validity material.
- [ ] Begin trimming the report so the main body focuses on the most important research content, with supporting detail moved to appendices where appropriate.
- [ ] Review Vaisnavii's shared persona draft.

### Christian

- [ ] Review the meeting recording/minutes and coordinate with the team on remaining assigned Sprint 2 validation work.
- [ ] Use the finalized manual-review artifacts and documented annotation process once the Sprint 2 sample is locked.

### All Team Members

- [ ] Pull from `main` regularly while working on feature branches to reduce avoidable merge conflicts.
- [ ] Use manual artifact inspection to verify evidence-based scanner findings rather than treating automated results as ground truth.
- [ ] Document newly discovered scanner limitations instead of expanding the project with additional risk indicators during Sprint 3.
- [ ] Help complete the remaining Sprint 2 work before the October 28 deadline.
