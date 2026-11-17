# CSC 580 Group 8 – Meeting Minutes

**Date:** November 17, 2026  
**Time:** Evening  
**Duration:** Approximately 46 minutes  
**Attendees:** Jim Prantzalos, Kyle Cantrell, Christian Heiney  
**Absent:** Vaisnavii Mohanraj  
**Purpose:** Review remaining Sprint 3 and final-project work, resolve outstanding manual-validation and adjudication questions, finalize report/release tasks, and coordinate the prerecorded final presentation.

## Main Topics of Discussion

- Reviewed the remaining **Sprint 3 backlog and closeout stories**.
  - Story 9.1, covering the final research sample, was marked complete.
  - The final sample consists of the three Sprint 3 trials, and the required sampling methodology and supporting information are already documented.
  - Final reproducible tables and figures were also considered complete.
  - The primary remaining research item is final cleanup of the independent manual-validation results.
  - Other remaining closeout work includes the retrospective, presentation materials, repository tagging/release work, and final report refinement.

- Reviewed the status of **independent manual validation**.
  - The team confirmed that the manual-review work has been completed across the frozen Sprint 3 sample, but some entries warrant another careful review.
  - Reviewers should confirm that all relevant security-sensitive findings have been identified and that annotation fields are internally consistent.
  - Scanner logic that was previously identified as incorrect or incomplete has already been incorporated where appropriate.
  - At this stage, the team does **not** plan to continue changing the scanner for newly discovered edge cases.
  - New issues identified during the final review will generally be documented in **Threats to Validity** rather than triggering further scanner implementation changes.

- Discussed how to handle **not-assessable manual-validation cases**.
  - Some annotations were marked as not assessable because the available evidence was ambiguous, conflicting, or insufficient to support a confident determination.
  - Christian suggested whether these cases should be relabeled as "indeterminate."
  - The team decided that the existing terminology does not need to change.
  - Instead, every not-assessable annotation should contain a clear note explaining why the reviewer could not make a determination.
  - Christian confirmed that his not-assessable entries already contain explanatory notes.
  - Any recurring or significant reasons for cases being unassessable should also be reflected in the project's threats-to-validity discussion.

- Discussed **adjudication of manual-validation findings**.
  - The team reviewed uncertainty around how completed adjudication is represented in the annotation files.
  - For this project, adjudication means that a disagreement or issue discovered during manual review has been resolved by either:
    - Correcting the scanner when an implementation fix was appropriate; or
    - Documenting the unresolved limitation or disagreement in the report/threats-to-validity material.
  - The current annotation schema does not contain a dedicated adjudication field, which makes it difficult for automated review to determine whether all discovered issues have been resolved.
  - The team will use the annotation notes and report documentation to demonstrate how ambiguous or discrepant cases were handled rather than introducing a new schema change at this stage.

- Agreed to perform a final **consistency/completeness review of the report and annotations**.
  - Jim has been using AI-assisted review to check whether the final report and validation artifacts appear complete and whether unresolved items remain.
  - The automated review continued to raise questions about adjudication and the number of not-assessable cases.
  - Kyle will run the current report and completed validation files through the same type of review using the previously established validation criteria.
  - If the review identifies a genuine unresolved issue, the team will determine whether it requires clearer annotation notes or an update to the report/threats-to-validity section.
  - The goal is to ensure there are no unexplained or apparently pending validation issues before the report is considered final.

- Confirmed that the **frozen sample and analysis artifacts** remain aligned.
  - The team reviewed the backlog criterion requiring the annotations to match the frozen sample and analysis.
  - The sample used for the completed validation remains frozen and reproducible.
  - No additional sampling changes are planned for the final report.

- Reviewed the status of the **final research report**.
  - The report is substantially complete.
  - The main remaining refinement is incorporating any final clarification arising from the manual-validation/adjudication review.
  - Final manual-validation findings may result in updates to the threats-to-validity section and validation summary.
  - The team does not expect major changes to the research findings or methodology at this stage.

