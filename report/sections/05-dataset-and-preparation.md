# Dataset and cohort

## Data source and unit of analysis

We use GitSkills version 1.0.0, released on Zenodo on August 10, 2026. Its July 2026 collection contains **3,797,117 file occurrences** from public GitHub repositories, including repeated copies of identical content [@gitskills]. The dataset calls scripts and other resources stored alongside `SKILL.md` **sibling files**. We import the released SQLite data into DuckDB for analysis.

Our starting unit is a **skill family**: qualifying artifacts with the same exact skill name, even when their descriptions differ. The shared name identifies candidates for comparison; it does not establish that they are copies of the same skill. Within a family, the similarity analyzer groups sufficiently related skill bodies into **clusters**. We then examine selected **directed comparisons** between related artifacts for which the available evidence supports a plausible earlier-to-later order. The relationship and direction methods are explained in the next section.

## Preparing comparison candidates

The project builds an `artifact_groupings` table from the GitSkills records. An artifact qualifies when its **frontmatter** (the YAML metadata at the start of `SKILL.md`) parses as valid, its instruction body is longer than 50 characters, and its content, name, and description are present. A candidate family must have at least two qualifying occurrences with the same name. Descriptions are normalized for supporting subgroups, but differences in description do not split a family during similarity analysis.

An earlier preparation audit established a larger pool of same-name candidates, but not all were eligible for the final study. Appendix A records the audit counts and links to the preparation SQL. The saved Sprint 3 sampling reports document the actual selection and replacement process.

## Selecting the three Sprint 3 trials

We analyzed **three non-overlapping, stratified random samples of 100 families each**. This is the final study population for the report; earlier Sprint 1 and Sprint 2 cohorts helped develop and test the method but do not contribute to the Sprint 3 results.

A family is eligible for selection only if it passes two checks:

1. **Distinct states:** At least two combinations of the main skill-file **hash** (an identifier derived from its exact content) and **sibling fingerprint** (a summary of known supporting-file contents) differ. Repeated copies of the same known state do not meet this requirement.
2. **Usable relationship:** The similarity analyzer can identify at least one primary directed comparison involving different main-file hashes or different *known* sibling hashes. A different hash alone does not establish relatedness or direction.

When a randomly drawn candidate fails the relationship check, the picker records the rejection and draws a replacement from the same size group. **Selection does not run the security scanner** and does not favor families with risk indicators. Families that fail eligibility are excluded from the study population, not counted as families with no risk.

We divided candidate families into five groups by their **total number of artifact occurrences**, including repeated copies. The allocation deliberately gives larger families more representation than they have in the candidate pool, so the study includes both ordinary and unusually large families without letting the largest ones consume the entire sample.

| Family size (artifact occurrences) | Per trial | Three trials |
| --- | ---: | ---: |
| Low: 2 | 20 | 60 |
| Medium: 3–15 | 55 | 165 |
| Large: 16–100 | 20 | 60 |
| X-Large: 101–500 | 4 | 12 |
| Extreme: 501 or more | 1 | 3 |
| **Total** | **100** | **300** |

: Family-size strata and allocation across the three trials

The trials use recorded random seeds **5801**, **5802**, and **5803**. Trial 2 excludes names selected in Trial 1; Trial 3 excludes names selected in both previous trials. Each trial saves its `families.txt` and `sampling_report.json`, preserving the selection and rejection record. These are separate, non-overlapping samples, but the exclusions mean they are not independent draws from an unchanged pool.

The allocation is **not proportional** to the wider candidate population. Our unweighted percentages therefore describe these 300 selected, relationship-eligible families; they must not be presented as population-wide estimates for GitSkills. The number of eligible families in each stratum after relationship screening has not been established for population weighting.

## What we analyzed

The three trials loaded **6,570 artifacts** with none skipped. Their similarity analysis selected **2,157 primary directed comparisons** in total. A *primary* comparison connects a derived candidate to at most one selected predecessor, using the graph method described in Section 6. We did not scan additional related directed edges in these trials, to limit repeated observations of similar changes within large families. Equivalent or direction-unknown relationships are retained for relationship review but are not assigned introduced/removed security behavior.

The main outcome is **family-level frequency**: how many sampled families contain at least one comparison with a supported risk indicator. We also report pair-level frequency using all analyzed primary directed comparisons as its denominator. The two measures answer different questions: how widely a signal appears across families versus how frequently it appears among selected comparisons. Comparisons within a family may share artifacts and are not independent historical events.

## Evidence availability and safe handling

The main skill bodies were available for all loaded artifacts, but commit dates and supporting-file content are not always available. A known empty sibling bundle is different from one whose contents could not be retrieved. We report unavailable files and partial evidence extraction rather than treating them as proof that no behavior exists.

All skills and bundled files are treated as untrusted data. We inspect stored content without running commands, installing dependencies, or retrieving referenced code. Before sharing extracted examples, potentially sensitive text must be reviewed and redacted where possible. The saved manifests record the dataset, rules, code revision, and inputs; numeric artifact IDs alone cannot identify the same content across database builds. Appendix E links the data dictionary and reproduction materials.
