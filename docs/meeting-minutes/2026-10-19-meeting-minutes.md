# CSC 580 Group 8 – Meeting Minutes

**Date:** October 19, 2026  
**Time:** Approximately 7:00 PM ET  
**Duration:** Approximately 53 minutes  
**Attendees:** Jim Prantzalos, Kyle Cantrell, Christian Heiney  
**Absent:** Vaisnavii Mohanraj  
**Purpose:** Review Sprint 2 progress and dependencies, discuss validation and testing work, respond to Sprint 1 feedback, and demonstrate the `SkillTrace` workflow used for lineage analysis and manual validation.

## Main Topics of Discussion

- Reviewed current **Sprint 2 backlog progress** and remaining work.
  - Jim's Story 5.1 comparison-method work is largely complete, with documentation and testing still remaining.
  - Kyle completed handling for missing or malformed artifact content so invalid records do not stop the analysis.
  - Kyle will submit the related pull request and continue work on safeguards ensuring dataset content is never executed.
  - Some Story 5.2 work remains dependent on the evidence-based comparison functionality being completed under Story 5.3.
  - Jim identified Story 5.3 as a priority because it is currently blocking Vaisnavii's end-to-end pipeline work.

- Discussed the relationship between **automated testing and the refined scanner**.
  - Automated test development does not need to wait for the final evidence-based scanner implementation.
  - Tests can be built against the current scanner and rerun as the scanner is refined.
  - The main validation question is whether the scanner flags cases that should be flagged and avoids flagging cases that manual review determines are false positives.
  - Scanner performance should therefore be evaluated against manually reviewed examples rather than only checking individual rule-match details.

- Reviewed **Sprint 1 instructor feedback**.
  - The instructor's feedback raised a question about showing the chronology or timeline of skill evolution.
  - The team confirmed that chronology and lineage are already part of the comparison methodology through similarity analysis, clustering, and available commit-date information.
  - The larger issue appears to be that some of the implemented capabilities were not sufficiently visible or clearly explained in the Sprint 1 documentation.
  - The team agreed that future documentation should make the lineage methodology and implemented tooling easier to discover and understand.
  - Overall Sprint 1 feedback was positive, with only a minor grading deduction.

- Revisited the **project's research objective and scope**.
  - The project is not intended to create a comprehensive malware scanner for natural-language `SKILL.md` files.
  - The objective is to estimate how often security-sensitive or risky behavior may be introduced as related skills are copied and modified across repositories.
  - Related skills are identified using more than name matching alone, including similarity measures and chronology information.
  - Establishing base/derived relationships allows the scanner to identify where potentially risky behavior appears or is removed as a skill evolves.

- Reviewed Christian's **validation sample and protocol** work.
  - Christian completed the primary tasks associated with defining the validation sample and submitted a pull request.
  - The team reviewed whether the generated CSV could contain third-party licensed or proprietary content.
  - The CSV primarily contains identifiers, timestamps, hashes, and other metadata rather than full skill content.
  - The team agreed that actual third-party `SKILL.md` content should not be committed into the project repository unless redistribution rights are clearly established.
  - Metadata and identifiers needed to reproduce or locate the validation sample can be retained without redistributing the source artifacts themselves.

- Discussed the **manual validation workflow**.
  - Kyle plans to perform manual validation while expanding the automated test coverage.
  - Story 6.3 manual-validation results will feed into Christian's Story 6.4 work evaluating validation results and limitations.
  - The intended comparison is between the scanner's automated findings and human review of the same examples.
  - This comparison should identify:
    - Cases correctly flagged by the scanner.
    - False positives.
    - Expected risky behavior that the scanner misses.
    - Limitations in the current rule set or comparison method.

- Reviewed **research-report progress**.
  - Kyle has already added methodology material and documentation of recently added scanner rules to the report.
  - Kyle and Christian will continue coordinating on the report as validation results become available.
  - Sprint 2 results and limitations should be incorporated into the report as the work is completed rather than postponed until Sprint 3.

- Reviewed Christian's **local development environment**.
  - Christian successfully completed the Sprint 1 environment setup using the project setup guide.
  - Git Bash was used where Bash-oriented setup instructions were more convenient than PowerShell.
  - The team discussed optional IDE tooling and student licensing resources.
  - Jim will send Christian information about the GitHub Student Developer Pack, which can provide access to JetBrains tools and other development resources.
  - IDE selection remains a matter of individual preference.

- Reviewed remaining **Epic 7 and sprint-closeout work**.
  - Vaisnavii's analysis-results and figure-generation work depends on the end-to-end pipeline and upstream scanner work.
  - Jim expects to complete the final sprint-maintenance/closeout stories before the Sprint 2 deadline.
  - **Sprint 2 is due October 28, 2026.**

- Demonstrated the **`SkillTrace` application** for lineage analysis and manual review.
  - `SkillTrace` uses generated family-analysis reports to visualize related artifacts and their relationships.
  - The tool can display:
    - Direct base/derived relationships.
    - Entire related-skill clusters.
    - Equivalent-peer relationships.
    - Content differences between artifacts.
    - Scanner results for selected base/derived pairs.
    - Associated sibling resources when present.
  - Family-analysis reports are generated from the GitSkills database and loaded by the application for interactive review.
  - The tool is intended to make manual validation easier by assembling lineage, similarity, content differences, and scan results in one place.

