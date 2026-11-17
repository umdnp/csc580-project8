# Sprint 3 Retrospective

**Project:** CSC 580 Group Project – Mining AI-Native Software Engineering  
**Team:** Team 8  
**Sprint:** Sprint 3 – Analysis, Integration, and Communication  
**Sprint Dates:** October 29 – November 18, 2026  
**Status:** Final

> Detailed technical decisions are recorded separately in `docs/decisions/`. This retrospective focuses on what we learned and our most important process improvement.

## Sprint Goal

Our goal was to turn the working scanner and preliminary findings into a well-supported research study. This meant expanding the analysis, checking the reliability of our results, conducting manual validation, and preparing the report and presentation.

## What We Accomplished

- Analyzed **three reproducible, non-overlapping samples of 100 skill families each**, expanding beyond the Sprint 2 cohort.
- Compared primary-edge and all-edge scanning to balance analysis time and evidence coverage.
- Saved family lists, settings, and results so the analysis can be inspected and reproduced.
- Organized manual review into separate checks of **artifact relationships** and **scanner findings**.
- Assigned reviewers to each trial and used shared annotation guidelines and SkillTrace reports.
- Strengthened testing, documented limitations, and incorporated results into the research report and presentation materials.

## What We Learned

### 1. More comparisons do not always produce better evidence

In our 30-family comparison, primary-edge scanning reduced directed comparisons from **3,997 to 468** while retaining **43 of 44** observed family–risk-indicator combinations. This made a larger study practical. We also documented what the faster approach could miss instead of treating the two methods as identical.

### 2. Random samples still need careful selection

Not every family contains distinct artifacts or a usable comparison. We refined the Family Picker to check eligibility, sample across family sizes, and save the selections and random seeds. We also recognized that our sampling choices limit how broadly we can apply the findings.

### 3. Manual review needs consistent guidelines and easy access to evidence

Reviewing an artifact relationship is different from checking a scanner finding. The shared annotation protocol helped reviewers make that distinction and record their judgments consistently. We also learned that direct links to comparisons in SkillTrace can save time during review.

### 4. Reproducibility involves more than rerunning the code

To reproduce our findings, we need the same dataset preparation, sample, settings, code version, and review records. Documenting these together made it easier to explain why results may differ across runs or scanner revisions.

## Most Important Process Improvement

**Our biggest process improvement was establishing a structured, shared validation process rather than relying primarily on automated testing and informal review.**

In Sprint 1, we focused on making the research question workable. In Sprint 2, real examples showed us that automated tests and scanner matches were not enough to support our conclusions. We recognized that we needed earlier validation and better coordination between analysis, testing, and reporting.

In Sprint 3, we acted on those lessons. We generated saved trial results, divided manual review among team members, and used the same annotation protocol to examine relationships and scanner findings. This gave us a clearer way to identify problems, discuss uncertain cases, and connect the report's conclusions to the underlying evidence.

**The process we want to carry forward is simple:** save the data and settings, generate evidence for review, assign reviewers, resolve or document disagreements, and then use the reviewed results in the report. This makes the work easier to share, reduces rework, and improves confidence in our findings.

## What We Could Improve

- **Review results earlier.** Schedule validation checkpoints before report writing is nearly complete, leaving more time to address findings.
- **Simplify manual review.** Include direct SkillTrace links in generated annotation files so reviewers can open comparisons without searching for them.
- **Coordinate changes more closely.** Agree on a point to freeze analysis settings and confirm that the report, figures, and validation results all use the same version.

## What We Should Carry Forward

- Continue using reproducible samples, saved settings, and controlled comparisons.
- Keep **observed differences**, **risk indicators**, and **confirmed security impact** separate when reporting results.
- Pair automated tests with independent manual review of real examples.
- Document important decisions and limitations, and keep research evidence traceable to repository artifacts.

## Summary

Sprint 3 helped us move from a working implementation to a more complete, evidence-based study. By expanding the sample, testing our analysis choices, and sharing validation work, we improved both the research and the way we worked together. Our most important lesson is to **build validation and integration into the process from the beginning**, not leave them until the end.

## Supporting References

- [RDR-013: Sprint 3 Sampling and Edge Selection](../decisions/RDR-013-sprint3-sampling-and-edge-selection.md)
- [RDR-014: Stratified Family Sampling Method](../decisions/RDR-014-stratified-family-sampling-method.md)
- [Manual Annotation Protocol](../instructions/manual_annotation_protocol.md)
- [End-to-End Reproducibility Instructions](../instructions/reproducibility.md)
