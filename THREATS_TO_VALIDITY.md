# Threats to Validity

This document explains the main limitations of the Sprint 3 analysis: what the scanner can recognize, how reliably the method compares related artifacts, and how far the findings can be generalized. Team-adjudicated annotations and computed validation summaries are now available for all three trials. These findings describe only the manually reviewed samples and do not change the frozen automated results.

## Construct Validity

### Rule-Based Security Detection

The scanner uses rule-based text patterns to identify security-sensitive behavior such as command execution, file-system access, network access, credential handling, external code execution, and system modification.

The main concerns are:

- A match may appear in documentation or an example rather than an instruction that will actually be executed.
- The scanner may miss behavior expressed in a form that the current rules do not recognize.
- A change in match count does not necessarily mean that risk increased or decreased.
- A security-sensitive capability is not necessarily malicious or unsafe.

For example, a skill may mention `curl` while explaining an API without instructing an agent to run it. Conversely, a script using Node.js `os.platform()` or `os.arch()` to read system information may produce no rule matches. These calls can be legitimate, but their absence from findings does not establish that all security-relevant behavior was detected.

Scanner findings are therefore treated as **static risk signals, not confirmed vulnerabilities**. Adjudicated Sprint 3 reviews demonstrate errors in both directions. In two Trial 3 `mcp-builder` comparisons (`3032753` to `3026710` and `3032753` to `3031464`), RI-003 treated reformatted evidence for existing network destinations as newly introduced. Both were rejected on review, and a later scanner fix addressed this pattern; the frozen study results were not rerun. Because their comparison direction was uncertain, both cases were excluded from the calculated precision subset.

Other reviewed comparisons support missed local-script invocations (RI-010), network changes (RI-003), and operations in supporting files. They also reveal rule-level extraction problems, including misclassified file operations. Missing sibling content and incomplete source evidence can prevent a full assessment, even when an individual behavior is visible. A missed rule match does not necessarily imply a missed risk indicator.

Relative script paths illustrate one detection limit: `scripts/verifier-fan-in.sh run` was missed in a reviewed comparison. Another unresolved *definition* issue is whether launching a browser with an HTTP(S) address should qualify as RI-003 network activity; the rules do not treat such launches consistently. These cases illustrate why scanner coverage depends on both its patterns and the definitions of its indicators. Details of individual cases belong in the [evaluation report](report/sections/08-evaluation-and-validation.md).

### Candidate-Family Matching and Similarity

The project first uses same-name skills to find possible comparison candidates and then uses content similarity and other available evidence to determine whether artifacts appear to be related.

The main concerns are:

- Two unrelated skills may share the same name.
- A reused skill that was renamed may be missed by the initial grouping.
- Similarity results depend on the selected method and thresholds.
- Candidate-family membership does not establish copying, authorship, or the original source.

A matching name or similarity score is therefore treated as evidence of a possible relationship, not proof of one. In the final Trial 3 adjudications, **three of five** sampled `no-related-edge` pairs were judged related and **two not related**. Across the 45 relationship-review cases, the computed summary records **42 agreements and three disagreements** with the automated relatedness classification. These judgments suggest that the current thresholds can miss substantively similar artifacts, but the deliberately stratified samples do not establish a population-wide missed-relationship rate. Relatedness also does not establish copying or direction.

See [RDR-003](docs/decisions/RDR-003-grouping-and-sibling-fingerprints.md) and [RDR-004](docs/decisions/RDR-004-skillmd-similarity-strategy.md).

### Language and Input Scope

The scanner examines the `SKILL.md` instruction body and eligible supporting files, not its YAML frontmatter. Metadata fields and declared tools do not by themselves show that an operation is being performed, so this is a deliberate scanning boundary—not a claim that metadata can never contain relevant instructions. The main detection concern is behavior expressed in an unrecognized form, including non-English prose without recognizable commands, URLs, paths, or credential references. Such behavior may be missed even when the underlying skill content is available.

See [RDR-002](docs/decisions/RDR-002-language-and-frontmatter-scanning.md).

## Internal Validity

### Earlier/Later Ordering

Question 4 requires us to determine whether security-sensitive behavior was **introduced**, so related artifacts need a reasonable earlier/later ordering.

GitSkills does not provide complete historical file contents or commit history for every artifact.

The main concerns are:

- `first_commit_at` is the earliest commit observed for the artifact in the available GitSkills history, not guaranteed proof of when the skill was originally created or introduced.
- File moves or renames may hide earlier history.
- The earliest artifact observed in the dataset may not be the true original.
- Source information written in a skill may be incomplete or incorrect.
- Some relationships may not contain enough evidence to determine which artifact came first.

The project uses the strongest available evidence to establish direction and leaves a relationship unresolved when the evidence is not strong enough. Unresolved relationships should not be used to claim that a behavior was introduced or removed.

When chronology or provenance evidence is unavailable, directional containment may provide a plausible ordering based on content similarity. However, this does not establish the actual historical sequence. Sprint 3 relationship notes also question direction in some pairs judged substantively related. Conclusions based on containment-only or otherwise uncertain ordering should therefore be interpreted cautiously; human recognition of related content cannot substitute for chronology or provenance.

See [RDR-007](docs/decisions/RDR-007-effective-chronology-and-direction-evidence.md).

### Alternative Explanations

A newly introduced security-sensitive behavior does not automatically mean that reuse or modification made a skill less secure.

For example, a later skill may add a network request, package installation, or file operation because its intended functionality changed.

