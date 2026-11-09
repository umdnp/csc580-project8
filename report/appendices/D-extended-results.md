
# Appendix D Additional Sprint 3 results

The tables below are calculated from the saved Sprint 3 `review/summary.json`, `review/families.csv`, `review/directed_pairs.csv`, and `review/direction_basis.csv` files. All indicator results are **automated** and pending independent human adjudication. Per-indicator counts overlap: one comparison may contain more than one supported indicator, and multiple comparisons may share artifacts.

## Indicator frequency by trial

Each entry counts **primary directed comparisons** with the indicated supported RI. The final column counts **distinct families** across the three non-overlapping trials that have at least one such comparison.

| Indicator | Trial 1 | Trial 2 | Trial 3 | All comparisons | Distinct families |
| --- | ---: | ---: | ---: | ---: | ---: |
| **RI-001** | 0 | 0 | 3 | 3 | 3 |
| **RI-002** | 0 | 0 | 0 | 0 | 0 |
| **RI-003** | 8 | 3 | 41 | 52 | 17 |
| **RI-004** | 0 | 0 | 0 | 0 | 0 |
| **RI-005** | 25 | 15 | 115 | 155 | 26 |
| **RI-006** | 57 | 7 | 95 | 159 | 10 |
| **RI-007** | 3 | 0 | 1 | 4 | 2 |
| **RI-008** | 8 | 4 | 6 | 18 | 8 |
| **RI-009** | 0 | 0 | 0 | 0 | 0 |
| **RI-010** | 33 | 23 | 145 | 201 | 39 |
| **RI-011** | 0 | 0 | 1 | 1 | 1 |

: Risk-indicator frequency across the three trials {.wide}

## Direction evidence and selected comparisons

The following categories are mutually exclusive per directed comparison. Counts of comparisons with RIs are *not* counts of verified copied-skill lineages.

| Direction basis | All comparisons | With supported RIs | Incomplete evidence coverage |
| --- | ---: | ---: | ---: |
| Declared source | 10 | 0 | 1 |
| Direct chronology | 399 | 55 | 42 |
| Equivalent-peer chronology | 355 | 43 | 8 |
| Repository-creation boundary | 827 | 111 | 86 |
| Directional containment | 566 | 131 | 74 |
| **Total** | **2,157** | **340** | **211** |

: Direction evidence and coverage for selected comparisons {.wide}

## Bundle change types

| Change type | Comparisons | With supported RIs |
| --- | ---: | ---: |
| `skill-only` | 805 | 33 |
| `siblings-only` | 190 | 41 |
| `skill+siblings` | 804 | 242 |
| `unknown` | 358 | 24 |
| **Total** | **2,157** | **340** |

: Primary-comparison counts by bundle change type

`unknown` describes an unavailable or insufficiently known sibling state, not a known unchanged bundle. Equivalent relationships are not counted as base-to-derived comparisons. A `siblings-only` classification uses main-skill equivalence under the similarity representation rather than requiring identical byte hashes; see Appendix B.

## Family-size and cluster notes

Across 300 families, the analyzer produced **438 similarity clusters**. Families with multiple clusters were uncommon in the smaller strata (0 of 60 Low families; 10 of 165 Medium) and more common in the larger strata (19 of 60 Large; all 12 X-Large; all three Extreme). These clusters indicate relatedness under the project's token-shingle method, not verified independent origins.

For illustration, selected large families show different cluster structures:

| Family | Artifact occurrences | Similarity clusters |
| --- | ---: | ---: |
| `implement` | 856 | 35 |
| `mcp-builder` | 543 | 11 |
| `documentation` | 508 | 19 |
| `cso` | 150 | 2 |

: Examples of family size and similarity clusters

The full per-family counts, coverage records, and selected comparisons remain in the three saved `review/` directories. They are not duplicated here because the detailed tables are best inspected directly as reproducible data files.
