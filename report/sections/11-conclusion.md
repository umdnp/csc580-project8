# Conclusion and future work {#sec-conclusion}

We investigated whether related agent skills contain security-sensitive operations absent from an artifact inferred to have come earlier. Across three Sprint 3 trials, **63 of 300 sampled families (21.0%)** contained at least one supported risk indicator, most often involving local script execution or external code or dependency acquisition. Skills with familiar names and similar purposes can contain different instructions about what an agent should run or retrieve.

Our static-analysis pipeline infers plausible relationships and comparison directions, compares skill instructions and available supporting files, and evaluates changed operations against **eleven defined risk indicators**. It distinguishes changes in underlying operations from differences in text or rule-match counts and retains evidence for human review.

Team adjudication of **90 directed and 45 relationship reviews** identified unsupported detections, missed indicators, and disagreements about relatedness. As [Section VII](#sec-evaluation) explains, accuracy calculations apply only to a restricted review subset and exclude some confirmed errors because comparison direction is uncertain. The feedback prompted a targeted scanner fix, but the frozen Sprint 3 counts were not recomputed. Together, the results provide **signals for security review**, rather than evidence of malicious activity.

## Future work

Near-term work should improve recognition of local-script invocations, operations in supporting files, and network or browser activity. Such changes should be tested against the adjudicated examples, including the resolved RI-003 formatting cases, and evaluated under a separately recorded configuration without replacing the frozen Sprint 3 results.

Longer-term research could validate additional risk indicators on larger, differently sampled cohorts. Comparing rule sets, sampling strategies, and similarity thresholds would help establish how these choices affect detection coverage and observed rates. This would help us better characterize security-sensitive changes associated with agent-skill reuse.

This study provides a reproducible starting point for identifying security-sensitive changes that deserve closer examination. **When adopting or updating an agent skill, understanding what changed can be just as important as understanding what the skill is intended to do.**