- Reviewed remaining **repository release tasks**.
  - The final Git tag/release should not be created until all remaining work has been merged and the repository is in its final state.
  - Jim is completing the Sprint 3 retrospective and other final deliverable/release tasks.
  - Repository tagging will occur after the final report, presentation materials, and other required artifacts are checked in.

- Discussed the structure and timing of the **final prerecorded presentation**.
  - The online-group presentation will be prerecorded and played during the professor's presentation sessions.
  - The team wants the final presentation to remain close to **20 minutes**, with approximately **25 minutes as an upper target**.
  - Because four team members will participate, most sections should remain near five minutes or less.
  - Kyle's section may require additional time because it includes the project results and a `SkillTrace` demonstration.
  - The presentation should move quickly through the slides and focus on the most important research story rather than attempting to explain every detail.

- Reviewed the tentative **presentation section assignments**.
  - Christian will present the opening/introductory portion of the deck.
  - Jim will continue from the introductory section into the project methodology.
  - Kyle will cover results/findings and the `SkillTrace` demonstration.
  - Vaisnavii's section includes the later validation/results material.
  - Each presenter should review the slides assigned to them and prepare their own natural-language script rather than reading generated presenter notes verbatim.
  - Christian will introduce the team and explain that the presentation is divided among the group members.

- Agreed on a simple **recording handoff approach**.
  - Team members do not need to wait for the previous presenter to finish recording before creating their own section.
  - Each section can use a simple verbal transition such as thanking the previous presenter before continuing.
  - This allows individual recordings to be created independently while still producing a coherent final video.
  - The team will provide individual recordings for final assembly once the slide deck is settled.

- Reviewed the **presentation content and opening story**.
  - The introductory slides explain the motivation for the research and the security risk posed by untrusted or modified skill files.
  - The presentation includes a real-world example involving malicious skill content to establish why the research question matters.
  - The team wants the opening to communicate the security problem clearly before moving into the methodology and technical results.
  - Kyle expects to demonstrate `SkillTrace` as part of his presentation section.

- Discussed the **visual design of the slide deck**.
  - Jim has prepared both:
    - A conventional editable PowerPoint-style deck; and
    - A higher-fidelity cybersecurity-themed version generated with AI-assisted presentation tooling.
  - The higher-fidelity version is visually stronger but is more difficult to edit because many slides are rendered as images.
  - The conventional version is easier to maintain and edit but is visually simpler.
  - Jim will make both versions available in the repository.
  - Vaisnavii, who had previously volunteered to work on presentation aesthetics, can review the two options and either select/refine one or create an alternative design.
  - The final visual style will be selected as a team.

- Discussed how **manual-validation changes could affect the slide deck**.
  - Most presentation content is considered stable.
  - The primary slide that may require revision is the validation-summary slide if the final counts of fully assessed versus not-assessable annotations change.
  - Vaisnavii's presentation section includes this portion of the deck, so any final count changes should be incorporated before recordings are finalized.

- Discussed **Thanksgiving-week scheduling and presentation timing**.
  - Several team members expect limited availability during the Thanksgiving holiday period.
  - The professor may select online groups for presentation beginning November 30.
  - The team would benefit from not being selected during the first couple of presentation days so that final recordings can be assembled and reviewed after the holiday.
  - Christian volunteered to email the professor requesting consideration for a slightly later presentation date and will copy the team.
  - The team understands that this is a request rather than a guaranteed schedule change.

- Reviewed the expected **final recording workflow**.
  - Team members should begin reviewing their assigned presentation sections and preparing scripts now.
  - Recordings should be completed as early as practical to avoid a last-minute dependency around the holiday.
  - The final deck and recording should be ready before the group's assigned presentation date.
  - Jim expects to assemble the individual recordings unless another team member is better positioned to complete the final edit.

## Decisions and Outcomes