Changes may also shift risk rather than simply increase or decrease it. For example, bundling documentation instead of fetching it online removes a network dependency, but the bundled copy could be outdated or altered. The scanner cannot determine which approach is safer from this change alone.

The analysis separates **what changed** (observable in the artifacts) from **what the change means** (which requires interpretation). A security-sensitive change alone does not establish malicious intent or increased risk.

**Confounding factors.** Family size and intended functionality may influence our findings. Larger families provide more opportunities to detect security-sensitive changes, while new operations may reflect legitimate functional requirements rather than increased risk. We did not control for these factors, so our results describe observed changes rather than establish causal relationships.

### Missing and Incomplete Data

Some GitSkills records have incomplete history, metadata, or related-file information.

Missing data can:

- prevent a relationship from being established;
- leave the earlier/later direction unresolved;
- hide behavior contained in unavailable related files; or
- bias the analysis toward records that have more complete metadata and history.

Missing information should be reported as missing or unresolved rather than interpreted as evidence that a behavior or relationship is absent. Across the saved Sprint 3 trials, **211 of 2,157** primary comparisons have incomplete evidence coverage, including **81 of 340** comparisons with supported indicators. Even a comparison labelled complete is complete only within the implemented extraction scope, not across every possible form of behavior.

## External Validity

### Sprint 3 Cohort and Manual-Review Samples

The final study consists of **three non-overlapping, stratified samples of 100 skill families each**, selected using seeds 5801, 5802, and 5803. The fixed 20/55/20/4/1 size-group allocation deliberately oversamples larger families. Selection requires at least one usable primary directed relationship, and later trials exclude previously selected names. The **300 families, 6,570 loaded occurrences, and 2,157 primary comparisons** are the study's observed sample, not a representative sample of all GitSkills families.

Each trial also has **30 directed-pair cases** drawn from six review strata and **15 relationship cases** drawn from three strata (review seed 580): **90 directed and 45 relationship cases in total**. These subsets deliberately include positive, negative, ambiguous, and coverage-limited cases. Their raw proportions cannot estimate corpus prevalence or scanner accuracy without a justified assessment scope and sampling adjustment. Review notes remain separate from the frozen automated results.

See [RDR-013](docs/decisions/RDR-013-sprint3-sampling-and-edge-selection.md) and [RDR-014](docs/decisions/RDR-014-stratified-family-sampling-method.md).

### Dataset Coverage

The analysis is limited to the selected GitSkills release dataset and the artifacts collected by its mining process.

The dataset should not be assumed to represent every agent skill, repository, platform, or development workflow. Results from this project therefore apply first to the data that was actually collected and analyzed.

## Conclusion Validity

The saved automated Sprint 3 results are documented for reproduction, but they are **not independent ground truth**. The reported **63 of 300 families (21.0%)** with supported indicators is an automated rate in the sampled cohort, not a human-confirmed incident rate or a population-wide estimate.

All **90 directed** and **45 relationship** review records are marked `adjudicated` and `complete`, and the saved summaries now include validation metrics. Of the 90 directed comparisons, **56** were marked `all_assessed` and **34** `not_assessable`; only **29** met the additional requirements for computed indicator metrics, including supported relatedness and direction, sufficient evidence coverage, and complete indicator judgments.

Across the eleven indicator categories in those **29 eligible comparisons**, the summaries report **13 true positives, 7 false negatives, and no counted false positives**, giving **100% observed micro-precision (13/13)** and **65.0% observed micro-recall (13/20)**. These small, deliberately stratified and non-independent review samples cannot support a population-wide accuracy estimate. In particular, **zero counted false positives does not mean zero actual false positives**: the two adjudicated `mcp-builder` RI-003 errors were excluded because their comparison direction was uncertain. Team adjudication does not itself measure independent inter-rater agreement.

Additional limits remain:

- Some comparisons reuse artifacts or underlying content, so their observations are not independent.
- Ambiguous relationships are intentionally left without directional conclusions; some sampled relationships may have been missed entirely.
- Counts from the selected families and deliberately stratified review subsets cannot be treated as population-wide risk estimates.
- Cases excluded for missing content, uncertain direction, or incomplete scope cannot be treated as negative findings, even where individual operations can be observed.

Related artifacts may share substantial reused or generated content, potentially inflating pair-level findings. Family-level reporting reduces—but does not eliminate—this dependence, because templates can also be shared across families. The study records these limitations rather than revising the frozen scanner or automated outcome counts. These review metrics characterize eligible adjudicated examples, not a corrected prevalence estimate for the 300-family cohort.

## Reproducibility

The analysis depends on the selected GitSkills release dataset, the project's derived analysis tables, the selected samples, and the versions of the analysis code and rules used to generate the results.

The repository documents dataset acquisition, analysis-table preparation, family sampling, and notebook execution. Sprint 3 manifests record the original code and rules, sample selection, and checksums. The **original automated counts remain frozen**: **63 of 300 families (21.0%)** and **340 of 2,157 primary directed comparisons (15.8%)** had supported indicators under the recorded rules. Later scanner improvements were not used to rescan those trials.

The final adjudication files were processed separately against the saved samples and summaries, without rerunning family analysis or scanning. Each trial's `review/summary.json` now includes sample-limited validation metrics; pre-adjudication summaries were preserved. This verifies a *review-metric update*, not a clean-environment end-to-end reproduction of all three Sprint 3 trials. Saved sample manifests still carry provisional approval metadata, so the team's subsequent approval needs to remain traceable through separate review records. These boundaries matter when comparing the frozen automated study with later manual judgments or scanner revisions.
