\clearpage

# Threats to Validity

## Construct Validity

The study uses rule-based indicators, candidate groupings, similarity measures, provenance evidence, and sibling-content fingerprints as operational representations of security-relevant instructions and artifact relationships. These constructs do not directly establish behavior during execution, maliciousness, or historical copying.

Rule presence, changes in match counts, and newly detected capabilities are distinct outcomes. A count increase can occur within an already detected capability, while a negative delta means fewer detected matches rather than necessarily lower risk. A missing entry in `rule_deltas` does not establish that a rule never matched. SQL screening patterns approximate scanner behavior and are selection heuristics rather than security findings.

`artifact_groupings` groups artifacts by exact name and normalized description, while `analyze_family` loads qualifying artifacts across description groups sharing an exact name. Neither shared metadata nor high similarity proves common ancestry. Similarity measures establish candidate relatedness; resolved declared provenance, chronology, and asymmetric containment provide direction evidence. Similarity-only relationships retain uncertainty about direction.

A sibling-content fingerprint indicates differences in bundled file content when composition data is available, not their security significance. The saved Sprint 1 wrapper reports scanned only `SKILL.md`. The current family scanner also reviews available sibling content, while `scan_diff` and SkillTrace pair scans compare skill bodies. Findings from these surfaces must be labeled separately; an absent delta on one surface does not establish safety on another.

## Internal Validity

Errors in candidate generation, similarity analysis, provenance interpretation, ordering, extraction, normalization, or rule matching can affect the reported relationships and scanner changes. Exact-name loading can group independently developed skills together and miss related skills whose names differ. Screening within description groups can also miss variation across those groups.

Declared provenance, commit dates, and asymmetric containment provide direction evidence but do not guarantee original authorship or direct descent. Commit history follows the artifact at its current path, so moves or renames may obscure earlier history. Supported provenance fields must resolve within the loaded exact-name family. An unsuccessful source lookup does not establish that the source is absent from the entire dataset, and a pair that also fails similarity criteria does not isolate a source-resolution failure.

Selected manual inspections identified uneven recognition of equivalent operation types and artificial count differences caused by line-ending formats. The earlier wrapper normalized line endings before scanning and retained the corrected case for regression checking. Normalization must be verified for each current input path before treating its counts as interchangeable. The historical fix addresses the observed issue, not every possible formatting sensitivity or scanner coverage gap.

Only selected comparisons were manually inspected. Saved reports are automated output rather than independent ground truth, and the sample does not establish scanner accuracy or complete validation of inferred relationships.

## External Validity

The revised Sprint 1 sample contains 43 artifacts across 10 exact-name families and produces 17 directed comparisons in the saved reports. Selection was purposeful and aimed to keep the sample below approximately 50 artifacts for focused tool validation. It has no separate random component.

Cases were chosen for informative relationship outcomes, scanner-count changes, newly detected capabilities, and known limitations. This intentionally favors useful validation cases. The earlier approximately 1,400-row design included random seeds and family expansion, but that component does not make the revised sample representative.

Searching stopped because additional screening was time-consuming, not because coverage was exhaustive or statistically optimized. Results describe the method's behavior on selected cases and cannot estimate population-wide risk prevalence or generalize automatically to other repositories, platforms, or datasets.

The Sprint 2 manual-validation design selects 13 pair-level cases from this same purposeful sample: five positive, four negative, and four ambiguous. It is a fixed method-validation set, not a random sample of GitSkills or of all eligible comparisons. Reviewers have not yet annotated these cases, so the sample provides no observed precision, recall, reviewer agreement, or error-rate estimate. See the [validation protocol](docs/validation/validation_protocol.md) and [validation sample](data/validation/validation_sample.csv).

## Conclusion Validity

Security-relevant instructions can be legitimate parts of development, deployment, or administration. Detected matches and changes in their counts do not by themselves establish maliciousness, exploitability, or increased or decreased risk.

The 17 directed comparisons are not independent observations: relationships may share endpoints or repeated content. Small category counts and deliberately selected cases limit quantitative conclusions. The saved Sprint 1 reports demonstrated count deltas in 10 of the then-current 12 scanner rules, with no confirmed delta examples for EXT-001 and SYS-001 in that selection. The current catalog contains 13 rules. Historical coverage and counts cannot establish coverage or accuracy for the revised catalog; reruns must identify their code revision and scan scope.

Ambiguous relationships are listed without directional scanning. A family with zero directed comparisons therefore provides no basis for concluding that its artifacts contain zero scanner matches. Similarly, unchanged aggregate counts can conceal differences in matched text and should not be interpreted as identical behavior.

