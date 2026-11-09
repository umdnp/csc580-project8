# Results

## Three-trial overview

Across three non-overlapping Sprint 3 trials, we analyzed **300 randomly selected, relationship-eligible skill families**, comprising **6,570 artifact occurrences** and **2,157 primary directed comparisons**. The automated analysis found at least one supported **risk indicator (RI)** in **63 families (21.0%)**. These are candidate security-sensitive changes identified under our rules, **not** confirmed vulnerabilities, malicious instructions, or observed executions. Independent manual validation is in progress.

| Measure | Trial 1 | Trial 2 | Trial 3 | Combined |
| --- | ---: | ---: | ---: | ---: |
| Families analyzed | 100 | 100 | 100 | **300** |
| Artifacts loaded | 2,275 | 2,067 | 2,228 | **6,570** |
| Primary directed comparisons | 665 | 633 | 859 | **2,157** |
| Families with a supported RI | 25 (25.0%) | 18 (18.0%) | 20 (20.0%) | **63 (21.0%)** |
| Comparisons with a supported RI | 113 (17.0%) | 36 (5.7%) | 191 (22.2%) | **340 (15.8%)** |
| Flagged comparisons (any reason) | 346 | 271 | 502 | **1,119** |
| Comparisons with incomplete evidence coverage | 123 | 28 | 60 | **211** |

: Automated results from the three Sprint 3 trials {.wide}

The same code revision, rules, similarity policy, and primary-edge setting were used in all three trials. No selected artifacts were skipped. Because the study deliberately oversampled larger families and required usable directed relationships, these percentages describe **our selected families**, not all skills in GitSkills.

## Finding 1: Security-sensitive changes appear across multiple families

Supported indicators appeared in **25 of 100 families in Trial 1, 18 of 100 in Trial 2, and 20 of 100 in Trial 3**. The combined rate was **63 of 300 (21.0%)**, with detections in each sample rather than just one. The figure below shows the rates without giving more visual weight to families that contribute many comparisons. Human review will determine how reliably these automated detections reflect the defined changes.

