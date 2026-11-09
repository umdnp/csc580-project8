# Results

## Three-trial overview

The saved Sprint 3 analysis covers **300 distinct, randomly selected families** in three equal-sized, non-overlapping samples. The pipeline loaded **6,570 artifacts** and analyzed **2,157 primary directed comparisons**. It automatically identified at least one **supported risk indicator (RI)** in **63 families (21.0%)** and **340 comparisons (15.8%)**. These are observations under the study's implemented rules, **not** manually confirmed vulnerabilities, malicious skills, or actual security incidents. Independent review of the selected validation cases is still in progress.

| Measure | Trial 1 | Trial 2 | Trial 3 | Combined |
| --- | ---: | ---: | ---: | ---: |
| Families analyzed | 100 | 100 | 100 | **300** |
| Artifacts loaded | 2,275 | 2,067 | 2,228 | **6,570** |
| Primary directed comparisons | 665 | 633 | 859 | **2,157** |
| Families with at least one supported RI | 25 (25.0%) | 18 (18.0%) | 20 (20.0%) | **63 (21.0%)** |
| Comparisons with at least one supported RI | 113 (17.0%) | 36 (5.7%) | 191 (22.2%) | **340 (15.8%)** |
| Flagged comparisons (any reason) | 346 | 271 | 502 | **1,119** |
| Comparisons with incomplete evidence coverage | 123 | 28 | 60 | **211** |

: Automated results from the three Sprint 3 trials {.wide}

Family percentages use 100 families per trial (300 combined); pair percentages use all primary directed comparisons in the relevant trial. No selected artifact was skipped. Each trial used the same code revision, rule registry, similarity policy, and primary-edge setting. The 300 families are the study sample, not a representative cross-section of every GitSkills skill.

## Finding 1: Detections occur across several families

The primary outcome—families containing at least one supported RI—ranges from **18% to 25%** across trials. This demonstrates that the scanner's indicators are not limited to one family or one trial. It does not yet establish the proportion of all GitSkills families with such changes, or how many observed detections independent reviewers will confirm.

The family-level outcome is intentional (RDR-013): a family contributes **one** to this measure whether one of its comparisons or many of its comparisons contain an indicator. The pair-level measure provides a useful second view, but answers a different question.