The available report figures and count summaries are generated from the Sprint 1 notebook's 33 view-order adjacent comparisons. They are not output from the planned Sprint 2 analysis pipeline, and their positive count deltas do not identify introduced capabilities or verified parent-child changes. Sprint 2 analysis outputs and manual annotations are not yet available; conclusions about their rates and category distribution must wait for those outputs.

## Reproducibility Threats

Team members independently downloaded the source database and ran the SQL queries on their own machines, reporting accurate reproduction of the results. This is positive empirical evidence of repeatability for those runs. It does not remove the following limitations concerning build-local identifiers, snapshot identity, and verification scope.

The saved Sprint 1 selection uses 43 build-local artifact IDs in `sql/create_sprint1_samples_view.sql`, which creates or replaces `sample_artifacts`. Both artifact and group numbers originate from unordered `row_number()` expressions, so independently rebuilding the same source does not guarantee identical numeric assignments. Reopening the same saved database preserves the existing mapping. The ID list in `data/sample-population/sample_population.csv` is a separate record; the view does not read it. These representations could diverge unless checked together.

The view stores a query rather than a snapshot of artifact rows. Returned data depends on candidate membership and the artifact/repository joins. A remapped numeric ID can select a different source occurrence rather than simply producing a missing row. Reproduction across builds therefore requires the dataset snapshot and an ID-to-source mapping based on `(repo_full_name, path)`; subgroup reconciliation uses exact name and normalized description. Content hashes provide an additional integrity check but do not uniquely identify occurrences. Dataset identity, dependencies, analysis code, rule definitions, and normalization settings can all affect reproducibility.

The script includes a count query with an expected result of 43, but the saved family-report totals do not verify execution or reconstruction of the view. Validation should check every selected ID and compare membership in both directions; a matching count alone is insufficient. Earlier frozen-table reconstruction checks apply to the earlier sample, not to this revised view.

## Missing and Incomplete Data

Missing content, chronology, or sibling-composition data can restrict analysis. Missing values do not establish the absence of a behavior or resource; they may reflect incomplete enrichment. Artifact pairs lacking adequate direction evidence remain ambiguous rather than being forced into an ordered comparison.

Commit history may be missing or limited to the current path. Sibling-composition coverage is uneven across repeated content occurrences, limiting comparisons of bundled resources. The current family scanner can scan available sibling content and records unavailable changed resources or unknown SHA evidence as incomplete coverage. This extends the older skill-only workflow but does not eliminate missing-data bias. Content recovered through a matching SHA should retain its evidence source, and missing content must not be interpreted as absence of behavior.

Filtering for available content, relatedness, or supported direction can bias results toward better-enriched records. Exclusions and ambiguity should therefore be reported separately from negative scanner findings. Candidate construction additionally requires valid frontmatter, a body longer than 50 characters, non-null name and description, and at least two qualifying occurrences with the same exact name. This excludes malformed or very short skills, metadata-poor artifacts, and singleton names before similarity analysis. The 50-character threshold is a heuristic rather than a validated quality boundary. Any later prevalence estimate must state whether its denominator is the source population, the 943,257 retained candidates in the local audit, or the further restricted set of supported directed comparisons.

## Output Scope and Traceability

Reports use artifact IDs, omit text diffs, and serialize scanner comparisons with `verbose=False` to limit exported content. This report describes aggregate results and generalized observations without selected family names, individual artifact IDs, repository identities, or source excerpts.

These measures do not guarantee anonymity or resolve licensing questions. Someone with the dataset can link an artifact ID to its source record, and the local sample view exposes all columns from matching artifacts. Limited exported evidence also means that detailed verification requires access to the corresponding local data and analysis settings.

## Mitigations

- Distinguish candidate relatedness from direction evidence, and preserve ambiguous relationships without directional scanning.
- Separate selection heuristics, observed tool output, selected manual inspection, and unresolved limitations.
- Treat scanner matches as signals rather than proof of risk, and report count changes separately from introduced capabilities.
- Preserve exact-name family context while documenting candidate-generation and provenance-resolution limits.
- Recheck the historical line-ending regression across current input paths, and reassess rule-delta coverage against the current 13-rule catalog.
- Version the embedded artifact-ID selection, reconcile it with the CSV list, and verify the ID-to-source mapping before reuse in another database build.
- Verify membership and dataset identity before claiming successful reconstruction of the revised sample.
- Record incomplete inputs and distinguish unscanned cases from negative findings.
- Keep broader census and stratified manual-review plans separate from completed Sprint 1 validation.
- Record methodological decisions and output constraints in research decision records and report documentation.