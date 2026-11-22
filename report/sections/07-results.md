# Results {#sec-results}

## Three-trial overview

A central distinction in our results is between changes the scanner flags for review and changes supported by evidence of a specific security-sensitive operation. Here, **supported** means that the automated analysis found evidence meeting an indicator's criteria—not that a human reviewer independently confirmed it. Across three non-overlapping Sprint 3 trials, we analyzed **300 relationship-eligible skill families selected through stratified random sampling**, comprising **6,570 artifact occurrences** and **2,157 primary directed comparisons**. The automated analysis found at least one supported **risk indicator (RI)** in **63 families (21.0%)**. [Table 4](#tbl-trial-results) summarizes the automated results by trial.

| Measure | Trial 1 | Trial 2 | Trial 3 | Combined |
| --- | ---: | ---: | ---: | ---: |
| Families analyzed | 100 | 100 | 100 | **300** |
| Artifacts loaded | 2,275 | 2,067 | 2,228 | **6,570** |
| Primary directed comparisons | 665 | 633 | 859 | **2,157** |
| Families with a supported RI | 25 (25.0%) | 18 (18.0%) | 20 (20.0%) | **63 (21.0%)** |
| Comparisons with a supported RI | 113 (17.0%) | 36 (5.7%) | 191 (22.2%) | **340 (15.8%)** |
| Flagged comparisons (any reason) | 346 | 271 | 502 | **1,119** |
| Comparisons with incomplete evidence coverage | 123 | 28 | 60 | **211** |

