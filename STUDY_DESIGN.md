# Study Design: Units, Population, Sample, Variables, and Outcomes

**Status:** Sprint 1 research design  
**Source dataset:** `agent_skills_release.db`

## Purpose

This document defines how the project will measure whether modified or reused GitSkills introduce security-relevant behavior that was absent from an earlier version or source artifact. It specifies the unit of analysis, population, sample, variables, and outcome measures required to answer the research question.

The threat model and detection-rule catalog are still under development. This design therefore refers to generic rule identifiers and rule categories rather than assuming a final list of checks. New rules and categories may be added without changing the overall measurement design.

## Unit of Analysis

### Primary Unit: Ordered Skill Comparison

The primary unit of analysis is one ordered comparison between two related, content-bearing skill artifacts:

- **Base artifact:** the earliest identified version or source content in the relationship.
- **Derived artifact:** the later, reused, or modified content being compared with the base.

The ordering is represented as:

base artifact -> derived artifact

The static analyzer produces a rule-match and category profile for both artifacts. The comparison stage then determines which detected rules and categories were introduced, removed, or retained in the derived artifact.

An ordered comparison is eligible when:

1. Both artifacts have analyzable stored content.
2. The extraction pipeline identifies a relationship between them using the project's documented relationship method.
3. Available evidence supports their base-derived ordering.
4. Both artifacts can be processed by the same scanner version and rule catalog.

The extraction pipeline will retain the evidence and method used to establish each relationship so that uncertain or invalid comparisons can be reviewed and excluded according to documented criteria.

### Secondary Processing Unit: Unique Content SHA

One unique content SHA is the secondary processing unit. Identical content does not need to be scanned repeatedly. The pipeline may scan each unique SHA once, cache its resulting profile, and reuse that profile in every applicable artifact occurrence and base-derived comparison.

SHA deduplication is a computational optimization, not statistical sampling. Artifact occurrences, repository occurrences, and comparison relationships will remain available after profiles are joined back to the complete extracted data.

## Population

### Source Population

The source population is all GitSkills artifact records contained in `agent_skills_release.db`.

### Analyzable Artifact Population

The analyzable artifact population is all records in the source population that contain stored skill content that the static analyzer can process.

### Eligible Comparison Population

The population used to answer the research question is all ordered base-derived comparisons that can be extracted from `agent_skills_release.db` and that satisfy the eligibility criteria defined above.

Artifacts without analyzable content or without an identifiable and ordered relationship remain part of the source population but are not part of the eligible comparison population. The pipeline will report how many records and candidate relationships are excluded and the reasons for exclusion.

## Sample and Analysis Strategy

### Automated Analysis

The automated analysis will attempt a census of the eligible comparison population rather than selecting a statistical sample. Every eligible base-derived comparison extracted from `agent_skills_release.db` will be processed by the comparison pipeline.

During development, smaller reproducible datasets may be used to test and debug the pipeline. These development datasets are not the research sample and will not replace the final population-level analysis.

### Manually Constructed Test Fixtures

Manually constructed base and derived skills will be used as test fixtures to verify that the scanner and comparison logic behave as expected when known patterns are introduced, removed, or retained. These fixtures are software tests and are not empirical observations from the GitSkills population.

### Manual Validation Sample

The team will manually review a stratified sample of at least 100 eligible base-derived comparisons from the automated results. The sample will contain:

- at least 50 comparisons for which the scanner reports one or more newly introduced rules or categories; and
- at least 50 comparisons for which the scanner reports no newly introduced rules or categories.

Within those groups, the sample will include the relationship types and scanner categories present in the results. Selection will use a recorded random seed after the strata are defined. If a stratum contains fewer cases than its allocation, all cases in that stratum will be reviewed and the remaining allocation will be redistributed using a documented procedure.

Manual reviewers will evaluate:

- whether the base-derived relationship and ordering are supported by the retained evidence;
- whether each reported rule match corresponds to the text identified by the scanner;
- whether reported category assignments are appropriate;
- whether a reported introduction was absent from the base and present in the derived artifact;
- whether an unflagged comparison contains a relevant introduction missed by the current rules; and
- whether the case should be labeled a true positive, false positive, false negative, true negative, or ambiguous under the documented threat model.

The validation sample may be expanded if early review identifies unstable rules, poorly represented relationship types, or categories requiring additional evidence.

## Variables

Variables are recorded at the artifact, relationship, scanner-profile, and comparison levels. Exact database column names will be recorded in `DATA_DICTIONARY.md` after they are verified against the implemented extraction pipeline.

### Artifact Identification Variables

For both the base and derived artifacts, the pipeline will retain available identifiers and metadata needed for traceability, including:

- artifact identifier;
- repository identifier;
- artifact path;
- declared skill name, when available;
- content SHA;
- content or a safe reference to the analyzed content; and
- available timestamp, commit, or ordering metadata used by the relationship method.

### Relationship Variables

Each ordered comparison will record:

