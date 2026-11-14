# Conclusion and future work {#sec-conclusion}

We investigated whether related agent skills contain security-sensitive operations that were absent from an artifact inferred to have come earlier. Across three Sprint 3 trials, **63 of 300 sampled families (21.0%)** contained at least one supported risk indicator. The most widespread changes involved local script execution and external code or dependency acquisition. These findings highlight a practical concern: a skill can retain its familiar name and purpose while changing what it instructs an agent to run or retrieve.

To identify these changes, we developed a reproducible static-analysis pipeline that establishes plausible relationships between artifacts, compares their instructions and available supporting files, and evaluates differences against eleven defined risk indicators. Rather than treating every changed command or scanner match as a security concern, the method examines the underlying operations and preserves the evidence needed for review.

Initial manual-review notes identified possible detection gaps and disputed relationship decisions, but final adjudication is not documented. Our findings therefore remain automated, not confirmed vulnerabilities or verified copying histories, and cannot be generalized to all GitSkills families.

## Future work

In the near term, a next scanner version could use Sprint 3 review examples as regression cases: recognize local script invocations such as `scripts/tool.sh`, clarify whether explicit browser launches fall within RI-003, and avoid treating reformatted URLs to existing hosts as new destinations. Better analysis of added or changed sibling-file content and checks of similarity thresholds against manually reviewed relationships would also address observed limitations. A larger, independently adjudicated review sample could then help assess detection accuracy. These improvements are **not** part of the frozen results reported here.

Longer-term work could use fuller Git histories and provenance evidence to strengthen earlier-to-later ordering, and match related skills across different names to capture renamed or repackaged copies. Language-aware code analysis could identify indirect commands and dynamically constructed network operations that text patterns miss. Larger samples, alternative edge-selection policies, and population-aware estimates could test how broadly the findings apply. Ultimately, a review tool integrated into skill adoption or updates could present the changed operations, their source context, and unresolved evidence to developers before they trust a skill.

The study provides a practical starting point for identifying changes that deserve closer examination. **When adopting or updating an agent skill, understanding what changed can be just as important as understanding what the skill is intended to do.**
