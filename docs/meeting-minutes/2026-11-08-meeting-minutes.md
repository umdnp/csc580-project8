# CSC 580 Group 8 – Meeting Minutes

**Date:** November 8, 2026  
**Time:** 4:00 PM ET  
**Duration:** Approximately 35 minutes  
**Attendees:** Jim Prantzalos, Vaisnavii Mohanraj, Kyle Cantrell, Christian Heiney  
**Purpose:** Review the Sprint 3 manual-validation workflow, assign validation work across the three trial runs, clarify lineage versus scanner annotations, review current pull requests and report preparation, and discuss remaining Sprint 3 and final-presentation work.

## Main Topics of Discussion

- Reviewed the **Sprint 3 trial structure and manual-validation plan**.
  - Sprint 3 now uses three independent trial runs rather than the smaller family cohort used in Sprint 2.
  - Each trial randomly selects **100 eligible skill families** from the larger GitSkills population.
  - Selected families must satisfy the project’s eligibility requirements, including having enough related artifacts to support comparison and at least one directed relationship that can be evaluated.
  - Families are unique across trials:
    - Trial 1 families do not appear in Trials 2 or 3.
    - Trial 2 families do not appear in Trial 3.
  - This produces **300 unique skill families** across the three trials.
  - Because similarity analysis and scanning are computationally expensive, the team is using sampled trials rather than attempting to process the full GitSkills population.

- Reviewed how **manual validation is sampled within each trial**.
  - The team does not manually inspect all 100 families in each trial.
  - The pipeline reproducibly selects a smaller set of artifact comparisons for manual review.
  - Reviewers will inspect the selected cases and record whether the automated analysis appears correct.
  - Manual findings will be incorporated into the final report and used to update the project’s limitations and threats-to-validity discussion.

- Assigned the three **Sprint 3 validation trials**.
  - Kyle will review **Trial 1**.
  - Christian will review **Trial 2**.
  - Vaisnavii will review **Trial 3**.
  - Jim has already run the Sprint 3 pipeline and committed the required trial outputs, so reviewers do not need to rerun the full pipeline before beginning validation.

- Kyle demonstrated the **manual-review setup and SkillTrace workflow**.
  - Sprint 3 outputs are available under the end-to-end pipeline Sprint 3 results directories.
  - Each trial contains the selected family list and the generated manual-review templates.
  - The two primary annotation files are:
    - The **relationship-pairs annotation template**.
    - The **directed-pairs annotation template**.
  - Reviewers should download the shared `reports.zip`, extract the generated JSON reports into the `apps/skilltrace/reports` directory, and launch `SkillTrace`.
  - `SkillTrace` can then be used to locate the relevant family, cluster, and artifact pair for each assigned manual-review case.

- Clarified the distinction between the two types of **manual annotation**.
  - **Relationship/lineage validation** evaluates whether the family-analysis process correctly identified the relationship between two artifacts.
  - Reviewers should determine whether:
    - The inferred direction appears correct.
    - The direction appears incorrect.
    - The analyzer was correct to leave the direction unknown when the evidence is ambiguous.
  - **Scanner validation** evaluates whether the security scanner and evidence-based risk indicators behaved correctly.
  - Reviewers should look for:
    - Correctly detected risky changes.
    - False positives.
    - Security-sensitive changes that appear to have been missed.
    - Whether the evidence and risk-indicator output accurately represents the underlying artifact change.
  - The relationship-pairs template is for validating lineage/family analysis, while the directed-pairs template is used for scanner validation.

- Reviewed the role of **front matter, diffs, scanner matches, and evidence** in `SkillTrace`.
  - Front matter is not included in the security scan.
  - Front-matter metadata may be used as supporting evidence for provenance or lineage direction.
  - Ordinary differences shown in the artifact diff do not necessarily represent security findings.
  - In the demonstrated interface:
    - Yellow-highlighted content represents differences between artifacts that were not necessarily detected by the scanner.
    - Green-highlighted content represents scanner-detected material.
    - The evidence view identifies findings that triggered one of the project’s evidence-based risk indicators.
  - Reviewers should therefore distinguish between a general text difference and an actual scanner/risk-indicator finding.