- comparison identifier;
- base artifact identifier;
- derived artifact identifier;
- relationship type;
- same-repository or cross-repository status;
- relationship-detection method;
- evidence supporting the relationship;
- evidence supporting base-derived ordering;
- relationship confidence or review status, if used by the implemented method; and
- eligibility or exclusion status and reason.

### Rule Catalog Variables

Each scanner rule will be defined in the evolving rule catalog. A rule definition should include:

- stable rule identifier;
- rule name and description;
- higher-level security-relevant category;
- detection logic or pattern reference;
- severity or review priority, if the threat model adopts one;
- known false-positive conditions;
- example positive and negative cases; and
- rule-catalog version.

The study design does not depend on any particular rule identifier or fixed set of categories. Results will be produced from the rule catalog used for a given pipeline run, and each run will record that catalog's version.

### Artifact Profile Variables

For each base and derived artifact, the scanner will produce a profile containing:

- set of matched rule identifiers;
- set of matched security-relevant categories;
- match count by rule and category;
- total matched-rule count;
- total matched-category count;
- match locations or evidence needed for validation and safe reporting; and
- scanner and rule-catalog versions.

### Comparison Variables

For each ordered comparison, the pipeline will derive:

- introduced rule identifiers: rules matched in the derived artifact but not the base;
- removed rule identifiers: rules matched in the base artifact but not the derived;
- retained rule identifiers: rules matched in both artifacts;
- introduced categories;
- removed categories;
- retained categories;
- number of introduced rules;
- number of introduced categories;
- indicator for at least one introduced rule;
- indicator for at least one introduced category; and
- overall comparison result under the current threat model.

The rule-level and category-level variables are both necessary. A derived artifact may introduce a new rule within a category that was already present in the base, which would be visible at the rule level but not as a newly introduced category.

## Outcome Measures

### Primary Outcome

The primary outcome is the proportion of eligible base-derived comparisons in which the derived artifact contains at least one detected security-relevant rule or category that was absent from the base artifact.

Two related introduction rates will be reported:

\[
\text{Rule introduction rate} =
\frac{\text{eligible comparisons with at least one introduced rule}}
{\text{eligible comparisons analyzed}}
\]

\[
\text{Category introduction rate} =
\frac{\text{eligible comparisons with at least one introduced category}}
{\text{eligible comparisons analyzed}}
\]

### Secondary Outcomes

Secondary outcome measures will be generated dynamically from the versioned rule catalog and may include:

- count and percentage of comparisons introducing each rule;
- count and percentage introducing each security-relevant category;
- distribution of introduced-rule counts per comparison;
- distribution of introduced-category counts per comparison;
- count and percentage of comparisons with removed signals;
- count and percentage with retained signals but no introduced signals;
- count and percentage with no detected profile change;
- introduction rates by relationship type;
- introduction rates for same-repository and cross-repository relationships; and
- number of distinct artifacts, content SHAs, and repositories represented in the analyzed comparisons.

When repeated content or relationships could affect a measure, results will identify whether the denominator consists of comparison occurrences, unique artifact relationships, or unique content-SHA pairs.

### Validation Outcomes

Manual validation will report:

- confirmed and rejected relationship counts;
- ordering disagreements;
- true-positive, false-positive, false-negative, true-negative, and ambiguous counts;
- precision and other validation metrics supported by the reviewed sample;
- results by rule, category, or relationship type when the sample size supports that breakdown; and
- representative failure modes and reasons for incorrect or ambiguous results.

Validation findings may lead to rule revisions. When rules change, the rule-catalog version will change and affected analyses will be rerun so that reported results correspond to one documented scanner and rule-catalog version.

## Interpretation Boundary

An introduced rule or category is a static risk signal. It indicates that the derived artifact contains a security-relevant instruction pattern that the scanner did not detect in the base artifact under the same rule catalog. It is not, by itself, proof that the derived skill is malicious, vulnerable, exploitable, or unsafe.

The study will distinguish scanner observations from conclusions about intent or real-world impact. It will not execute untrusted instructions or scripts from the dataset.

## Risk-Signal Interpretation Disclaimer

A detected risk signal indicates that a skill contains an instruction pattern identified as security-relevant by the project's current rule catalog. It does not prove that the skill is malicious, vulnerable, exploitable, or unsafe.

Likewise, an introduced risk signal means that the scanner detected a rule or category in the derived artifact that it did not detect in the corresponding base artifact. This is a comparison of static artifact content, not evidence that the instruction was executed or caused harm.

The available evidence may not establish:

* whether the instruction is executable in the intended environment;
* whether an agent or user ever executed it;
* whether execution requires user approval or additional permissions;
* whether security controls would prevent or restrict the behavior;
* whether a referenced file, script, command, credential, or network resource is harmful;
* whether the behavior creates an exploitable condition; or
* whether the artifact's author intended malicious behavior.

Many legitimate skills require commands, file operations, network access, scripts, or authentication instructions to perform their intended functions. The project will therefore describe scanner findings as **security-relevant capabilities**, **risk signals**, or **patterns requiring review**. Terms such as **malicious**, **vulnerable**, and **exploitable** will be used only when supported by additional evidence beyond a static rule match.