- Clarified the **clustering and lineage methodology** during the `SkillTrace` walkthrough.
  - Skills with the same name are not automatically assumed to be the same artifact family.
  - Similar documents are grouped into clusters, while substantially different artifacts with the same name can fall into separate clusters.
  - Only clusters containing multiple related artifacts are useful for reuse/change analysis.
  - Parent/child or base/derived relationships are established using similarity and chronology information.
  - Commit dates are useful when present, but the dataset contains artifacts with missing dates.
  - Because date information is incomplete, chronology cannot rely exclusively on `first_commit_at`.
  - Highly similar **equivalent peers** can provide supporting chronology information when one artifact lacks a date and a closely related peer has usable date information.

- Reviewed an example scanner result inside `SkillTrace`.
  - The demonstrated example showed a negative rule delta because an `npm install` instruction present in the base artifact had been removed from the derived artifact.
  - This reinforced that the scanner needs to identify both **introduced** and **removed** security-sensitive behavior.
  - The example also illustrated how the visual diff can be used to verify whether the scanner's result matches the underlying artifact changes.

- Discussed **sibling-resource analysis**.
  - A skill can introduce or modify associated resources such as scripts, Markdown files, JSON/YAML files, or other supporting artifacts even when the primary `SKILL.md` changes little.
  - These sibling resources may contain security-sensitive behavior relevant to the supply-chain analysis.
  - The team recognized that sibling-resource changes need to be considered as part of the broader comparison and validation methodology.
  - The exact supported sibling scan scope will continue to be refined as the Sprint 2 implementation develops.

- Revisited the instructor's request for a **timeline/chronology view**.
  - A literal date-only timeline would be incomplete because many GitSkills artifacts do not contain usable commit dates.
  - The team's similarity- and lineage-based approach provides a more complete ordering than filtering the study down to only artifacts with dates.
  - The team will focus on documenting and communicating this methodology more clearly rather than replacing it with a date-only approach.

## Decisions and Outcomes

- Story 5.3 evidence-based security comparison is a near-term priority because it is blocking Vaisnavii's end-to-end analysis pipeline.
- Automated testing can proceed against the current scanner and be rerun as scanner behavior is refined.
- Scanner validation will focus on agreement with manual review, including false positives and missed detections.
- The project will continue to frame results as evidence of **potentially risky behavior introduced during reuse/evolution**, not as definitive malware classification.
- Existing chronology and lineage functionality will be documented more clearly in response to Sprint 1 instructor feedback.
- Chronology will continue to use similarity, clustering, commit information, and equivalent-peer relationships rather than relying exclusively on commit dates.
- Actual third-party `SKILL.md` content will not be committed to the project repository unless redistribution rights are established; reproducible identifiers and metadata can be stored instead.
- `SkillTrace` will be used as a supporting tool for manual validation and inspection of related artifact families.
- Validation work will compare automated scanner results with manually inspected artifact changes and document false positives, missed detections, and method limitations.
- Scanner reporting will account for both the introduction and removal of security-sensitive behavior.
- Sibling resources will be considered in the comparison methodology because security-sensitive changes may occur outside the primary `SKILL.md`; the exact scan scope remains subject to refinement.
- Sprint 2 report material should be updated as methodology and validation results become available.
- **Sprint 2 remains due October 28, 2026.**

## Action Items

### Jim

- [ ] Complete the remaining Story 5.1 comparison-method documentation and testing.
- [ ] Complete Story 5.3 evidence-based security comparison so Vaisnavii can proceed with the end-to-end pipeline.
- [ ] Review and merge outstanding pull requests as they are submitted.
- [ ] Complete the remaining Sprint 2 maintenance/closeout stories before the October 28 deadline.
- [ ] Improve documentation of the existing chronology/lineage methodology so the implemented capabilities are easier to identify.
- [ ] Send Christian information about the GitHub Student Developer Pack.
- [ ] Assist team members with `SkillTrace` or environment setup questions as needed.

### Kyle

- [ ] Submit the pull request for handling missing or malformed artifact content.
- [ ] Complete the remaining Story 5.2 safeguard ensuring dataset content is never executed.
- [ ] Continue expanding automated test coverage using the current scanner implementation.
- [ ] Perform Story 6.3 manual validation while developing the automated test coverage.
- [ ] Provide the manual-validation results needed for Christian's Story 6.4 analysis.
- [ ] Continue updating the research report as scanner and validation work progresses.

### Christian

- [ ] Complete Story 6.4 evaluation of validation results and limitations after the Story 6.3 manual-validation results are available.
- [ ] Use `SkillTrace` and the validation sample to become familiar with the lineage and manual-inspection workflow.
- [ ] Continue coordinating with Kyle on Sprint 2 research-report updates.
- [ ] Raise questions in Discord if validation requirements, tooling, or terminology remain unclear.

### Vaisnavii

- [ ] Continue the end-to-end Sprint 2 analysis pipeline once Story 5.3 is complete.
- [ ] Generate the preliminary analysis results and figures after the required scanner and pipeline dependencies are available.

### All Team Members

- [ ] Communicate blockers and dependencies through Discord as soon as they are identified.
- [ ] Avoid committing third-party skill content to the repository unless redistribution rights are established.
- [ ] Use manual inspection and `SkillTrace` findings to help identify scanner false positives, missed detections, and methodology limitations.
- [ ] Continue improving documentation so major implemented capabilities and research decisions are easy for reviewers to find.
