
# Appendix C Validation scope and status {#app-c}

Each of the **three Sprint 3 trials** generated **30 directed-comparison review cases** (five from each of six strata) and **15 relationship-review cases** (five from each of three strata), using review seed **580**. The total is **90 directed cases and 45 relationship cases**. These samples come from the saved results for each separate 100-family trial; they are **not** additional data collected for the final analysis.

Directed review covers supported indicators, uncertain indicators, flagged comparisons without supported indicators, coverage-limited comparisons, sibling changes, and unflagged directed comparisons. Relationship review includes equivalent, ambiguous, and no-related-edge cases. The two reviews serve different purposes: relationship review examines the similarity and ordering decisions, while directed review examines extraction, source differences, RI judgments, and coverage.

Reviewers distinguish rule matches, extracted evidence, supported versus uncertain indicator decisions, missing evidence, and evidence for direction. A reported RI is a **false positive** when manual inspection does not support it under the defined indicator policy. A **false negative** requires a manually supported *in-scope* indicator that the scanner did not report as supported. A reviewer should not count a benign change outside RI-001 through RI-011 as a missed indicator merely because it is security-related in another sense.

Original independent annotations were preserved, and final team-agreed copies of all **90 directed** and **45 relationship** judgments were recorded as `adjudicated` and `complete`. The original selected pairs, automated outputs, and sample manifests were retained unchanged. The study's original manifests still have provisional approval metadata; the later team approval is documented separately in each trial's adjudication notes.

## Indicator review and accuracy

| Measure | Trial 1 | Trial 2 | Trial 3 | Total |
| --- | ---: | ---: | ---: | ---: |
| Directed reviews | 30 | 30 | 30 | **90** |
| `all_assessed` | 18 | 12 | 26 | **56** |
| `not_assessable` | 12 | 18 | 4 | **34** |
| Excluded: direction not supported | 0 | 6 | 6 | **12** |
| Excluded: incomplete coverage | 4 | 2 | 9 | **15** |
| Eligible for indicator metrics | 14 | 4 | 11 | **29** |
| True positives | 2 | 1 | 10 | **13** |
| False positives (counted) | 0 | 0 | 0 | **0** |
| False negatives | 3 | 1 | 3 | **7** |

: Adjudicated directed-review scope and indicator counts {#tbl-validation-review} {.wide}

The exclusions partition the 90 cases in the saved validation summaries; they do not mean that all review questions were answered in excluded cases. For the **29 eligible comparisons**, the computed eleven-indicator results yield **100% observed micro-precision (13/13)** and **65.0% observed micro-recall (13/20)**. Two indicator judgments in Trial 1 remain uncertain and are not counted as negatives. These metrics are conditional on relatedness, defensible direction, review scope, and evidence coverage. They apply only to this small stratified review subset, not the full trial population.

In two Trial 3 `mcp-builder` comparisons (base `3032753` to derived `3026710` and `3031464`), review rejected the saved RI-003 claim: reformatted references pointed to existing network destinations rather than newly introduced operations. Both comparisons had uncertain direction and thus were **excluded from the counted precision denominator**. The later scanner correction added targeted regression tests, but the original trial counts were not regenerated. Other examples reveal missed local wrapper-script invocations (`improve`), a missed network-related indicator (`health-bugs`), and additional network, dependency, and execution changes in a `tdd-migration-pipeline` supporting Python script. Missing sibling evidence and uncertain direction prevent some such cases from contributing to quantitative estimates.

## Relationship review

The **45** adjudicated relationship judgments produced **42 agreements and 3 disagreements** with the algorithm's relatedness classification (15/0, 15/0, and 12/3 across Trials 1–3). In Trial 3, three of the five selected `no-related-edge` cases were judged related, while the other two were judged not related. These results concern classification agreement with the tool, **not independently measured inter-rater agreement**, proof of copying, or a population-wide error rate. Ordering remained uncertain in many reviewed relationships.

The trial-level `review/summary.json` files hold the calculated `manual_validation` and `relationship_validation` outputs, with the pre-adjudication summaries preserved separately. Detailed original and final judgments, source observations, and unresolved evidence limitations are retained in the `manual-review/` folders. The [Manual Annotation Protocol](../../docs/instructions/manual_annotation_protocol.md) defines the review criteria; [Appendix E](#app-e) links the supporting repository artifacts.
