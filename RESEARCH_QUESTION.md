# Research Question

## Topic

**Question 4: Skill Security and Supply-Chain Risk**

## Research Question

**Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

## Motivation

Agent skills can contain instructions involving commands, files, networks, scripts, and credentials. When skills are reused or modified, new security-sensitive behavior may be introduced without being obvious to someone adopting the skill.

Comparing stored instructions and associated resources in GitSkills can help identify changes that warrant security review.

## Expected Contribution

This study provides a static comparison method, eleven defined risk indicators, and exploratory evidence of candidate security-sensitive changes between related GitSkills artifacts. The indicators are review signals rather than confirmed vulnerabilities; their validated frequency and historical lineage remain unresolved.

## Interpretation and Feasibility

We interpret the research question as a comparison of stored instructions and associated resources between related artifacts. The assessment uses eleven defined [risk indicators](docs/decisions/RDR-010-evidence-based-risk-indicators.md) to identify specific introduced or changed operations, rather than treating new keywords or increased rule-match counts as sufficient evidence of risk.

GitSkills provides artifact content, repository information, and dates for assessing relatedness and comparison direction. Sharing a name does not establish reuse, and the designations **base** and **derived** describe comparison orientation rather than proven original authorship or direct copying. Equivalent and direction-unknown relationships are retained separately.

The study does not execute instructions, measure a causal effect of reuse, or attempt comprehensive security detection. Behavior outside the eleven indicators is not automatically a scanner error.

## Competing Explanation

Differences may reflect routine adaptation, packaging, or legitimate functionality. A reported indicator may identify an intended feature rather than unwanted exposure; it does not by itself establish malicious intent or increased security risk.
