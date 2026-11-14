# Threats to Validity

This document explains the main limitations of the Sprint 3 analysis: what the scanner can recognize, how reliably the method compares related artifacts, and how far the findings can be generalized. The manual-review observations below have not been fully adjudicated.

## Construct Validity

### Rule-Based Security Detection

The scanner uses rule-based text patterns to identify security-sensitive behavior such as command execution, file-system access, network access, credential handling, external code execution, and system modification.

The main concerns are:

- A match may appear in documentation or an example rather than an instruction that will actually be executed.
- The scanner may miss behavior expressed in a form that the current rules do not recognize.
- A change in match count does not necessarily mean that risk increased or decreased.
- A security-sensitive capability is not necessarily malicious or unsafe.

For example, a skill may mention `curl` while explaining an API without instructing an agent to run it. Conversely, a script using Node.js `os.platform()` or `os.arch()` to read system information may produce no rule matches. These calls can be legitimate, but their absence from findings does not establish that all security-relevant behavior was detected.

Scanner findings are therefore treated as **static risk signals, not confirmed vulnerabilities**. Sprint 3 review notes identify possible errors in both directions. In two Trial 3 `mcp-builder` comparisons, a reviewer questioned RI-003 because URLs were reformatted but their hostnames had appeared in the base artifact. Eight Trial 1 directed-case notes identify candidate missed indicators, although those reviews remain pending and some cases are not fully assessable. Six Trial 3 directed-case notes describe potentially relevant sibling-file instructions that were not reflected in the reported comparison evidence, including package installs, cleanup commands, a Python subprocess call, and permission changes. These are case-level observations, not adjudicated scanner-error counts; examples and missing context can change the final classification.

Additional Sprint 3 reviewer feedback identifies a potential RI-010 gap for relative script paths: `./scripts/verifier-fan-in.sh run` was recognized as a local-script invocation, while `scripts/verifier-fan-in.sh run` was reportedly missed. Both can invoke the same script, depending on the execution context. This is a candidate false-negative mechanism, not a confirmed false-negative RI without checking the full base-to-derived change and whether the text instructs execution rather than merely mentions a path. A separate scope question concerns explicit browser launches such as `open https://example.test/page`: the current RI-003 policy does not consistently treat them as network operations, unlike recognized network-client commands. Whether they should qualify requires a definition change, not merely a pattern fix.

### Candidate-Family Matching and Similarity

The project first uses same-name skills to find possible comparison candidates and then uses content similarity and other available evidence to determine whether artifacts appear to be related.

The main concerns are:

- Two unrelated skills may share the same name.
- A reused skill that was renamed may be missed by the initial grouping.
- Similarity results depend on the selected method and thresholds.
- Candidate-family membership does not establish copying, authorship, or the original source.

A matching name or similarity score is therefore treated as evidence of a possible relationship, not proof of one. In Trial 3, a reviewer judged three of five sampled `no-related-edge` pairs to be related, judged one uncertain, and judged one not related. This suggests that the current thresholds can miss substantively similar artifacts, but five deliberately sampled cases cannot establish a general missed-relationship rate. Relatedness also does not establish copying or direction.

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

The saved automated Sprint 3 results are reproducible, but they are **not independent ground truth**. The reported **63 of 300 families (21.0%)** with supported indicators is an automated rate in the sampled cohort, not a human-confirmed incident rate or a population-wide estimate.

Initial annotations exist for all **90 directed** and **45 relationship** review cases, but review status is not uniform:

- **Trial 1:** All 30 directed reviews are marked `pending`; the 15 relationship reviews are marked `complete`.
- **Trial 2:** All 30 directed and 15 relationship cases are marked `complete` and identify reviewers. However, 29 directed cases have `indicator_review_scope=not_assessable`, and some relationship notes still describe incomplete checks. These records do not establish fully adjudicated indicator judgments.
- **Trial 3:** All 30 directed and 15 relationship records are marked `complete` and contain substantive reviewer notes, but adjudication of uncertain or contested judgments is not documented.

All three saved execution summaries still state that independent review/adjudication is awaited, and their sample manifests remain provisional. Therefore, these files support **qualitative error analysis**, but do not yet justify finalized precision, recall, reviewer-agreement, or corrected incidence estimates. A potentially missed command is not automatically a false-negative RI; the complete indicator criteria, evidence coverage, relatedness, and direction must be assessed.

Additional limits remain:

- Some comparisons reuse artifacts or underlying content, so their observations are not independent.
- Ambiguous relationships are intentionally left without directional conclusions; some sampled relationships may have been missed entirely.
- Counts from the selected families and deliberately stratified review subsets cannot be treated as population-wide risk estimates.

Related artifacts may share substantial reused or generated content, potentially inflating pair-level findings. Family-level reporting reduces—but does not eliminate—this dependence, because templates can also be shared across families. The study records these limitations rather than revising the frozen scanner or automated outcome counts. Final adjudication and approvals should be recorded before making stronger validation claims.

## Reproducibility

The analysis depends on the selected GitSkills release dataset, the project's derived analysis tables, the selected samples, and the versions of the analysis code and rules used to generate the results.

The repository documents how to acquire the data, build the analysis tables, reconstruct the samples, and run the notebooks. The Sprint 3 sample manifests and review files preserve sampling seeds, code and rule identity, selected cases, and checksums. The Sprint 3 scanner and automated results remain fixed under the recorded configuration. Reviewer observations document coverage limitations and opportunities for future improvements; they do not retroactively change the reported findings. The original automated summaries should remain unchanged while reviewers reconcile annotation statuses and record final adjudications and approval references. Results should identify the dataset release, sample, and analysis configuration so that later changes can be distinguished from the frozen trials.