![Family-level versus comparison-level rates in the three trials. Family-level rates are more similar across trials.](report/figures/sprint3-family-vs-pair-rates.png){#fig-sprint3-rates width="100%" .wide}

## Finding 2: Pair-level totals are sensitive to a few families

As the figure shows, the comparison-level rate varies more than the family-level rate. A reason is that some families yield far more primary comparisons than others. Within a family, multiple comparisons can share artifacts and recurring evidence; they should not be counted as independent historical changes.

The most influential family in each trial contributed the following indicator-bearing comparisons:

| Trial | Family | Indicator-bearing comparisons | Share of that trial's indicator-bearing comparisons |
| --- | --- | ---: | ---: |
| 1 | `cso` | 55 | 48.7% |
| 2 | `junta-leiloeiros` | 8 | 22.2% |
| 3 | `mcp-builder` | 133 | 69.6% |

: Most influential family in each trial {.wide}

To test the sensitivity of the descriptive result, we recalculated each trial's pair-level rate **without its most influential family**, leaving the original study sample and results untouched:

| Trial | All families | Excluding the listed dominant family |
| --- | ---: | ---: |
| 1 | 113 / 665 = 17.0% | 58 / 549 = **10.6%** |
| 2 | 36 / 633 = 5.7% | 28 / 613 = **4.6%** |
| 3 | 191 / 859 = 22.2% | 58 / 560 = **10.4%** |
| **Combined** | **340 / 2,157 = 15.8%** | **144 / 1,722 = 8.4%** |

: Sensitivity of comparison-level detection rates to dominant families {.wide}

After excluding these three families, the family-level rate is **60 of 297 (20.2%)**, compared with **63 of 300 (21.0%)** originally. This contrast explains why family-level frequency is the primary measure. It also cautions against interpreting the 2,157 comparisons as independent security events.

## Finding 3: Indicators differ in how widely they appear

Risk indicators describe specific security-sensitive *changes*, not general scanner matches. The table counts the number of distinct sampled families containing each indicator and, secondarily, the number of directed comparisons where it was supported. A family or comparison can appear in several rows.

| Indicator | Families (of 300) | Comparisons (of 2,157) |
| --- | ---: | ---: |
| **RI-010** Local script execution | **39** | 201 |
| **RI-005** External code/dependency acquisition | **26** | 155 |
| **RI-003** Network expansion/redirection | **17** | 52 |
| **RI-006** Destructive/privileged file operation | **10** | 159 |
| **RI-008** System or permissions modification | 8 | 18 |
| **RI-001** Direct download-and-execute | 3 | 3 |
| **RI-007** Credential access/potential exposure | 2 | 4 |
| **RI-011** External instruction dependency | 1 | 1 |
| **RI-002**, **RI-004**, **RI-009** | **0 each** | **0 each** |

: Risk indicators by the number of sampled families and directed comparisons {.wide}

![Number of distinct families with each supported risk indicator; indicators with no detections are included at zero.](report/figures/sprint3-indicators-by-family.png){#fig-sprint3-indicators width="100%" .wide}

RI-010 is observed across the most families, followed by RI-005. By contrast, RI-006 produces almost as many comparison-level observations as RI-005 but is found in only **10 families**. Of RI-006's 159 indicator-bearing comparisons, **134** occur in `cso` and `mcp-builder` together. The difference between these columns is important: a high pair count can indicate repeated comparisons within a few families rather than wide distribution across the sample.

RI-002, RI-004, and RI-009 were not supported in these trials. Zero detections could reflect the sampled content, missing evidence, or the implemented rules. It does not establish that those behaviors are absent from GitSkills.

## Supporting observation: Family size and cluster structure

Larger families were more likely to contain at least one supported RI. They also offered more candidate relationships and, often, more **similarity clusters**—groups of artifacts whose instructions are related under the study's similarity criteria.

| Family size | Families | Families with an RI | Rate | Mean similarity clusters per family |
| --- | ---: | ---: | ---: | ---: |
| Low (2 artifacts) | 60 | 4 | 6.7% | 1.0 |
| Medium (3–15) | 165 | 24 | 14.5% | 1.1 |
| Large (16–100) | 60 | 23 | 38.3% | 1.5 |
| X-Large (101–500) | 12 | 9 | 75.0% | 3.8 |
| Extreme (501+) | 3 | 3 | 100.0% | 21.7 |

: Family size, indicator frequency, and similarity-cluster structure {.wide}

For example, `implement` contains **856 artifacts in 35 clusters**, whereas `cso` contains **150 artifacts in two clusters**. Many occurrences under one name do not necessarily represent a single shared history: different skills may use the same name. Conversely, several clusters do not prove different authors or independent origins. The three Extreme families are too few to support a broad conclusion about their 100% detection rate.

These patterns also help explain why the study starts with same-name candidates but requires content similarity before choosing comparisons. They do **not** show that adding copies or increasing family size causes security risk.

## Supporting observation: Evidence changes are broader than supported indicators

The scanner flagged **1,119 of 2,157 comparisons (51.9%)** for some observed rule, evidence, or indicator-related change. Only **340 (15.8%)** satisfied the narrower requirements for at least one supported RI. Thus, **779 flagged comparisons** had no supported indicator. This separation is **by design**, not a claim that the other differences are harmless.

For example, a change from `npm install` to `bun install` can be correctly recorded as changed command evidence, yet it does not on its own demonstrate a newly introduced acquisition source (RI-005). The comparator retains the evidence; the assessor withholds an unsupported risk indicator. The contrasting `python-executor` case in Section 6 introduces an explicit remote-script execution method and a new network-operation hostname. These are examples of how assessment considers the *meaning of the change*, not merely the presence or number of matching words.

## Coverage and ordering qualifications

**Evidence coverage.** Of the **2,157 comparisons**, **211** have incomplete evidence coverage; **81** of the **340** comparisons with supported indicators are in this group. A specific operation can be fully extracted even when another portion of the same comparison is missing or partially extracted. The complete-labelled subset contains **259 indicator-bearing comparisons among 1,946 pairs (13.3%)**, compared with **340 among 2,157 (15.8%)** overall. This is a descriptive coverage check, not a correction for detection error or sampling bias.

**Direction evidence.** The 2,157 comparisons use declared source (10), direct chronology (399), equivalent-peer chronology (355), repository-creation boundaries (827), or directional containment (566). Of the 340 indicator-bearing comparisons, **131** rely on containment direction alone. Such relationships provide plausible orderings but not verified ancestry. Appendix D provides the full direction breakdown and the main change-type counts.

**Sibling differences.** The pipeline classifies **190 comparisons** as `siblings-only` under its bundle-equivalence rules, with supported indicators in **41**. These observations support inspecting bundled resources, but most positive `siblings-only` comparisons are concentrated in `mcp-builder`; case-level review is needed before treating them as distinct changes in executed script behavior.

The independent manual reviews of the similarity decisions and the supported/unsupported indicators remain in progress. The results above are therefore final **automated trial counts** but provisional as claims about correctly detected security-sensitive changes. Their validation and the interpretation of individual cases belong in the evaluation and discussion sections.
