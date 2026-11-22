# Sprint 3 Release — Post-Release Adjudication Note

**Add this note to the GitHub release description for the existing [`sprint3` tag](https://github.com/umdnp/csc580-project8/releases/tag/sprint3).** Do not move the tag or rewrite the original frozen trial outputs.

### Update after the November 17 Sprint 3 tag

The `sprint3` tag preserves the original Sprint 3 snapshot. Following that tag, the team completed adjudication of all **135 manually reviewed cases** (**90 directed comparisons** and **45 relationship cases**). The adjudicated inputs were applied to the saved cohorts **without rerunning the original security scans**. The later updates on `main` include final adjudicated CSVs, team decision notes, and computed validation summaries for all three trials.

Of the 90 directed reviews, **56** were fully assessed and **34** were not assessable. After excluding insufficiently supported direction and incomplete evidence, **29** directed comparisons qualified for indicator accuracy calculations. These produced **13 true positives**, **7 false negatives**, and **zero counted false positives**: **100% observed micro-precision (13/13)** and **65.0% observed micro-recall (13/20)**. The restricted precision calculation excludes **two adjudicated RI-003 false positives** whose comparison directions were uncertain. The 45 relationship reviews agreed with the analyzer's relatedness classification in **42** cases and disagreed in **3**.

The original automated totals (**63/300 families** and **340/2,157 primary comparisons** with supported indicators) remain frozen and unchanged. The review metrics describe only the eligible, deliberately selected review subset and do not establish population-wide scanner accuracy. The team also completed a separate clean-environment reproduction of all three Sprint 3 trials. This verification is distinct from applying the adjudicated CSVs to the saved summaries; it does not replace the original frozen research results.

See the current [research report](https://github.com/umdnp/csc580-project8/blob/main/report/final.pdf), [validation appendix](https://github.com/umdnp/csc580-project8/blob/main/report/appendices/C-validation-materials.md), and [reproducibility guide](https://github.com/umdnp/csc580-project8/blob/main/docs/instructions/reproducibility.md) for the final post-release evidence and remaining limitations.