- The final Sprint 3 research sample is complete and consists of the three documented trials.
- The scanner is effectively **frozen**; newly discovered edge cases will generally be documented as limitations rather than triggering new scanner development.
- Not-assessable validation entries will retain the existing terminology but must include explanatory notes describing why a determination could not be made.
- Manual-validation disagreements are considered adjudicated when they have either been addressed in the implementation or explicitly documented as a limitation.
- The team will not add a new adjudication column to the annotation schema at this late stage.
- Kyle will perform an additional completeness/consistency review of the final report and validation files to identify any genuinely unresolved validation or adjudication issues.
- The final report is substantially complete and should require only validation-related refinements and final cleanup.
- The Git tag/release will be created only after all final artifacts have been merged and checked in.
- The final presentation will be prerecorded and should target approximately **20 minutes**, with roughly **25 minutes as an upper limit**.
- Each team member will present a portion of the deck, with Kyle receiving additional time as needed for results and the `SkillTrace` demonstration.
- Presenters may record independently using simple verbal transitions between sections.
- Jim will make both the editable and higher-fidelity presentation versions available for final design review.
- Vaisnavii will review the presentation aesthetics and help determine the final slide style.
- The validation-summary slide will be updated only if the final manual-validation counts materially change.
- Christian will ask the professor whether the team can avoid being scheduled during the first couple of post-Thanksgiving presentation days.
- Final presentation recordings should be completed early enough to allow assembly and review before the group's assigned presentation date.

## Action Items

### Jim

- [ ] Complete the Sprint 3 retrospective and remaining final-deliverable work.
- [ ] Incorporate any newly identified manual-validation limitations into the threats-to-validity section.
- [ ] Review the final validation/adjudication findings after Kyle's completeness check.
- [ ] Finish the presentation content and make both slide-deck versions available to the team.
- [ ] Update the validation-summary slide if the final assessment counts change.
- [ ] Complete the final Git tag/release after all required artifacts are merged and finalized.
- [ ] Review assigned presentation slides and prepare/record the methodology section.
- [ ] Assemble the individual team presentation recordings into the final video if needed.

### Kyle

- [ ] Recheck the final manual-validation results for any cases that require clarification or additional notes.
- [ ] Run the completed report and validation artifacts through a final consistency/completeness review using the established validation criteria.
- [ ] Identify any genuinely unresolved adjudication or validation issues and report them to Jim.
- [ ] Review assigned presentation slides and prepare the results/findings section.
- [ ] Prepare the `SkillTrace` demonstration portion of the final presentation.
- [ ] Complete the assigned presentation recording early enough for final assembly and review.

### Christian

- [ ] Confirm that all not-assessable Trial 2 annotations contain clear explanatory notes.
- [ ] Complete any remaining minor cleanup to the manual-validation annotations.
- [ ] Email the professor requesting consideration for a presentation date later than the first couple of post-Thanksgiving presentation days and CC the team.
- [ ] Review the introductory presentation slides and prepare a concise presentation script.
- [ ] Introduce the team and explain the split presentation format in the opening section.
- [ ] Complete the assigned presentation recording early enough for final assembly and review.

### Vaisnavii

- [ ] Review the meeting minutes and any final manual-validation updates.
- [ ] Review the two available slide-deck styles and recommend/refine the final presentation aesthetic.
- [ ] Update the validation/results slide if the final manual-validation counts change.
- [ ] Review assigned presentation slides and prepare the validation/results section.
- [ ] Complete the assigned presentation recording early enough for final assembly and review.

### All Team Members

- [ ] Review assigned presentation slides and confirm comfort with the material before recording.
- [ ] Keep individual presentation sections concise so the complete video remains near the 20-minute target.
- [ ] Use natural-language scripts rather than reading AI-generated presenter notes verbatim.
- [ ] Use simple verbal transitions between presenters so recordings can be produced independently.
- [ ] Complete remaining validation/report cleanup before the final repository release is tagged.
- [ ] Provide presentation recordings early enough for final compilation and review before the assigned presentation date.
