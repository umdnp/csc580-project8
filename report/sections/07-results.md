# Results

## Automated comparison outcomes

The saved run reports at least one supported indicator in **588 of 3,997 directed comparisons (14.7%)**, across 19 of the 30 provisional families. This is an automated result under the implemented indicator policy. It is not the rate of confirmed vulnerabilities, successful attacks, or independently validated modifications. The saved research summary and pair-level CSV are the sources for the tables in this section.

| Measure | Saved result |
| --- | ---: |
| Selected families / artifacts loaded | 30 / 1,151 |
| Directed pairs analyzed | 3,997 |
| Pairs with changed extracted evidence | 1,998 (50.0%) |
| Pairs with at least one supported RI | 588 (14.7%) |
| Pairs flagged for any reported reason | 2,241 (56.1%) |
| Pairs with incomplete evidence coverage | 206 (5.2%) |
| Ambiguous edges excluded from directional scanning | 2,244 |

The broader flagged total includes evidence and rule observations and must not be substituted for the supported-indicator total. Likewise, the 1,998 pairs with evidence changes include ordinary differences that do not support an RI. The gap between these measures illustrates why a detected difference is insufficient to answer the research question.

## Types of reported change

Local script execution (RI-010), network expansion/redirection (RI-003), and credential access/potential exposure (RI-007) occur most often in the automated output. Each row below counts pairs supporting that indicator at least once. A pair may appear in several rows; percentages are not portions of a mutually exclusive distribution.

| Indicator | Pairs | Percent of all 3,997 pairs |
| --- | ---: | ---: |
| RI-001 Download and execute | 96 | 2.40% |
| RI-002 Executed code source changed | 0 | 0.00% |
| RI-003 Network expanded or redirected | 381 | 9.53% |
| RI-004 Network security weakened | 22 | 0.55% |
| RI-005 Code or dependency acquisition | 179 | 4.48% |
| RI-006 Destructive or privileged file operation | 41 | 1.03% |
| RI-007 Credential access or potential exposure | 231 | 5.78% |
| RI-008 System or permissions modification | 53 | 1.33% |
| RI-009 Sensitive file-system access | 0 | 0.00% |
| RI-010 Local script execution | 413 | 10.33% |
| RI-011 External instruction dependency | 0 | 0.00% |

Zero supported observations for RI-002, RI-009, and RI-011 do not establish that those changes never occur. Their absence can reflect this cohort, limited evidence, matching logic, uncertain assessments, or the difficulty of associating operations across artifacts. Validation must inspect negative cases before concluding that a zero frequency demonstrates successful absence detection.

The assessor reports 5,551 supporting findings summed across comparisons. These are deduplicated constructs within pairs, not 5,551 globally unique actions. Repeated artifacts and additional edges can count related evidence again. The report uses the figure only to describe report volume, not as a measure of distinct harmful behavior.

## Edge selection and direction evidence

Primary edges contribute 468 comparisons, of which 81 have supported indicators (17.3%). Additional edges contribute 3,529 comparisons, of which 507 have indicators (14.4%). Most observations therefore come from comparisons beyond the single selected predecessor. Pooling them without an edge-type breakdown would obscure how the graph contributes to the reported frequency.

Direction is based on direct chronology for 237 pairs, equivalent-peer chronology for 996, repository boundaries for 1,046, containment for 1,713, and resolved source declarations for five. Containment alone accounts for 42.9% of comparisons and 401 of the 588 indicator-bearing pairs. Consequently, many apparent introductions depend on the weakest direction basis. These cases can show meaningful differences even where the historical order remains contestable.

Family contributions are also uneven. One family contributes 1,136 comparisons (28.4% of the cohort) and 298 indicator-bearing pairs (50.7% of all indicator-bearing pairs). This concentration makes the pooled rate sensitive to family selection and graph density. Appendix D provides the complete family and direction-basis tables so readers can inspect this imbalance rather than assume every family contributes equally.

## Coverage and complete-case description

Of the 3,997 pairs, 206 have incomplete evidence coverage, including 117 with missing sibling content. The remaining incompleteness can involve partial or unsupported extraction and other recorded evidence issues. The execution summary's 117 incomplete sibling comparisons is therefore narrower than the research summary's 206 pairs with incomplete evidence coverage; these are different fields, not interchangeable totals.

The pair-level table contains 3,791 comparisons labelled complete, with 484 indicator-bearing pairs (12.8%). Another 104 indicator-bearing pairs occur among the 206 incomplete comparisons. Restricting to complete-labelled cases changes the descriptive rate, but cannot correct selection bias or prove that the detector recognized all relevant operations. The main total of 588 includes both groups and should always be accompanied by this coverage distinction.

## Representative interpretation cases

**Equivalent installation syntax.** A reviewed development example replaces `bun add` with `npm install` for the same dependencies and sync workflow. Installation is already present, and no new registry or source is demonstrated. The rule can correctly identify both commands while RI-005 is a false positive for a newly introduced acquisition operation. An explicitly incorrect missing-sync example must not add independent positive support. This is a test of the existing RI definition, not a request to detect additional categories.

**A retained credential pattern.** A client SDK example adds another initialization block using a framework-exposed authentication-key variable. The base already contains the same key-based initialization pattern. The name may attract review, but its added occurrence alone does not establish introduced RI-007. A separate, newly credential-bearing outbound operation would need its own evidence. This case illustrates why keyword presence and a change in credential behavior must be judged separately.

**Download and permission changes.** Another example adds remote retrieval followed by an executable-permission change and invocation of the downloaded file. The saved assessor reports network expansion and permission modification. Inspection can ask whether acquisition or deletion also satisfies an existing indicator. However, a download-then-execute sequence is not automatically the direct interpreter pipeline defined by RI-001, and a newly introduced HTTP URL is not automatically RI-004's HTTPS downgrade. Payload format, unavailable content, and direction limitations must remain explicit.

These examples illustrate interpretation issues identified during development and review discussion. They are not a completed, independently adjudicated accuracy sample for the current frozen outputs. Appendix D provides the current cohort tables, while Appendix E identifies the underlying result artifacts.