- Reviewed Christian’s initial **Trial 2 relationship validation** work.
  - Christian had already completed an initial review of approximately 15 relationship cases.
  - He found manually navigating to each pair in `SkillTrace` cumbersome.
  - To simplify the process, he created spreadsheet hyperlinks that open the corresponding comparison directly in `SkillTrace`.
  - The team confirmed that the link format works and considered it a useful convenience improvement.
  - Jim noted that similar links could potentially be generated automatically in future annotation files, although no change was committed during the meeting.

- Discussed Christian’s observation of apparently **benign artifact differences**.
  - Some reviewed pairs contained differences such as user-specific local file paths.
  - These differences may be visually apparent in a diff but are not automatically scanner findings.
  - The discussion reinforced the need to evaluate the correct annotation type:
    - Relationship review asks whether the inferred lineage/direction is reasonable.
    - Scanner review asks whether actual security-sensitive behavior was detected correctly.
  - Reviewers should avoid treating every textual difference as a false-positive scanner result.

- Reviewed available **manual-annotation documentation and prior examples**.
  - The manual annotation protocol is documented under `docs/instructions/`.
  - The protocol defines the expected values for the fields in the annotation templates.
  - Sprint 2 manual-review results are also available as examples of completed annotations.
  - Vaisnavii can use the Sprint 2 review files as a reference when completing Trial 3.
  - Christian offered to share his spreadsheet/link approach if it is useful to the other reviewers.

- Set a target for completing the **Sprint 3 manual validations**.
  - Kyle requested that all three trial reviews be completed by **Friday, November 13**.
  - Vaisnavii and Christian confirmed that the deadline is workable.
  - Completing validation by Friday will allow the team to incorporate the results into the report over the weekend before the Sprint 3 deadline.
  - Vaisnavii indicated that she may be able to complete her review earlier.

- Reviewed Christian’s current **pull requests and Windows environment issue**.
  - Christian submitted a pull request related to problems encountered when running the project from a OneDrive-managed Windows location.
  - He also submitted a pull request establishing additional mechanics/structure for the final report.
  - Jim will review both pull requests.
  - The team discussed avoiding development environments inside OneDrive-synchronized folders because Python virtual environments and repositories can contain many small files and may experience performance or file-access problems when continuously synchronized.
  - Christian will relocate his project repository/environment to a local directory outside the OneDrive-managed Desktop/Documents folders.

- Reviewed the status of the **final research report**.
  - The final report structure is being prepared while the team waits for the three Sprint 3 manual-validation result sets.
  - Once validation is complete, the findings will be incorporated into the report.
  - Validation results will also inform updates to the threats-to-validity and limitations sections.

- Discussed the upcoming **final presentation**.
  - Sprint 3 ends on November 18, but the project will still require a final presentation afterward.
  - The exact presentation deadline has not yet been confirmed; the team expects it to occur after Thanksgiving and near the end of the course.
  - For online students, the team expects the presentation may be submitted as a recorded video.
  - The tentative workflow is:
    - Create a shared slide deck.
    - Develop a script for the presentation.
    - Divide the slides among team members so everyone contributes.
    - Have each team member record their assigned section individually.
    - Send the individual recordings to Jim.
    - Jim will combine the recordings into a single final presentation video.
  - Zoom was suggested as a convenient tool for recording each individual section.

- Briefly reviewed other **course work and grading follow-up**.
  - Vaisnavii completed a draft of the separate product-scenario/UML assignment and shared it with the team for review.
  - The professor has indicated that he will review a previously disputed assignment grade that appears to have been based on requirements different from those stated during the course video.
  - The team does not expect additional action on that grading issue unless the instructor requests it.
  - The group is not yet certain whether additional course assignments or a final exam will be assigned after the project work.

- Confirmed the **remaining meeting schedule**.
  - The recurring meeting time has been changed to **4:00–5:00 PM ET** for the remaining meetings.
  - The new time works for the team and better accommodates Christian’s schedule.

