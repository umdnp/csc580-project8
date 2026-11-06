# CSC 580 Group 8 – Meeting Minutes

**Date:** November 2, 2026  
**Time:** Approximately 8:00 PM ET  
**Duration:** Approximately 31 minutes  
**Attendees:** Jim Prantzalos, Kyle Cantrell  
**Absent:** Vaisnavii Mohanraj, Christian Heiney  
**Purpose:** Review the Sprint 3 backlog, define the final sampling and validation strategy, identify any remaining scanner refinements, and plan the analysis, report, and presentation work for the remainder of the project.

## Main Topics of Discussion

- Reviewed the overall **Sprint 3 focus**.
  - Sprint 3 will primarily center on producing the final research analysis and report rather than introducing substantial new implementation work.
  - Remaining technical work should support the final sampling, validation, and analysis needed to answer the research question.
  - The team will also need to complete the usual sprint-closeout work and prepare the final presentation.
  - **Sprint 3 is due November 18, 2026.**

- Discussed finalizing the **scanner rules and risk indicators**.
  - Kyle's manual-validation work will be used to identify any important scanner gaps that should be addressed before the final analysis.
  - The team wants to finalize the supported rule set and risk indicators rather than continue expanding the scanner throughout Sprint 3.
  - Only issues considered important enough to affect the final analysis should result in additional scanner changes.
  - An example discussed was detection of credential-related values such as `auth_token`.
  - Once any high-priority validation findings are addressed, the scanner will be treated as sufficiently complete for the final study.
  - Remaining unsupported cases can be documented as limitations or future work.

- Discussed whether to restrict the final analysis to **directed lineage edges**.
  - The current family analysis can include both:
    - **Directed edges**, where the inferred base/derived relationship is comparatively strong.
    - **Related edges**, where the likely relationship is more ambiguous.
  - Related edges may introduce additional noise and substantially increase the amount of work required to scan a family.
  - Jim proposed testing whether directed edges alone preserve a similar variety of risk-indicator findings.
  - The goal is not necessarily to preserve the same number of findings, but to determine whether directed edges continue to expose the same general categories of security-sensitive changes.
  - If directed-only scanning produces comparable coverage, the related edges could be excluded from the final analysis to reduce runtime and allow a larger variety of families to be studied.
  - This remains a test to be completed rather than a finalized methodological change.

- Reviewed the need for a **sample-based analysis** rather than scanning the full population.
  - Processing every available family is not feasible within the semester because lineage analysis requires substantial content comparison, including similarity and shingle-based comparisons.
  - The team therefore plans to analyze reproducibly selected samples of skill families.
  - An initial target of approximately **100 families per trial** was discussed.
  - The final sample size may be reduced if runtime proves too high.

- Discussed a **stratified random sampling approach** for skill families.
  - The existing artifact-grouping data can be ordered by family/group size.
  - Families can then be divided into broad high-, middle-, and low-size tiers.
  - A rough partition of the ordered population into upper 20%, middle 60%, and lower 20% groups was discussed as a starting point.
  - The random sample should draw fewer families from the high and low extremes and place most of the sample in the middle tier.
  - This approach is intended to preserve variety while avoiding a sample dominated by either extremely large or very small families.
  - The family-selection process should remain random within each tier rather than manually choosing families that are known to produce findings.

- Reviewed planned changes to the **Family Picker** tool.
  - Kyle will refine the existing Family Picker into a focused sampling utility.
  - The tool should:
    - Accept a requested number of families.
    - Randomly select families across the defined high/middle/low tiers.
    - Return the selected family names for use by the analysis notebook/pipeline.
  - The Family Picker should not perform the scanner or analysis itself.
  - Keeping selection separate from analysis will make the sampling process easier to understand and reuse.

- Discussed the planned **multi-trial analysis design**.
  - The team intends to run multiple independently selected samples rather than base the final conclusions on a single cohort.
  - A target of **three trial samples** was discussed.
  - Each trial should use a recorded random seed so the selected families and resulting analysis can be reproduced.
  - Results from the trials can then be compared or aggregated to determine whether recurring risk-indicator patterns emerge.
  - Consistent findings across independently selected samples will provide the primary evidence for the final analysis.
  - The absence of a particular risk indicator across the trials can also be reported as a result rather than forcing the sample to contain every indicator.

- Discussed **manual validation** of the final sample results.
  - Kyle recommended that all team members participate in manual validation because the final sample will be larger than the Sprint 2 validation cohort.
  - Jim agreed that validation should be shared across the team.
  - Manual review will be performed on a reproducibly selected subset of the sampled results rather than every family.
  - Validation should cover both:
    - Whether the inferred lineage/base-derived relationship is reasonable.
    - Whether the scanner correctly identified the security-sensitive change.
  - The first trial sample will be used to establish the validation workflow before the additional trials are completed.

