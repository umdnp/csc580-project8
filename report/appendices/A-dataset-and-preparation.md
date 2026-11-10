\clearpage


# Appendix A Dataset construction and preparation {#app-a}

## Candidate selection

The preparation script, `sql/create_analysis_tables.sql`, creates the comparison-candidate table from GitSkills without modifying the released source data. An occurrence qualifies when its `SKILL.md` frontmatter is valid, its instruction body has more than 50 characters, and its content, name, and description are present. A name must occur at least twice among qualifying records. Identical copies count toward this initial requirement; distinct content and usable relationships are checked later during sampling.

Descriptions are lowercased, trimmed, and whitespace-normalized to form supporting subgroups, but the family analyzer compares across those subgroups. The prepared table also holds sibling-content fingerprints, which are populated by later enrichment; a missing fingerprint must not be treated as proof that the bundle is empty. The source SQL and the detailed preparation workflow (`report/diagrams/preparation-activity.puml`) remain in the repository for reproduction.

## Selection audit and identity

| Preparation stage | Retained artifacts | Excluded at this stage |
| --- | ---: | ---: |
| All source occurrences | 3,797,117 | - |
| Valid frontmatter | 1,627,753 | 2,169,364 |
| Body over 50 characters and required fields present | 1,621,757 | 5,996 |
| Name repeated among qualifying occurrences | 943,257 | 678,500 |

: Candidate-selection audit for the prepared GitSkills snapshot {#tbl-selection-audit} {.wide}

The October 15, 2026 preparation audit retained **943,257 occurrences** across **162,995 same-name families**. The Sprint 3 picker later considered **162,461 preliminary candidates**, screened for distinct main-file/sibling states, and required at least one usable directed comparison. These intermediate counts describe different screening stages; **none is the denominator for the reported 21.0% result**. The final study contains 300 relationship-eligible families and 6,570 loaded occurrences.

Local artifact and group IDs may differ across database builds; reproduction uses repository/path identity, content hashes, and the dataset snapshot. Sibling enrichment distinguishes known empty bundles from missing content.

## Sprint 3 sample audit

The following counts come from the saved `sampling_report.json` files. A rejection means that the candidate failed the family picker's relationship validation, **not** that it contained no security-sensitive behavior. The picker replaced rejected candidates in the same stratum.

| Sample | Seed | Families selected | Candidates rejected during drawing | Previously selected families excluded |
| --- | ---: | ---: | ---: | ---: |
| Trial 1 | 5801 | 100 | 239 | 0 |
| Trial 2 | 5802 | 100 | 288 | 100 |
| Trial 3 | 5803 | 100 | 247 | 200 |

: Sprint 3 sample seeds and family-selection audit {#tbl-sampling-audit}

Each trial retains the same 20/55/20/4/1 size allocation described in [Section IV](#sec-dataset). The sampling reports preserve the rejection reasons, source database identity, thresholds, excluded `families.txt` paths and checksums, and exact selected names. The screened eligible population was not enumerated for population weighting, so these records cannot support a corpus-wide prevalence estimate.
