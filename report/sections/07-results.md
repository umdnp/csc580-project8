\clearpage

# Results

This section distinguishes saved Sprint 1 observations, a locally reproduced methodological example, and population-level results that remain to be produced. The worked example demonstrates tool behavior; it does not estimate prevalence or validate historical ancestry.

## Dataset Processing Results

The local candidate-selection audit on October 15, 2026 retained 943,257 of 3,797,117 source artifact occurrences, a reduction of 75.16 percent. The retained rows represent 162,995 exact-name families and 628,026 name-and-normalized-description groups. Dataset and Data Preparation provides the executable SQL, cumulative counts, and filter rationale. These totals describe candidate construction, not completed similarity analyses, directed comparisons, or security scans. Unique analyzed SHA counts, final relationship totals, scan completion and exclusion counts remain to be measured by the broader pipeline.

### Saved Sprint 1 Extraction Outcomes

Inspection of `notebooks/extraction_pipeline/results/sample_artifacts_scanner_results.parquet` confirmed the following saved results. This is an audit of the saved output, not a rerun of every dataset comparison with the current rules.

| Saved notebook measure | Observed value |
| --- | ---: |
| Artifact rows | 43 |
| Exact-name groups | 10 |
| Adjacent comparisons with stored scanner output | 33 |
| Comparisons with at least one positive rule-count delta | 13 (39.4%) |
| Positive rule-delta events across those comparisons | 35 |
| Sum of positive rule-count deltas | 77 |

The 77 additional matches sum positive deltas only; they are not the net change after accounting for decreases, a count of unique actions, or a count of newly introduced capabilities. Multiple rules can increase in one pair, and multiple matches can contribute to one rule's delta.

The 33 notebook pairs follow view-order adjacency within names, whereas the saved family-analysis reports contain 17 selected directed relationships. These outputs test different parts of the workflow and must not be combined into one relationship denominator. The 39.4 percent figure describes this purposeful notebook sample only, not population prevalence or a rate of proven harmful changes.

## Security-Pattern Results

[TODO: Report the prevalence of detected rules and categories.]

## Introduced Risk Signals

[TODO: Report how frequently derived artifacts introduced rules or categories that were absent from their base artifacts.]

## Removed and Retained Signals

[TODO: Report how frequently signals were removed, retained, or unchanged.]

## Results by Relationship Type

[TODO: Compare meaningful relationship groups when supported by the data.]

## Validation Results

The configured sample-skill test selection passed seven cases at the documented code revision, and a separate local verification passed all 21 extraction-pipeline test cases. These deterministic checks establish expected outputs for those fixtures; they do not estimate accuracy on dataset artifacts. The worked example below was reproduced from local data, but neither its inferred direction nor its scanner findings have been established here as independently annotated ground truth. Numerical manual-review results remain pending the review protocol and annotations described in Evaluation and Validation.

## Representative Examples

### Worked Example: Similarity, Inferred Direction, and Scanner Change

The example uses one five-artifact candidate family from the prepared local DuckDB database. Family and endpoint identities are omitted under the report's reporting policy; the selected source and target are labeled A and B. The analysis was rerun locally on October 15, 2026 at code revision `f2b4c7d`, using the default similarity policy and current registered scanner rules. The database release identifier and integrity hash have not yet been documented, so this is a local demonstration rather than a fully frozen dataset experiment.

#### From Candidate Family to Selected Pair

The family contains five skill variants and five bundle variants in one similarity cluster. All ten distinct skill-variant pairs pass the relatedness policy, but the resulting graph selects only two directed predecessor edges. It also records one equivalent undirected relationship and two direction-unknown relationships; other supported directed candidates are retained as additional relationships.

For the selected A-to-B edge, the analysis reports 2,936 shared shingles, containment of approximately 0.962, and Jaccard of approximately 0.414. Thus, about 96.2 percent of A's distinct shingles occur in B, while their shared shingles account for about 41.4 percent of the combined set. These are representation-overlap measures, not percentages of lines copied or probabilities of common ancestry.

The selected edge has `containment` as its direction basis and is classified as `skill-only`. This supplies a structural hypothesis for treating A as base and B as derived; it does not establish that A was published first or directly copied. The second selected edge in the family uses chronology, illustrating that one family can contain relationships with different evidential bases.

```text
Five exact-name artifact occurrences
          |
Five skill variants; ten qualifying similarity pairs
          |
One cluster; two selected directed predecessor edges
          |
Selected pair A -> B (containment-based, skill-only)
          |
Scan both skill bodies with the same 13-rule catalog
          |
25 base matches -> 49 derived matches; no new categories
```

#### Paired Scanner Results

| Changed rule | Base A | Derived B | Delta |
| --- | ---: | ---: | ---: |
| CMD-001: shell-language code fences | 3 | 5 | +2 |
| CMD-002: command invocations | 2 | 6 | +4 |
| CRED-001: secret-related terms | 11 | 14 | +3 |
| CRED-002: credential-file references | 5 | 12 | +7 |
| EXT-002: package installation | 1 | 3 | +2 |
| FS-003: file-reading commands/APIs | 1 | 2 | +1 |
| NET-001: HTTP/HTTPS URLs | 2 | 7 | +5 |
| **Total rule matches** | **25** | **49** | **+24** |

Each changed rule already matches the base, so none of these increases constitutes new rule presence. All introduced-category flags are false. This example therefore demonstrates increased matches within existing capabilities rather than the introduction of a previously absent category. It cannot support a claim that the derived artifact is more harmful, that instructions executed, or that any credential was exposed.

These counts describe the current code revision and local inputs. Counts depend on the rule catalog, input handling, and analyzed text. Runs using different definitions or processing settings must be labeled separately rather than pooled as measurements from an identical instrument.

#### Scan Scope and Review Implications

This table compares the two skill bodies using `SkillAnalyzer` and `compare_results`, the same scanning and comparison components used by `scan_diff`. It does not present sibling findings. The broader `scan_family` path reviews selected directed edges and applicable sibling changes, and can flag matches in new destination content even without a positive aggregate count delta.

A reviewer should inspect the matched instructions in context, assess the direction evidence separately, and distinguish missing sibling evidence from a negative result. This case shows that the pipeline can connect candidate selection, inferred direction, and rule-level differences; it supplies neither population-level generalization nor independent ground truth.

## Results Summary

The reproduced family example contains five artifacts, ten qualifying similarity pairs, and two selected directed relationships. Its selected containment-based pair has 25 base matches and 49 derived matches, with increases in seven rules and no introduced categories. Seven configured sample-skill tests pass. These observations demonstrate selected implementation behavior; population introduction rates and independently measured validation accuracy remain unreported.