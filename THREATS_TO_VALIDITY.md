# Threats to Validity

## Construct Validity

The study uses rule-based indicators, candidate groupings, similarity measures, provenance evidence, and sibling-content fingerprints as operational representations of security-relevant instructions and artifact relationships. These constructs do not directly establish behavior during execution, maliciousness, or historical copying.

Rule presence, changes in match counts, and newly detected capabilities are distinct outcomes. A count increase can occur within an already detected capability, while a negative delta means fewer detected matches rather than necessarily lower risk. A missing entry in `rule_deltas` does not establish that a rule never matched. SQL screening patterns approximate scanner behavior and are selection heuristics rather than security findings.

`artifact_groupings` groups artifacts by exact name and normalized description, while `analyze_family` loads qualifying artifacts across description groups sharing an exact name. Neither shared metadata nor high similarity proves common ancestry. Similarity measures establish candidate relatedness; resolved declared provenance, chronology, and asymmetric containment provide direction evidence. Similarity-only relationships retain uncertainty about direction.

A sibling-content fingerprint indicates differences in bundled file content when composition data is available, not their security significance. The current wrapper scans only `SKILL.md`, so a sibling-only relationship with no scanner delta does not imply that sibling changes are harmless.

## Internal Validity

Errors in candidate generation, similarity analysis, provenance interpretation, ordering, extraction, normalization, or rule matching can affect the reported relationships and scanner changes. Exact-name loading can group independently developed skills together and miss related skills whose names differ. Screening within description groups can also miss variation across those groups.

Declared provenance, commit dates, and asymmetric containment provide direction evidence but do not guarantee original authorship or direct descent. Commit history follows the artifact at its current path, so moves or renames may obscure earlier history. Supported provenance fields must resolve within the loaded exact-name family. An unsuccessful source lookup does not establish that the source is absent from the entire dataset, and a pair that also fails similarity criteria does not isolate a source-resolution failure.

Selected manual inspections identified uneven recognition of equivalent operation types and artificial count differences caused by line-ending formats. The wrapper normalizes line endings before scanning, and the corrected case is retained for regression checking. This fix addresses the observed issue, not every possible formatting sensitivity or scanner coverage gap.

Only selected comparisons were manually inspected. Saved reports are automated output rather than independent ground truth, and the sample does not establish scanner accuracy or complete validation of inferred relationships.

## External Validity

The revised Sprint 1 sample contains 43 artifacts across 10 exact-name families and produces 17 directed comparisons in the saved reports. Selection was purposeful and aimed to keep the sample below approximately 50 artifacts for focused tool validation. It has no separate random component.

Cases were chosen for informative relationship outcomes, scanner-count changes, newly detected capabilities, and known limitations. This intentionally favors useful validation cases. The earlier approximately 1,400-row design included random seeds and family expansion, but that component does not make the revised sample representative.

Searching stopped because additional screening was time-consuming, not because coverage was exhaustive or statistically optimized. Results describe the method's behavior on selected cases and cannot estimate population-wide risk prevalence or generalize automatically to other repositories, platforms, or datasets.

## Conclusion Validity

Security-relevant instructions can be legitimate parts of development, deployment, or administration. Detected matches and changes in their counts do not by themselves establish maliciousness, exploitability, or increased or decreased risk.

The 17 directed comparisons are not independent observations: relationships may share endpoints or repeated content. Small category counts and deliberately selected cases limit quantitative conclusions. The saved reports demonstrate count deltas in 10 of 12 scanner rules, but this is coverage of observed variation, not a measure of accuracy. EXT-001 and SYS-001 remain without confirmed delta examples.

Ambiguous relationships are listed without directional scanning. A family with zero directed comparisons therefore provides no basis for concluding that its artifacts contain zero scanner matches. Similarly, unchanged aggregate counts can conceal differences in matched text and should not be interpreted as identical behavior.

## Reproducibility Threats

The project team confirmed that `artifact_id` is deterministic for the project's dataset. Revised membership is encoded as 43 IDs in `sql/create_sprint1_samples_view.sql`, which creates or replaces `sample_artifacts`. The embedded ID list is the source of truth for sample membership; the view does not read an external CSV file. Changes to this list must be versioned and kept consistent with the documented sample.

The view stores a query rather than a snapshot of artifact rows. Returned data depends on the underlying database, and IDs absent from that database do not appear in the result. Deterministic IDs for the agreed dataset do not establish identical data across different releases. Dataset identity, dependencies, analysis code, rule definitions, and normalization settings can all affect reproducibility.

The script includes a count query with an expected result of 43, but the saved family-report totals do not verify execution or reconstruction of the view. Validation should check for both missing selected IDs and unexpected returned IDs against the embedded selection list; a matching count alone is insufficient. Earlier frozen-table reconstruction checks apply to the earlier sample, not to this revised view.

## Missing and Incomplete Data

Missing content, chronology, or sibling-composition data can restrict analysis. Missing values do not establish the absence of a behavior or resource; they may reflect incomplete enrichment. Artifact pairs lacking adequate direction evidence remain ambiguous rather than being forced into an ordered comparison.

Commit history may be missing or limited to the current path. Sibling-composition coverage is uneven across repeated content occurrences, limiting comparisons of bundled resources. The current wrapper does not scan sibling-file contents even where those contents are available.

Filtering for available content, relatedness, or supported direction can bias results toward better-enriched records. Exclusions and ambiguity should therefore be reported separately from negative scanner findings.

## Output Scope and Traceability

Reports use artifact IDs, omit text diffs, and serialize scanner comparisons with `verbose=False` to limit exported content. This report describes aggregate results and generalized observations without selected family names, individual artifact IDs, repository identities, or source excerpts.

These measures do not guarantee anonymity or resolve licensing questions. Someone with the dataset can link an artifact ID to its source record, and the local sample view exposes all columns from matching artifacts. Limited exported evidence also means that detailed verification requires access to the corresponding local data and analysis settings.

## Mitigations

- Distinguish candidate relatedness from direction evidence, and preserve ambiguous relationships without directional scanning.
- Separate selection heuristics, observed tool output, selected manual inspection, and unresolved limitations.
- Treat scanner matches as signals rather than proof of risk, and report count changes separately from introduced capabilities.
- Preserve exact-name family context while documenting candidate-generation and provenance-resolution limits.
- Retain the line-ending regression case and the two remaining rule-delta coverage gaps.
- Version the embedded artifact-ID selection and keep the documented sample consistent with it.
- Verify membership and dataset identity before claiming successful reconstruction of the revised sample.
- Record incomplete inputs and distinguish unscanned cases from negative findings.
- Keep broader census and stratified manual-review plans separate from completed Sprint 1 validation.
- Record methodological decisions and output constraints in research decision records and report documentation.