- Discussed sequencing for the **final study runs**.
  - Jim will first test the directed-edge-only approach to determine whether it continues to produce useful risk-indicator findings.
  - Kyle's revised Family Picker will then be used to create the first random sample.
  - The team will review and manually validate a subset of the first trial.
  - If the approach performs as expected, two additional reproducible random trials will be run.
  - The three result sets will then form the basis of the final analysis and report.

- Reviewed the expected **final report work**.
  - Much of the project's methodology has already been documented in the existing research report.
  - Sprint 3 work will focus on cleaning up the explanation, incorporating the final sample methodology, and adding the empirical results from the planned trials.
  - The report should explain the recurring risk patterns found across the trials and relate those findings back to the project's supply-chain-risk research question.
  - Additional unsupported risks or scanner enhancements can be identified as future work rather than implemented during the final sprint.

- Discussed the **final presentation**.
  - The exact presentation format for online students has not yet been confirmed.
  - If a recorded presentation is required, the team discussed creating a shared slide deck and script and assigning each member a section related to work they contributed.
  - Team members could record their individual portions using tools such as PowerPoint or Zoom.
  - Jim offered to combine the individual recordings into a single final video if needed.
  - No final presentation workflow will be chosen until the instructor's expectations are clearer.

## Decisions and Outcomes

- Sprint 3 will focus primarily on final sampling, validation, analysis, report completion, and presentation preparation rather than major new scanner development.
- Kyle's manual-validation findings will be reviewed for any **final high-priority scanner fixes** before the rule set and risk indicators are frozen for the final analysis.
- The team will test whether **directed lineage edges alone** preserve sufficiently similar risk-indicator coverage before deciding whether to exclude related edges.
- The final study will use **randomly selected skill-family samples** because scanning the full population is not computationally feasible within the project timeline.
- Family selection will use a **stratified random approach** across high-, middle-, and low-size family tiers, with most selections coming from the middle tier.
- The Family Picker will be simplified into a sampling utility that returns selected family names and does not perform scanning or analysis.
- The initial target is approximately **100 families per trial**, subject to reduction if runtime requires a smaller sample.
- The team plans to run **three reproducible trials** with recorded random seeds and compare the resulting risk-indicator patterns.
- The team will not cherry-pick families based on whether they are known to contain scanner findings.
- Manual validation will be shared across the team and will evaluate both the inferred relationships and scanner findings.
- The first sampled trial will be validated before proceeding with the remaining two trials.
- Final conclusions will be based on recurring patterns observed across the sampled trials, including indicators that appear frequently as well as indicators that do not appear.
- Remaining scanner limitations will be documented rather than driving substantial new implementation during Sprint 3.
- **Sprint 3 remains due November 18, 2026.**

## Action Items

### Jim

- [ ] Review Kyle's manual-validation findings and identify any final scanner or risk-indicator fixes that are necessary before the final analysis.
- [ ] Implement any agreed high-priority scanner fixes and then freeze the scanner scope for the remainder of Sprint 3.
- [ ] Test the pipeline using directed edges only and compare the resulting risk-indicator coverage with the current approach.
- [ ] Use the revised Family Picker to run the first stratified random sample once the tool is available.
- [ ] Adjust the initial sample size if approximately 100 families proves too expensive to process.
- [ ] Coordinate manual validation of the first trial sample across the team.
- [ ] Run two additional seeded trials after the first sample and validation workflow are confirmed.
- [ ] Aggregate the trial results and incorporate the final analysis into the research report.
- [ ] Coordinate the final presentation/recording workflow once the instructor's requirements are known.

### Kyle

- [ ] Recheck the manual-validation results for any important scanner gaps that should be fixed before the final study, including credential-related cases such as `auth_token`.
- [ ] Refine the Family Picker into a stratified random family-selection utility.
- [ ] Support a configurable requested sample size and return only the selected family names for use by the analysis pipeline.
- [ ] Ensure the sampling process can be reproduced using recorded random seeds.
- [ ] Share the Family Picker results with Jim for directed-edge testing and the first final-study trial.
- [ ] Participate in manual validation of the first sampled trial.
- [ ] Continue supporting final report and presentation work as needed.

### Vaisnavii

- [ ] Review the meeting minutes and updated Sprint 3 sampling/analysis plan.
- [ ] Participate in the shared manual-validation work once the first final-study sample is available.
- [ ] Contribute to the final analysis, report, and presentation work as assigned.

### Christian

- [ ] Review the meeting minutes and updated Sprint 3 sampling/analysis plan.
- [ ] Participate in the shared manual-validation work once the first final-study sample is available.
- [ ] Contribute to the final analysis, report, and presentation work as assigned.

### All Team Members

- [ ] Participate in manual validation of the reproducibly selected subset from the first trial.
- [ ] Validate both the inferred lineage relationship and the scanner's security-sensitive finding for assigned examples.
- [ ] Report any critical scanner gaps discovered during validation before the scanner scope is finalized.
- [ ] Avoid adding new scanner features during Sprint 3 unless they are necessary to address a significant validation issue.
- [ ] Help complete the final report and presentation materials before the November 18 Sprint 3 deadline.
