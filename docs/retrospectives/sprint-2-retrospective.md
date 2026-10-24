# Sprint 2 Retrospective

**Project:** CSC 580 Group Project – Mining AI-Native Software Engineering  
**Team:** Team 8  
**Sprint:** Sprint 2 – Implementation and Validation  
**Sprint Dates:** October 8 – October 28, 2026  
**Status:** Working draft for team review

> Detailed technical decisions are recorded separately in `docs/decisions/`. This retrospective focuses on what the team learned during Sprint 2, what changed as a result, and what we should carry forward.

## Sprint Goal

The goal of Sprint 2 was to turn our initial research approach into a working, testable pipeline for comparing related GitSkills artifacts and identifying security-sensitive changes.

That meant improving extraction and comparison, testing the method against real examples, and producing reproducible evidence while acknowledging the limits of the dataset.

## What We Accomplished

- Extended the related-skill comparison and scanner to preserve and compare the evidence behind rule matches.
- Improved extraction and normalization of commands, URLs, paths, and other source constructs.
- Expanded the sibling-scanning approach to cover added or changed files with available content, regardless of extension.
- Defined evidence-based risk indicators to distinguish security-sensitive changes from ordinary differences.
- Added automated and regression tests for data preparation, extraction, normalization, and comparisons.
- Developed validation and reporting workflows for reviewing scanner results and supporting preliminary analysis.
- Continued recording important research and implementation decisions in RDRs.

## What We Learned

### 1. Detecting a match is not the same as understanding a change

Two skills can have the same number of rule matches while using different commands, URLs, or file paths. Rule counts alone can miss meaningful differences.

We moved to **evidence-based scanning**, preserving and comparing the actual source constructs. We also separated three questions: what matched, what changed, and whether the change supports a defined risk indicator. A detected difference does not automatically imply a security threat.

### 2. Command detection requires context

Commands such as `more`, `less`, and `service` are also common words in prose. Keyword matching therefore produced false positives.

We refined extraction to consider command structure and surrounding text instead of relying on keywords alone. Manual validation is still needed to identify cases the rules may miss or misinterpret.

### 3. Sibling files require attention to file format and content availability

A character can mean different things depending on the file type: `#` may be a Python comment, a Markdown heading, or part of a JSON string. Applying one interpretation to every file can produce misleading results.

We refined parsing where format matters and kept changed sibling files eligible for scanning regardless of extension. When content is unavailable, we record that limitation rather than treating the file as safe or unchanged in behavior.

### 4. Extracting enough context without capturing too much is difficult

Short snippets sometimes omitted information needed to interpret a match; longer snippets could include unrelated text. Markdown backticks also caused problems when incomplete inline-code boundaries joined separate constructs or left stray backticks attached to URLs.

We improved extraction boundaries to preserve complete constructs and capture nearby context separately. Regression tests helped prevent these problems from recurring.

### 5. Line endings can affect parsing and comparison

Windows (`CRLF`) and Unix-style (`LF`) line endings caused inconsistencies in parsing and source positions, including around fenced code blocks.

We updated normalization and added tests so equivalent content is handled consistently without losing accurate source references.

### 6. Small data-preparation errors can affect research results

Our description normalization collapsed whitespace but sometimes left leading or trailing spaces, separating descriptions that should have been grouped together.

We corrected the normalization order and added regression tests. We also learned that rebuilding derived tables can change grouping identifiers and reported counts, so analysis outputs need to be tied to the data and implementation version that produced them.

### 7. Real examples reveal issues that constructed tests can miss

Reviewing actual comparisons exposed misleading matches, incomplete evidence, and gaps in content coverage. These were not always apparent in isolated unit tests.

We added regression cases and refined validation to consider relatedness, detected evidence, and risk indicators separately. We also learned to keep the selected review cases, validation protocol, and generated results aligned.

### 8. Preserving evidence requires safe reporting

Capturing the original source text improves traceability, but may also expose credentials or other sensitive values in generated reports.

We established an approach that preserves the evidence needed for internal comparison while redacting sensitive values in exported results. This helps keep the analysis useful without unnecessarily exposing source data.

## What Changed During Sprint 2

**We kept the original research question, but changed how we measure and interpret security-sensitive differences.**

The largest shift was from relying on rule counts to comparing source evidence and assessing changes through explicit risk indicators. Rule counts remain useful summaries, but are not sufficient on their own.

We also broadened our treatment of changed sibling files, improved format-aware extraction and normalization, strengthened regression tests, and made missing or uncertain evidence more visible in the results.

## What We Should Carry Forward

- Continue pairing automated tests with manually reviewed examples from the dataset.
- Distinguish **observed evidence**, **risk indicators**, and **confirmed security impact**; static scanning cannot establish execution or malicious intent.
- Report missing content, uncertain direction, and incomplete comparisons rather than treating them as negative findings.
- Record the dataset, code revision, and preparation steps used to generate results.
- Refine rules when validation identifies meaningful gaps, without expanding scope unnecessarily.

## What We Could Improve

- **Validate with real examples earlier.** Representative skill and sibling comparisons could expose parsing problems before they reach reporting.
- **Keep validation materials synchronized.** The reviewed cases, protocol, and generated outputs should stay aligned as scanner results and indicators change.
- **Allow more time for integration review.** Changes to extraction, family comparison, reporting, and validation should be tested together sooner.

## Priorities for Sprint 3

- Complete the analysis and produce final results addressing the research question, including robustness checks, sensitivity analysis, or meaningful subgroup comparisons.
- Complete manual validation and error analysis, documenting false positives, missed detections, and uncertain findings.
- Generate final figures and tables from the pipeline, and verify that documented setup steps reproduce the primary results.
- Complete the research report with citations, separating findings from interpretation and addressing dataset bias, measurement error, confounding, missing data, reproducibility, and generalizability.
- Prepare a documented repository release, with major artifacts traceable to issues, commits, pull requests, and research decisions.
- Prepare the final demonstration and presentation, and identify the team's most important process improvement in the Sprint 3 retrospective.

## Team Input Before Finalizing

Each team member should review this draft and confirm that it reflects the sprint's actual work.

- [ ] Add any significant lesson or blocker that is missing.
- [ ] Confirm the status of the validation sample, preliminary results, and research report update.
- [ ] Confirm that at least one Sprint 2 pull request was reviewed by another team member.
- [ ] Revise anything described as completed that remains in progress at the sprint review.

## Summary

Sprint 2 showed that detecting a command, URL, or file operation is easier than accurately interpreting what changed and why it matters. Real data exposed ambiguity in command usage, file formats, source boundaries, line endings, and content availability.

We responded by moving to evidence-based comparisons, improving extraction and normalization, strengthening tests and validation, and treating uncertainty more explicitly. Most importantly, we learned to distinguish **detecting a difference from establishing its security significance**—a stronger foundation for the final analysis in Sprint 3.