## Decisions and Outcomes

- Sprint 3 will use **three independent trials of 100 unique skill families each**, for a total of 300 unique sampled families.
- Manual validation will be performed on reproducibly selected subsets of each trial rather than all 100 families.
- Validation responsibilities are divided as follows:
  - **Trial 1:** Kyle.
  - **Trial 2:** Christian.
  - **Trial 3:** Vaisnavii.
- Reviewers do not need to rerun the full Sprint 3 pipeline because the required results and reports have already been generated.
- The team will maintain two distinct validation activities:
  - **Relationship/lineage validation** for the family-analysis methodology.
  - **Scanner validation** for security findings, evidence, and risk indicators.
- Front matter will remain excluded from security scanning and used only where relevant to provenance/lineage analysis.
- General artifact differences should not be interpreted as scanner findings unless they are actually detected by the scanner/evidence workflow.
- The existing manual annotation protocol and Sprint 2 completed reviews will serve as the reference for Sprint 3 annotation.
- Christian’s direct `SkillTrace` comparison links are considered a useful workflow improvement, although automatic generation of those links is not required for the current sprint.
- All three Sprint 3 manual-validation reviews should be completed by **Friday, November 13, 2026**, so the findings can be incorporated into the report before the Sprint 3 deadline.
- Team members should avoid keeping the active repository and Python virtual environment inside OneDrive-synchronized Windows folders.
- The tentative final-presentation plan is to divide a shared slide deck among the team, record individual sections separately, and combine them into one final video.
- The remaining team meetings will be held from **4:00–5:00 PM ET**.
- **Sprint 3 remains due November 18, 2026.**

## Action Items

### Jim

- [ ] Review Christian’s pull request related to the Windows/OneDrive environment issue.
- [ ] Review Christian’s pull request establishing additional final-report structure/mechanics.
- [ ] Support Kyle, Christian, and Vaisnavii with questions about the Sprint 3 manual-validation process.
- [ ] Incorporate the completed validation findings into the final analysis, report, and threats-to-validity documentation.
- [ ] Coordinate the final presentation slide/script workflow once the instructor confirms the presentation requirements.
- [ ] Combine the team’s individual presentation recordings into the final video if the recorded-presentation format is required.

### Vaisnavii

- [ ] Complete the **Trial 3** relationship and scanner manual-validation annotations.
- [ ] Use the manual annotation protocol and Sprint 2 completed reviews as references when filling out the annotation templates.
- [ ] Complete the Trial 3 review by **Friday, November 13**, or earlier if possible.
- [ ] Share/review the separate product-scenario/UML assignment draft with the team as needed.

### Kyle

- [ ] Complete the **Trial 1** relationship and scanner manual-validation annotations.
- [ ] Assist Christian and Vaisnavii with `SkillTrace`, annotation fields, or validation questions as needed.
- [ ] Complete the Trial 1 review by **Friday, November 13**.
- [ ] Use the combined manual-validation findings to support the final report and evaluation of scanner/lineage accuracy.

### Christian

- [ ] Complete the remaining **Trial 2** scanner-validation annotations and finalize the relationship review.
- [ ] Complete the Trial 2 review by **Friday, November 13**.
- [ ] Share the spreadsheet/direct-link workflow with other team members if useful.
- [ ] Relocate the active project repository and Python environment to a local directory outside OneDrive-synchronized folders.
- [ ] Respond to feedback on the submitted environment and final-report pull requests.

### All Team Members

- [ ] Complete assigned manual-validation work in time for the results to be incorporated into the Sprint 3 report.
- [ ] Distinguish relationship/lineage validation from scanner/evidence validation when reviewing cases.
- [ ] Use `SkillTrace`, the manual annotation protocol, and the Sprint 2 examples when validating assigned cases.
- [ ] Raise questions in Discord or contact Jim/Kyle directly if a validation case or annotation field is unclear.
- [ ] Review the final report as Sprint 3 validation results are incorporated.
- [ ] Prepare to contribute an assigned section to the final recorded presentation once the presentation format is confirmed.
