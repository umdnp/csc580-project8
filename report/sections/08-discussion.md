\clearpage

# Discussion

## Interpretation of Findings

The available empirical observations are from the purposeful Sprint 1 tool-validation sample, not a Sprint 2 population analysis. In its extraction workflow, 13 of 33 view-order adjacent comparisons had at least one positive rule-count delta, and those events summed to 77 additional rule matches. This shows that the current rules detect differences in security-sensitive text in some selected pairs. It does not show that 13 skills acquired new capabilities: some rules were already present in the earlier endpoint, and the notebook's adjacent-pair ordering does not establish lineage. Separately, the saved family workflow produced 17 directed comparisons from the same 43-artifact sample; direction is an evidence-based hypothesis, not proof of ancestry.

The Sprint 2 contribution available so far is a 13-case validation design, not a set of human judgments. Until those cases are reviewed and the approved Sprint 2 analysis outputs are generated, the report cannot say how often the method identifies supported changes, misses relevant behavior, or produces false positives.

## Comparison With Expectations

The exploratory evidence is consistent with the expectation that the sample contains both pairs with increased rule matches and pairs without such an increase. The family reports also preserve ambiguous and equivalent relationships instead of forcing every same-name candidate into an ordered comparison. These observations describe the selected sample and method behavior only. They do not test whether such changes are common across GitSkills, and no confirmed relationship or scanner-accuracy rate is available.

## Simpler and Competing Explanations

Positive count changes have several plausible non-malicious explanations. A later instruction may be longer or more detailed, may support a new legitimate task, or may include examples and documentation that contain commands, URLs, or credential terminology. A count can rise without the underlying capability being new, and changes in formatting or wording can alter regex matches. Similarity may reflect shared templates or common conventions rather than copying. Finally, the purposeful sample and its selection criteria emphasize informative cases rather than a population distribution.

## Security and Supply-Chain Implications

The pipeline can help reviewers prioritize changes for contextual inspection by preserving source identifiers, direction evidence, scanner rule IDs, and change summaries. Its most defensible use is as a static review aid: authors and adopters can inspect whether a changed instruction is necessary, what files or services it affects, and whether it introduces an unexpected operation. The current evidence does not establish how often such review would find a real vulnerability or prevent harm. No claim about malicious authorship, actual execution, or supply-chain propagation follows from a text match alone.

## Practical Recommendations

For researchers and tool maintainers, keep relatedness, direction, scanner output, and scan coverage as separate judgments; preserve unresolved and incomplete cases; and rerun reports when rule definitions or inputs change. For skill authors and adopters, review the actual changed instructions and their operational context, especially commands, network access, credential handling, file operations, package installation, and system changes. Treat a positive match as a prompt to investigate, not as an automatic rejection or a security verdict.

## Unexpected Findings

Within the Sprint 1 adjacent-pair output, 20 of 33 pairs had no positive rule-count delta, while the remaining 13 had one or more. Positive events were distributed across all six categories, with different counts by rule. This variation is useful for testing the reporting path but is not a stable ranking of category risk: the sample is small and purposeful, a pair may contribute several events, and the event count depends on rule behavior and text volume. The family workflow's smaller set of 17 directed edges also illustrates that candidate loading, view adjacency, and selected predecessor relationships are different analytic stages.

## Interpretation Boundaries

The measurements concern detected text patterns and their differences across selected artifact occurrences. They do not establish that instructions were executed, that an agent had the required permissions, that the referenced resources were sensitive, that an exploitable condition existed, or that authors intended harm. The relationship procedure does not prove copying, authorship, or causal propagation. Sprint 1 percentages are not population estimates; no Sprint 2 manual-validation metrics are available yet. These limits are material to every security and supply-chain interpretation in this report.