![Percentage of sampled families with at least one supported risk indicator, by trial and combined.](report/figures/sprint3-family-vs-pair-rates.svg){#fig-sprint3-rates width="47%"}

A family counts once in this measure, whether one comparison or many contain an indicator. This keeps the focus on **how widely the changes appear among sampled families**. The sensitivity check below shows why that choice matters.

## Finding 2: Script execution and external code acquisition are the most widespread changes

The risk indicators distinguish specific operational changes from ordinary differences in instructions. **RI-010** Local script execution was supported in **39 families (13.0% of all sampled families)**, followed by **RI-005** External code or dependency acquisition in **26 families (8.7%)**. Together, those two indicators appeared in **52 distinct families**: 39 had RI-010, 26 had RI-005, and 13 had both. Thus, **52 of the 63 indicator-bearing families (82.5%)** had at least one of these two indicators. The overlap matters; adding the individual counts would double-count families.

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

: Supported indicator counts among 300 families and 2,157 comparisons

These categories **overlap**: one changed command or family may support several indicators. The `python-executor` example in Section 6 illustrates how a single operation can support more than one indicator. Counts here are not counts of independent incidents.

The distribution also varies by counting unit. **RI-006** Destructive or privileged file operations appeared in just **10 families**, but in **159 comparisons**; **134** of those comparisons came from `cso` and `mcp-builder`. That concentration is a reason to present family counts first. **RI-002**, **RI-004**, and **RI-009** had no supported detections in these trials. Zero detections do not establish that these behaviors are absent from other skills or undetectable by other methods.

## Sensitivity check: Why families are the primary unit

The secondary comparison-level detection rate was **340 of 2,157 pairs (15.8%)**, but it varied from **5.7% to 22.2%** across trials. A few families contributed many indicator-bearing comparisons: `cso` accounted for **55 of 113** in Trial 1, `junta-leiloeiros` for **8 of 36** in Trial 2, and `mcp-builder` for **133 of 191** in Trial 3. Excluding these three families *for a sensitivity calculation only* reduced the combined pair-level rate to **144 of 1,722 (8.4%)**, while the family-level rate changed only from **63 of 300 (21.0%)** to **60 of 297 (20.2%)**. This supports using family-level frequency to describe the spread of detections in our sample; it does not remove sampling bias or prove population-wide risk prevalence.

| Trial | All pairs | Excl. top family |
| --- | ---: | ---: |
| 1 | 113/665 (17.0%) | 58/549 (**10.6%**) |
| 2 | 36/633 (5.7%) | 28/613 (**4.6%**) |
| 3 | 191/859 (22.2%) | 58/560 (**10.4%**) |
| **Total** | **340/2,157 (15.8%)** | **144/1,722 (8.4%)** |

: Sensitivity of pair-level rates to the leading family in each trial

## Supporting observation: Family size and similarity clusters

Larger families were more likely to contain at least one supported indicator. They also offered more opportunities for directed comparisons and often contained more **similarity clusters**, which group artifacts with related instruction content under our thresholds.

| Family size | Families | Families with an RI | Rate | Mean similarity clusters per family |
| --- | ---: | ---: | ---: | ---: |
| Low (2 artifacts) | 60 | 4 | 6.7% | 1.0 |
| Medium (3–15) | 165 | 24 | 14.5% | 1.1 |
| Large (16–100) | 60 | 23 | 38.3% | 1.5 |
| X-Large (101–500) | 12 | 9 | 75.0% | 3.8 |
| Extreme (501+) | 3 | 3 | 100.0% | 21.7 |

: Family size, indicator frequency, and similarity-cluster structure {.wide}

For example, `implement` contained **856 artifacts in 35 clusters**, while `cso` had **150 artifacts in two clusters**. This reinforces why sharing a name is not enough to establish that skills are related. Multiple clusters do not prove different authors or independent origins, and a larger family provides more opportunities to detect changes. With only three Extreme families, their 100% detection rate should not be generalized.

## Supporting observation: Not every detected difference supports a risk indicator

The scanner **flagged 1,119 of 2,157 comparisons (51.9%)**, but only **340 (15.8%)** met the narrower criteria for at least one supported indicator. The remaining **779 flagged comparisons** are still recorded as differences or uncertain evidence; they are **not** declared harmless. This is an intentional distinction between noticing a change and identifying one that warrants security review. Section 6 gives contrasting examples of those outcomes.

## Evidence and ordering qualifications

**Evidence coverage.** Of the **2,157 comparisons**, **211** had incomplete evidence coverage, including **81 of the 340** with supported indicators. A particular detected operation can have complete extracted evidence even when another part of the comparison is incomplete. Among the **1,946 comparisons labelled complete**, **259 (13.3%)** had supported indicators, compared with **340 of 2,157 (15.8%)** overall. This is a coverage comparison, not a correction for detection error or selection bias.

**Direction evidence.** The 2,157 comparisons were oriented through declared source (10), direct chronology (399), equivalent-peer chronology (355), repository-creation boundaries (827), or directional containment (566). Of the 340 indicator-bearing comparisons, **131** relied on containment for direction. These methods support plausible earlier/later ordering, not verified histories of copying. Appendix D contains the full breakdown.

**Supporting files.** The analysis labelled **190 comparisons** `siblings-only` under its bundle-equivalence rules, with supported indicators in **41**. Most of those indicator-bearing comparisons are concentrated in `mcp-builder`, so manual review is needed before treating them as independent changes in executed-script behavior. Equivalence under the similarity representation does not guarantee byte-identical `SKILL.md` text.

The three trials' automated results are complete, but **independent human validation of relationship decisions and indicator judgments is still underway**. The next section describes how those findings will be evaluated.
