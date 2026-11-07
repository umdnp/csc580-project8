# RDR-014: Stratified Family Sampling Method

| Field | Value |
| --- | --- |
| **Status** | Accepted |
| **Date** | 2026-11-07 |
| **Type** | Research methodology and implementation |
| **Related work** | Question 4, Sprint 3, RDR-003, RDR-004, RDR-007, RDR-013, `family_picker` |
| **Evidence** | DuckDB exploration of `artifact_groupings` and `artifacts`; `src/gitskills/sampling/families.py`; `notebooks/end_to_end_pipeline/` |
| **Supersedes** | None; specifies the family-selection method for RDR-013 |

## Context

RDR-013 establishes three non-overlapping samples of 100 skill families for Sprint 3. The GitSkills database contains **847,539 distinct artifact names**, but not every name has multiple artifacts or a usable comparison. We need to identify eligible families before selecting the samples.

Family sizes vary considerably. A sampling method should cover both common and unusually large families without allowing the largest to dominate the work. The team also needs to reproduce each trial and explain why families were included or rejected.

## Decision Drivers

- Select families with at least one usable primary directed comparison.
- Cover different family sizes while keeping the analysis practical.
- Produce 300 distinct families across three reproducible trials.
- Separate candidate screening from relationship evidence and security findings.
- Record selection criteria, exclusions, and validation results.
- Use the same sampling method in the CLI and notebook.

## Decision

> **Use stratified random sampling to select three non-overlapping sets of 100 exact-name families. Screen candidates using distinct content hashes, require at least one usable primary directed relationship, and allocate each sample across five size groups using a 20/55/20/4/1 distribution.**

### Family eligibility

A **family** includes artifacts with the same exact skill name, even if their descriptions differ. Descriptions can change as skills evolve, and the analyzer already compares artifacts across the entire same-name family.

Selection has two stages:

1. **Database screening:** Find families with at least two distinct combinations of `file_sha` and `sibling_content_sha`. Repeated copies of the same state do not count as distinct variants.
2. **Relationship validation:** Require at least one **primary directed relationship** between artifacts with different `SKILL.md` hashes, or with the same `SKILL.md` hash and different, known sibling-content hashes. Use the same similarity and direction policy as the analysis pipeline.

A different hash state does not, by itself, establish a related or directed comparison. Likewise, missing sibling information is unknown, not evidence that bundled content changed.

When a candidate fails validation, the picker records the reason and draws a replacement from the same size group. **Family selection does not run the security scanner.** It establishes that a usable comparison exists; the analysis pipeline determines whether that comparison contains security-sensitive changes.

### Stratified allocation

Size groups are based on **total artifact count**, including repeated copies. Distinct hash states determine candidate eligibility, not the family's size group.

| Family size | Artifacts per family | Families in DB | Artifact records | Share of families | Per trial | Three trials |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | 2 | 84,442 | 168,884 | 51.81% | 20 | 60 |
| Medium | 3–15 | 70,495 | 349,853 | 43.25% | 55 | 165 |
| Large | 16–100 | 7,329 | 242,838 | 4.50% | 20 | 60 |
| X-Large | 101–500 | 659 | 116,940 | 0.40% | 4 | 12 |
| Extreme | 501+ | 70 | 64,742 | 0.04% | 1 | 3 |
| **Total** | | **162,995** | **943,257** | **100%** | **100** | **300** |

Database counts describe names with at least two records in `artifact_groupings`, **before** distinct-content screening and relationship validation. They are not counts of families eligible for selection.

The **20/55/20/4/1** allocation is intentionally not proportional to the database distribution. Low and Medium families account for about 95% of these families, but 75% of each sample. We give larger families greater representation because they may offer more opportunities to observe changes and reuse, while limiting the number of X-Large and Extreme families because they can be expensive to analyze. This supports comparisons across family sizes, but unweighted results do not represent the wider population. For sample sizes other than 100, the picker uses largest-remainder allocation to preserve the total.

### Three-trial workflow

Trials use seeds **5801, 5802, and 5803**, derived from the notebook's base seed (`580`) and trial number. The separate seed used for manual-validation sampling is unchanged.

Trial 2 excludes names selected in Trial 1; Trial 3 excludes both previous lists. These exclusions come from saved `families.txt` files, not a fixed exclusion list. If a size group cannot supply enough validated families, the picker reports the shortage rather than changing the allocation.

Each trial saves:

- **`families.txt`** — names used as input to the analysis pipeline.
- **`sampling_report.json`** — sampling settings, database identity, size-group allocations, exclusion inputs, accepted families, and validation or rejection details.

The notebook generates a family list if one is missing and reuses it when present. The command-line tool calls the same library code. Existing sample files are not silently overwritten.

## Evidence

DuckDB exploration found **1,536 family names** where total artifact counts differ from counts of distinct primary-and-sibling hash combinations. Most observed differences were small, but they support screening on distinct states rather than assuming every artifact record represents a variant.

The size-group counts above show why proportional sampling would include few Large, X-Large, or Extreme families. They describe the database before relationship validation; the number of eligible families in each group may be lower.

RDR-013 documents why the broader Sprint 3 study focuses on primary edges. This record defines how families enter that study.

## Alternatives Considered

| Alternative | Outcome | Reason |
| --- | --- | --- |
| Group by name and normalized description | Not selected | Descriptions can change; the analyzer uses the entire exact-name family. |
| Qualify families using total artifact count alone | Not selected | Multiple records may represent identical content. |
| Accept any family with distinct hash states | Not selected | Different states may be unrelated or lack supported direction. |
| Maintain a fixed JSON exclusion list | Not selected | Candidate eligibility comes from DuckDB; prior trial selections are excluded through their family lists. |
| Use 20/60/20/0/0 or omit size strata | Not selected | The revised distribution covers every size group while controlling analysis cost. |
| Run security scans during selection | Not selected | Only a usable directed relationship must be established before sampling. |
| Use separate TOML configuration or a selection cache | Not selected for now | Fixed strata and a few input parameters are sufficient; further complexity is not justified yet. |

## Consequences and Limitations

- The sampled population is restricted to families with a usable primary directed relationship. Rejected families are **not** treated as families with no detected risk.
- Direction is inferred from available evidence, not proof of historical ancestry (RDR-007).
- The allocation is not proportional to the database distribution, and only families with usable primary directed relationships are eligible. Findings describe this selected population and should not be generalized to all GitSkills families without accounting for these restrictions.
- The trials do not overlap, but later selections depend on exclusions from earlier trials. They are not independent draws from an unchanged population.
- Relationship validation may take longer for families with many distinct variants. The picker reports progress; additional caching is deferred until performance shows a need.
- Reproducing results requires the recorded dataset, selection parameters, similarity policy, and applicable code, not only the seed.

## Follow-up Actions

- Generate three 100-family lists and preserve their sampling reports.
- Run the same primary-edge pipeline for each trial and keep the results separate (RDR-013).
- Review rejection counts and runtime after the first trial.
- Describe eligibility restrictions and stratification in the final report's methodology and threats to validity.

## Revisit Criteria

Revisit this approach if too few families pass validation in a size group, relationship checks become impractical for large families, or the sampling restrictions prevent the study from supporting its intended conclusions.