: Automated results from the three Sprint 3 trials {#tbl-trial-results} {.wide}

The three trials used the same active rules, similarity policy, primary-edge setting, and recorded scanner and cohort implementation fingerprints. No selected artifacts were skipped. Because the study deliberately oversampled larger families and required usable directed relationships, these percentages describe **our selected families**, not all skills in GitSkills.

## Finding 1: Security-sensitive changes appear across multiple families

Supported indicators appeared in **25 families in Trial 1, 18 in Trial 2, and 20 in Trial 3**, for a combined total of **63 of 300 families (21.0%)**. As [Figure 2](#fig-sprint3-rates) shows, the findings were spread across all three trials rather than concentrated in one. Each family counts once, regardless of how many comparisons contain an indicator, so the result shows how widely these changes appeared among the sampled families.

![Percentage of sampled families with at least one supported risk indicator, by trial and combined.](report/figures/sprint3-family-vs-pair-rates.svg){#fig-sprint3-rates width="47%" .here}

## Finding 2: Script execution and external code acquisition are the most widespread changes

Changes involving local scripts and external code stood out in our results. The automated analysis supported **RI-010** (local script execution) in **39 families (13.0%)** and **RI-005** (external code or dependency acquisition) in **26 families (8.7%)**. The indicators overlapped in **13 families** and together appeared in **52 of the 63 indicator-bearing families (82.5%)**. These changes matter because they can alter what code an agent runs or obtains. [Figure 3](#fig-sprint3-indicators) shows the family-level distribution, while [Table 5](#tbl-indicator-counts) provides comparison-level counts.

![Number and percentage of sampled families with each of the eight detected risk indicators.](report/figures/sprint3-indicators-by-family.svg){#fig-sprint3-indicators width="100%" .wide}

| Indicator | Families | Pairs |
| --- | ---: | ---: |
| **RI-010** Script execution | **39** | 201 |
| **RI-005** Code acquisition | **26** | 155 |
| **RI-003** Network expansion | **17** | 52 |
| **RI-006** Destructive file ops | **10** | 159 |
| **RI-008** System/permissions | 8 | 18 |
| **RI-001** Download-and-execute | 3 | 3 |
| **RI-007** Credential access | 2 | 4 |
| **RI-011** External instructions | 1 | 1 |
| **RI-002/004/009** No detections | **0** | **0** |

: Supported indicator counts among 300 families and 2,157 comparisons {#tbl-indicator-counts}

These categories **overlap**: one changed command or family may support several indicators. The `python-executor` example in [Section V](#sec-method) illustrates how a single operation can support more than one indicator. Counts here are not counts of independent incidents.

The distribution also varies by counting unit. **RI-006** Destructive or privileged file operations appeared in just **10 families**, but in **159 comparisons**; **134** of those comparisons came from `cso` and `mcp-builder`. That concentration is a reason to present family counts first. **RI-002**, **RI-004**, and **RI-009** had no supported detections in these trials. This does not mean those behaviors are absent from GitSkills or that our rules would recognize every instance.

## Sensitivity check: Why families are the primary unit

The secondary comparison-level detection rate was **340 of 2,157 pairs (15.8%)**, but it varied from **5.7% to 22.2%** across trials. A few families contributed many indicator-bearing comparisons: `cso` accounted for **55 of 113** in Trial 1, `junta-leiloeiros` for **8 of 36** in Trial 2, and `mcp-builder` for **133 of 191** in Trial 3. To see how much those families influenced the results, we excluded them in a separate sensitivity calculation. The pair-level rate fell from **15.8%** to **144 of 1,722 (8.4%)**, while the family-level rate changed only slightly, from **63 of 300 (21.0%)** to **60 of 297 (20.2%)**. The trial-by-trial pair-level rates appear in [Table 6](#tbl-sensitivity). This supports using family-level frequency to describe how widely detections appear across the sampled families.

| Trial | All pairs | Excl. top family |
| --- | ---: | ---: |
| 1 | 113/665 (17.0%) | 58/549 (**10.6%**) |
| 2 | 36/633 (5.7%) | 28/613 (**4.6%**) |
| 3 | 191/859 (22.2%) | 58/560 (**10.4%**) |
| **Total** | **340/2,157 (15.8%)** | **144/1,722 (8.4%)** |

: Sensitivity of pair-level rates to the leading family in each trial {#tbl-sensitivity}

## Supporting observation: Family size and similarity clusters

Larger families were more likely to contain at least one supported indicator. They also offered more opportunities for directed comparisons and often contained more **similarity clusters**, which group artifacts with related instruction content under our thresholds ([Table 7](#tbl-family-size-results)).

| Family size | Families | Families with an RI | Rate | Mean similarity clusters per family |
| --- | ---: | ---: | ---: | ---: |
| Low (2 artifacts) | 60 | 4 | 6.7% | 1.0 |
| Medium (3–15) | 165 | 24 | 14.5% | 1.1 |
| Large (16–100) | 60 | 23 | 38.3% | 1.5 |
| X-Large (101–500) | 12 | 9 | 75.0% | 3.8 |
| Extreme (501+) | 3 | 3 | 100.0% | 21.7 |

: Family size, indicator frequency, and similarity-cluster structure {#tbl-family-size-results} {.wide}

For example, `implement` contained **856 artifacts in 35 clusters**, while `cso` had **150 artifacts in two clusters**. This reinforces why sharing a name is not enough to establish that skills are related. Multiple clusters do not prove different authors or independent origins. Higher detection rates in larger families may simply reflect more artifacts and more chances to observe a change, **not** greater inherent security risk. With only three Extreme families, their 100% detection rate should not be generalized.

## Supporting observation: Not every detected difference supports a risk indicator

The scanner **flagged 1,119 of 2,157 comparisons (51.9%)**, but only **340 (15.8%)** met the narrower criteria for at least one supported indicator. The remaining **779 flagged comparisons** are still recorded as differences or uncertain evidence; they are **not** declared harmless. This is an intentional distinction between noticing a change and identifying one that warrants security review. [Section V](#sec-method) gives contrasting examples of those outcomes.

## Evidence and ordering qualifications

**Evidence coverage.** Of the **2,157 comparisons**, **211** had incomplete evidence coverage, including **81 of the 340** with supported indicators. A particular detected operation can have complete extracted evidence even when another part of the comparison is incomplete. Among the **1,946 comparisons labelled complete**, **259 (13.3%)** had supported indicators, compared with **340 of 2,157 (15.8%)** overall. This is a coverage comparison, not a correction for detection error or selection bias.

**Direction evidence.** The 2,157 comparisons were oriented through declared source (10), direct chronology (399), equivalent-peer chronology (355), repository-creation boundaries (827), or directional containment (566). Of the 340 indicator-bearing comparisons, **131** relied on containment for direction. These methods support plausible earlier/later ordering, not verified histories of copying. [Appendix D](#app-d) contains the full breakdown.

**Supporting files.** The analysis labelled **190 comparisons** `siblings-only` under its bundle-equivalence rules, with supported indicators in **41**. Most of those indicator-bearing comparisons are concentrated in `mcp-builder`. Adjudicated review found both unsupported and missed detections in individual comparisons. Equivalence under the similarity representation does not guarantee byte-identical `SKILL.md` text.

The automated counts were frozen before subsequent review findings and a scanner correction. They were **not recomputed** using the revised scanner. [Section VII](#sec-evaluation) explains what the adjudicated review supports and where the original detections were incorrect or incomplete.
