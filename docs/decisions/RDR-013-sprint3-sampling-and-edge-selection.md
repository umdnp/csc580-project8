# RDR-013: Sprint 3 Sampling and Edge Selection

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-11-07 |
| **Type** | Research methodology |
| **Related work** | Question 4, Sprint 3, RDR-006, RDR-007, RDR-010, RDR-012 |
| **Evidence** | `notebooks/end_to_end_pipeline/sprint2/results/` |
| **Supersedes** | None; defines the Sprint 3 analysis sample rather than the earlier validation sample |

## Context

Question 4 asks whether modified or reused skills introduce security-sensitive behavior absent from an earlier artifact. To understand how often these changes appear across GitSkills, we need to examine a broad range of skill families without allowing a few large families to dominate the results.

The initial 30-family analysis scanned all directionally supported relationships. This included selected predecessor relationships (**primary edges**) and other related, directed comparisons (**additional edges**). Additional edges can reveal useful changes, but they also produce many comparisons among artifacts from the same family.

We evaluated whether primary edges would provide enough evidence for a broader Sprint 3 study.

## Decision Drivers

- Study more families rather than repeatedly comparing related artifacts within a smaller set.
- Keep the unit of analysis and reported indicator rates clear.
- Check whether findings are consistent across separately selected random samples.
- Preserve a way to assess what primary-only analysis may miss.
- Keep selection, analysis, and validation reproducible.

## Decision

> **Use three non-overlapping, stratified random samples of 100 skill families each for the main Sprint 3 analysis. Scan primary directed edges only, and use an all-edge analysis of a smaller sample as a robustness check.**

Each trial will use the same family-selection criteria, dataset snapshot, similarity settings, scanner rules, and indicator definitions. Its selection seed and family list will be recorded so the trial can be reproduced. Families will not be repeated across trials.

**Family-level prevalence will be the primary measure:** the proportion of sampled families with at least one supported occurrence of a given risk indicator. We will also report the proportion of primary directed pairs containing each indicator. Reporting both measures shows how widely an indicator appears across families and how often it appears in the analyzed relationships.

We will present the three trials separately to assess consistency, then combine their counts for overall estimates rather than simply averaging pair-level percentages. Because families are sampled within size strata, any claim about the wider eligible GitSkills population must account for the sampling proportions. We will estimate uncertainty by resampling families within their size strata.

For the robustness check, we will select approximately 20–30 families across the sampled size strata and compare `primary` with `all` using the same scanner version. Manual validation will be used to assess whether reported indicators represent meaningful security-sensitive changes.

## Evidence

The original 30-family analysis covered 1,151 artifacts. Comparing primary and additional edges **within that same scanner run** gives the following results:

| Measure | All edges | Primary edges |
| --- | ---: | ---: |
| Directed comparisons | 3,997 | 468 |
| Distinct detected RI categories | 8 | 8 |
| Family–RI combinations | 44 | 43 |

Primary edges reduced the comparison count by **88.3%** while retaining **43 of 44** observed family–indicator combinations. The exception was RI-005 in `neurokit2`, detected only on additional edges. This shows that primary-only analysis retains much of the observed indicator coverage, but not all of the evidence.

Large families also account for many additional comparisons. For example, `seo` contributed 1,136 all-edge comparisons but only 88 primary comparisons. Using primary edges reduces this imbalance, although it does not make relationships within a family independent.

A later primary-only run used updated scanner rules, so differences between that run and Sprint 2 cannot be attributed solely to edge selection. The controlled comparison above uses one scanner version.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Analyze fewer families with `all` edges | Not selected for the main study | Preserves more within-family comparisons but gives less breadth and can overrepresent large families. |
| Analyze 300 families with `primary` edges | **Selected** | Broadens family coverage while retaining most indicator patterns observed in the initial comparison. |
| Omit additional edges entirely | Not selected | Additional edges may expose distinct changes and remain useful for a robustness check. |

## Consequences and Limitations

- Primary edges are **inferred** predecessor relationships, not verified historical ancestry. Additional edges may contain distinct security-sensitive changes that the main analysis excludes.
- Risk indicators are scanner observations requiring interpretation, not confirmed vulnerabilities, malicious behavior, or probabilities of actual supply-chain harm.
- Pair-level observations within a family are related. Large families can still contribute more pairs, so pair-level rates must not be treated as independent observations.
- Families without eligible primary relationships will be reported separately so they are not mistaken for families with no detected changes.
- Stratified sample proportions may differ from the eligible GitSkills population. Unweighted results describe the sampled families unless the design supports broader inference.
- Similar results across three trials would support stability under this sampling design, not prove that the estimates generalize to every GitSkill.
- Scanner changes can alter indicator counts. Comparisons used to evaluate edge selection must hold the scanner version and settings constant.

## Follow-up Actions

- Select and record three distinct 100-family samples, including their seeds and stratum allocations.
- Run the same primary-edge pipeline for all three samples and preserve their separate results.
- Report family-level prevalence, pair-level rates, trial-to-trial variation, and appropriately weighted pooled estimates with uncertainty.
- Complete manual review of selected findings and examine false positives and missed behavior.
- Compare primary and all edges on a smaller stratified subset, reporting indicator patterns that appear only on additional edges.

## Revisit Criteria

Revisit this decision if the robustness check finds substantial indicator patterns missed by primary edges, if the sampling design cannot support the intended population claims, or if validation shows that the selected predecessor relationships are unsuitable for assessing security-sensitive changes.
