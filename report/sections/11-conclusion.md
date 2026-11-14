# Conclusion and future work {#sec-conclusion}

We investigated whether related agent skills contain security-sensitive operations that were absent from an artifact inferred to have come earlier. Across three Sprint 3 trials, **63 of 300 sampled families (21.0%)** contained at least one supported risk indicator. The most widespread changes involved local script execution and external code or dependency acquisition. These findings highlight a practical concern: a skill can retain its familiar name and purpose while changing what it instructs an agent to run or retrieve.

To identify these changes, we developed a reproducible static-analysis pipeline that establishes plausible relationships between artifacts, compares their instructions and available supporting files, and evaluates differences against eleven defined risk indicators. Rather than treating every changed command or scanner match as a security concern, the method examines the underlying operations and preserves the evidence needed for review.

Initial manual-review notes identified possible detection gaps and disputed relationship decisions, but final adjudication is not documented. Our findings therefore remain automated, not confirmed vulnerabilities or verified copying histories, and cannot be generalized to all GitSkills families.

## Future work

Near-term work should focus on improving detection accuracy using the Sprint 3 manual-review findings. This includes addressing potential false positives and false negatives, refining existing rules, and clarifying risk-indicator definitions. Expanding the rules and indicators to recognize additional security-sensitive behaviors could also reveal risks that the current analysis does not capture. These changes should be evaluated against manually reviewed examples to measure their effectiveness.

Longer-term research could apply an expanded and validated set of indicators to larger samples of GitSkills artifacts. Comparing results across different rule sets, sampling strategies, and similarity thresholds would help determine how detection coverage influences the observed findings. Rather than attempting to build an exhaustive security scanner or reconstruct complete histories from live repositories, future research should focus on better characterizing the frequency and types of security-sensitive changes associated with agent-skill reuse. The broader goal is to strengthen our understanding of potential supply-chain exposure when adopting skills from external sources.

This study provides a reproducible starting point for identifying security-sensitive changes that deserve closer examination. **When adopting or updating an agent skill, understanding what changed can be just as important as understanding what the skill is intended to do.**
