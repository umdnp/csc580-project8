\clearpage

# Method and Implementation

## Method Overview

The study measures whether modified or reused GitSkills introduce security-relevant behavior that was absent from an earlier version or source artifact. For each eligible ordered comparison, the method scans the base and derived artifacts with the same versioned rule catalog, constructs a rule and category profile for each artifact, and measures which signals were introduced, removed, or retained in the derived artifact.

The current implementation combines exact-name candidate loading, token-shingle similarity, evidence-based direction inference, and a static scanner with 13 registered rules across six categories. The executable tools support individual file comparisons and family-level review. A completed population census and statistical validation are separate research tasks; the existence of these tools does not establish that those tasks have been completed. Rule definitions, dependency versions, code revision, and analysis settings must be recorded for each reported run.

## Analysis Algorithm

### Artifact Profiling

Let \(R(a)\) be the set of rule identifiers detected in artifact \(a\), and let \(C(a)\) be the set of security-relevant categories represented by those rules. For each artifact, the static analyzer records the matched rules, categories, counts, and match evidence required for validation.

### Base-Derived Comparison

For an eligible ordered pair with base artifact \(b\) and derived artifact \(d\), the comparison stage computes:

$$
R_{introduced} = R(d) \setminus R(b)
$$

$$
R_{removed} = R(b) \setminus R(d)
$$

$$
R_{retained} = R(b) \cap R(d)
$$

These sets describe the study's intended rule-presence measures. The current comparator directly emits introduced-category flags and nonzero rule-count deltas; it does not serialize separate introduced, removed, and retained rule sets. Those sets can be derived from complete endpoint profiles.

The same set operations define category-level measures:

$$
C_{introduced} = C(d) \setminus C(b), \quad
C_{removed} = C(b) \setminus C(d), \quad
C_{retained} = C(b) \cap C(d)
$$

A comparison has a rule-level introduction when $|R_{introduced}| > 0$, and it has a category-level introduction when $|C_{introduced}| > 0$. Both measures are retained because a new rule may appear within a category already present in the base artifact.

### Match-Count Changes and Introduced Capabilities

Let \(n_r(a)\) be the number of matches for rule \(r\) in artifact \(a\). The implemented comparator calculates:

$$
\Delta_r = n_r(d) - n_r(b)
$$

A positive delta means more matched text for that rule, a negative delta means fewer matches, and zero means an unchanged count. The `rule_deltas` output includes only rules whose counts differ. Its omission of a rule therefore does not establish that the rule was absent from both artifacts.

Three outcomes must be distinguished:

| Outcome | Condition | Interpretation |
| --- | --- | --- |
| New rule presence | Base count is zero and derived count is positive | A previously undetected rule appears. |
| Introduced capability | A category is absent from the base profile and present in the derived profile | A previously undetected category appears. |
| Increased existing signal | Both counts are positive and the derived count is larger | More matches occur without necessarily introducing a rule or category. |

For example, increasing package-install matches from one to three produces a delta of +2. If external code execution was already detected in the base, this increase does not introduce that capability. Conversely, a new rule may appear inside an existing category. Total counts are sums of rule matches, not counts of unique actions: one instruction may match multiple rules. Equal totals can conceal different matched text or offsetting changes.

### Outcome Computation

The planned population-level primary outcome is the proportion of eligible comparisons in which the derived artifact contains at least one detected security-relevant signal that was absent from the base:

$$
\text{Rule introduction rate} =
\frac{\text{eligible comparisons with at least one introduced rule}}
{\text{eligible comparisons analyzed}}
$$

$$
\text{Category introduction rate} =
\frac{\text{eligible comparisons with at least one introduced category}}
{\text{eligible comparisons analyzed}}
$$

Secondary outputs may include:

- the count and percentage of comparisons introducing each rule or category;
- distributions of introduced-rule and introduced-category counts;
- counts and percentages of comparisons with removed signals;
- counts and percentages with retained signals but no introduced signals;
- counts and percentages with no detected profile change;
- introduction rates by relationship type;
- introduction rates for same-repository and cross-repository comparisons; and
- the numbers of distinct artifacts, content SHAs, and repositories represented.

Every reported denominator will identify whether it represents comparison occurrences, unique artifact relationships, or unique content-SHA pairs.

## Threat Model and Rule Catalog

The static analyzer is intended to identify security-relevant instructions or behaviors such as executable commands, URLs, scripts, file operations, credential-related instructions, and other categories adopted by the final threat model. A rule match is a reviewable signal, not a conclusion that an artifact is malicious or unsafe.

Each rule in the catalog should define:

- a stable rule identifier;
- rule name and description;
- higher-level security-relevant category;
- detection logic or pattern reference;
- severity or review priority, if adopted by the threat model;
- known false-positive conditions;
- positive and negative examples; and
- rule-catalog version.

### Category Rationale

The categories operationalize the trust boundaries described in `THREAT_MODEL.md`: instructions can cause an agent to execute programs, communicate externally, access local data, handle secrets, obtain executable dependencies, or alter its host environment. These are consequential capabilities even when required by a legitimate task. The catalog favors inspectable technical indicators that can be matched without running untrusted content. This is a rationale for the current scope, not evidence that the catalog detects every security-relevant behavior.

| Category | Registered rules and indicators | Reason for inclusion | Interpretation limit |
| --- | --- | --- | --- |
| Command execution | CMD-001: shell-language code fences; CMD-002: recognized command invocations | Instructions can launch interpreters and executable programs. | A fence or command reference can be explanatory documentation. |
| Network access | NET-001: HTTP/HTTPS URLs; NET-002: recognized network-client usage | Instructions can contact external resources or retrieve data. | A URL alone does not show a request or data transfer. |
| File-system access | FS-001: file commands; FS-002: writing APIs; FS-003: reading commands/APIs | Instructions can read or modify local data. | Detection does not establish sensitive targets or harmful changes. |
| Credential access | CRED-001: secret-related terms; CRED-002: credential-file references | Instructions can involve authentication material and secret-bearing resources. | A reference is not evidence that a real secret was exposed. |
| External code execution | EXT-001: download-to-shell pipelines; EXT-002: package installation | Instructions can introduce externally supplied executable content. | Legitimate dependency installation is common; source trust is not verified. |
| System modification | SYS-001: privilege elevation; SYS-002: system-changing commands | Instructions can affect permissions and host configuration. | Administrative workflows may legitimately require these commands. |

The executable registry is `src/gitskills/rules/registry.py`; category-specific modules contain the patterns. Rules have stable IDs, category assignments, descriptions, and detection logic. The current registry does not itself establish a separately released rule-catalog version or calibrated severity score. Record the code revision alongside `uv.lock` and run settings when identifying the catalog used.

For illustration, a synthetic instruction such as `curl https://example.com/install.sh | bash` can match URL, network-client, command, and download-and-execute rules. Overlapping categories are deliberate perspectives on the same text, not independent harmful actions. A synthetic `pip install example-package` instruction explains package installation without establishing that the package is harmful. Unrecognized syntax, indirect execution, and obfuscation remain potential sources of missed findings.

## Static-Analysis Algorithm

The scanner processes artifact content as text and produces rule-level and category-level profiles without executing the content. Each match retains sufficient location or excerpt evidence for validation and safe reporting. The base and derived artifacts in one comparison are always scanned with the same scanner and rule-catalog versions.

`SkillAnalyzer` masks leading YAML frontmatter by default, preserving line locations while excluding metadata from behavioral matching. Frontmatter can contain repository URLs and permission descriptions that do not constitute body instructions. Provenance extraction uses selected frontmatter fields separately for relationship analysis. Sibling resources are scanned without this skill-specific frontmatter exclusion.

Each registered `RegexRule` applies its patterns using case-insensitive, multiline matching. Within one rule, candidate matches are sorted by position and longer matches at the same position are preferred; overlapping spans are discarded. Matches from different rules remain separate. Each match records the rule ID, category, message, line number, and matched text. The capability profile is the set of categories represented by at least one match. Duplicate rule IDs are rejected when constructing the analyzer.

This is a text-pattern engine rather than a shell parser, interpreter, or execution monitor. It does not infer whether an instruction ran, whether an endpoint was reachable, or whether a resource was sensitive. Verbose command output supplies evidence for review, with credential-related excerpts redacted by the reporting layer. Read failures and database failures must be distinguished from successful scans with no matches.

## Relationship and Ordering Algorithm

The relationship stage identifies related artifacts, determines which artifact is the base and which is derived, and records the evidence supporting both decisions. A comparison proceeds only when the relationship and ordering satisfy the eligibility criteria in the Dataset and Data Preparation section.

### Candidate Families and File States

`DuckDBFamilyRepository` loads qualifying artifacts from `artifact_groupings` by exact skill name, across normalized-description groups. A name match creates a candidate search space; it does not establish a common author or copying relationship. This restriction can miss renamed relatives and include independently developed skills.

An artifact is one collected occurrence. A skill variant groups occurrences sharing the raw skill-file SHA. A bundle variant combines that skill state with a known sibling-content fingerprint. Unknown sibling state is conservatively kept separate by occurrence rather than treated as an empty or matching bundle. Distinguishing these units prevents identical skill text from hiding changes in associated scripts or resources.

### Similarity and Relatedness

For each distinct skill variant, the implementation masks frontmatter, tokenizes the body, lowercases tokens, and constructs the set of distinct contiguous five-token shingles. Technical structures such as URLs, paths, flags, and dotted identifiers are preserved where the tokenizer recognizes them. Repetition of an identical shingle does not increase its weight.

For shingle sets \(A\) and \(B\):

$$
J(A,B)=\frac{|A\cap B|}{|A\cup B|}, \qquad
K(A\rightarrow B)=\frac{|A\cap B|}{|A|}
$$

Jaccard measures symmetric overlap; containment measures how much of one representation appears in the other. Empty-set comparisons receive zero similarity. The current exploratory defaults require maximum directional containment of at least 0.80, Jaccard of at least 0.30, and at least five shared shingles. All three conditions must pass for distinct skill variants. Bundle variants with the same raw skill SHA can be compared without a distinct-skill similarity test.

Consider a synthetic example with 100 shingles in A, 250 in B, and 90 shared. Containment A to B is 0.90, containment B to A is 0.36, and Jaccard is 90/260, approximately 0.346. The pair passes the defaults. Requiring Jaccard as well as containment prevents a small text embedded in a much larger file from qualifying solely because all its shingles were retained. These are exploratory heuristics, not validated probabilities of copying; threshold calibration and sensitivity analysis remain evaluation work.

Qualifying similarity relationships form connected clusters. If A relates to B and B relates to C, all three can occupy one cluster even if A and C fail the direct pairwise test. Scores of 1.0 describe the shingle representation and do not necessarily establish byte-identical original files.

### Direction Evidence and Uncertainty

The implementation considers direction only after relatedness is established. It first resolves supported declared-source fields (`derived_from`, `upstream_skill`, `source_repo`, and `upstream_source`) against the loaded family. Conflicting declarations preserve an ambiguous relationship. A resolved source provides the strongest direction basis; an unresolved reference does not show that the source is absent from the full dataset.

Equivalent states without a resolved declared source remain undirected. For other relationships, the decision order is:

1. Compare distinct effective observed chronology points. Available evidence can come from an equivalent bundle peer; reports distinguish that proxy from direct chronology.
2. If chronology does not resolve the pair, check whether an observed state predates the other repository's creation boundary. Repository creation is a boundary, not the skill's creation date.
3. Otherwise, use asymmetric containment when the difference between the two containment scores is at least 0.10. Infer direction from the more-contained state toward the other state.
4. Preserve the relationship as ambiguous if no basis resolves direction.

`first_commit_at` describes observed history at the current path, which can omit history before a move or rename. Containment supplies a structural hypothesis, not a verified temporal sequence. Consequently, the terms parent and child denote inferred base and derived endpoints throughout this report, not proven direct historical descent.

### Graph Selection and Change Classification

Candidate directed edges are ranked by evidence basis: declared source, direct chronology, equivalent-peer chronology, repository boundary, and containment. Tie-breaking considers evidence count, temporal proximity where applicable, similarity, shared shingles, and deterministic endpoint identity. The selector retains at most one predecessor per target bundle and rejects candidates that would create a cycle. Other supported directed relationships remain available as additional comparisons; a related pair need not become a selected parent edge.

Relationships are classified as skill-only, siblings-only, skill-and-siblings, equivalent, or unknown according to skill similarity/state and available sibling fingerprints. A root candidate is a node with no selected predecessor, not a verified original author or original publication.

The state diagram provides a conceptual model of a candidate bundle pair's classification. The code computes these outcomes rather than maintaining a mutable state field. Declared-source decisions take precedence over fallback evidence; equivalent states without a resolved source remain undirected. Predecessor selection considers the surrounding graph, not just the isolated pair.

```{#fig-relationship-state .plantuml source="report/diagrams/relationship-state.puml" caption="Conceptual UML state diagram for relationship classification. Scanner flags are separate from lineage outcomes."}
```

Ambiguous relationships are retained as uncertainty and excluded from directional family scanning. They must not be counted as comparisons with no security signals.

## Tools and Implementation Architecture

The implementation is organized around four functional components:

1. **Extractor:** Reads the relevant records and metadata from `agent_skills_release.db`.
2. **Relationship builder:** Produces candidate ordered base-derived relationships and eligibility evidence.
3. **Static analyzer:** Applies the versioned rule catalog to unique artifact content and creates rule and category profiles.
4. **Comparator and reporter:** Joins profiles to eligible relationships, computes changes and aggregate measures, and writes reproducible analysis artifacts.

The project uses Python 3.12 or newer, DuckDB for analysis queries, and dependencies recorded in `pyproject.toml` and `uv.lock`. `FamilyAnalyzer` implements relationship construction; `SkillAnalyzer` and `compare_results` implement text scanning and paired comparison; `FamilyRiskAnalyzer` orchestrates directed-family review. Tests use pytest. SkillTrace is a FastAPI application for inspecting generated family reports, content, diffs, and pair scans. The report sources are Markdown combined through `report/pandoc.yaml`.

| Entry point | Input and purpose | Scan scope |
| --- | --- | --- |
| `analyze_family` | Exact family name and DuckDB; infer and report relationships | Relationship analysis; no security scan |
| `scan_diff` | Two local paths, base first; compare rule counts and capabilities | The two supplied skill bodies |
| `scan_family` | Exact family name and DuckDB; review selected directed edges | Skill bodies and available sibling content for applicable changes |
| SkillTrace | Saved analysis reports plus DuckDB; inspect graph and content | Its pair scan compares selected skill bodies |

`scan_family` flags positive skill-rule count deltas. Its sibling review considers aggregate count increases and rule matches in new or changed destination content; such a finding can exist without a positive aggregate delta. Missing sibling content or SHA evidence is recorded as incomplete coverage. Neither an unflagged pair nor an incomplete scan establishes safety.

### Family-Scan Component Interactions

The sequence diagram follows the successful `scan_family` execution path. The CLI loads both artifacts and sibling records before passing them to `FamilyRiskAnalyzer`; that analyzer invokes `FamilyAnalyzer` and reviews the selected directed edges. Calls to the scanner can reuse cached results. Sibling review is conditional on the classified change type and records unavailable evidence separately from negative findings. Argument, database, and output-write failure paths are omitted for readability.

```{#fig-family-scan .plantuml source="report/diagrams/family-scan-sequence.puml" width="5.6in" caption="Sequence diagram of family scanning, including conditional sibling analysis and comparison."}
```

## End-to-End Pipeline

The broader population-analysis target is:

1. Load the required source tables from `agent_skills_release.db`.
2. Extract analyzable artifact content and traceability metadata.
3. Identify candidate relationships and determine base-derived ordering.
4. Apply eligibility filters and record exclusions.
5. Identify unique content SHAs.
6. Scan each unique SHA with the configured scanner and rule catalog.
7. Join cached profiles back to all applicable artifact occurrences.
8. Compare base and derived profiles to calculate introduced, removed, and retained rules and categories.
9. Produce structured result tables, summary measures, validation inputs, logs, and report-ready figures or tables.

The pipeline records the scanner version, rule-catalog version, configuration, and other run metadata needed to connect every result to the implementation that produced it.

The implemented family workflow is narrower than that census target: `DuckDBFamilyRepository` loads one exact-name family, `FamilyAnalyzer` selects relationships, and `FamilyRiskAnalyzer` scans selected edges using per-analysis caches. Skill scans are reused by skill SHA; sibling scans reuse available content by SHA, with occurrence-based fallback where necessary. This does not establish a persisted, population-wide profile store.

After completing the database preparation documented in `data/README.md`, install dependencies with `uv sync` and use `uv run python -m gitskills.tools.analyze_family --help`, `uv run python -m gitskills.tools.scan_diff --help`, and `uv run python -m gitskills.tools.scan_family --help` for executable options. Family tools accept an exact name and `--db PATH`; `scan_diff` accepts the base and derived paths. An analysis report can be saved to `apps/skilltrace/reports` for SkillTrace. Scan reports must use a separate directory because their schema differs from the graph report schema.

## Baselines and Test Fixtures

The earlier or source artifact serves as the within-relationship baseline for each derived artifact. This paired baseline supports a direct claim about whether a signal was detected in the derived artifact but not in its identified base; it is not a general-purpose prediction baseline.

The implementation uses constructed base and derived pairs under `tests/sample_skills`, with expected outputs under `tests/pytests/test_configs`. The shared pytest runner checks introduced categories, total counts, and individual rule deltas. These fixtures establish expected behavior on selected inputs; they are not empirical population observations or a measurement of scanner precision and recall. Additional coverage of removals, unchanged counts with changed text, and difficult direction cases should be evaluated explicitly.

[TODO: Define any additional baseline rule set, heuristic, comparison method, or ablation required by the final evaluation, and explain what question that baseline answers.]

## Design Decisions

### Ordered Comparisons Rather Than Isolated Artifacts

The research question concerns behavior newly introduced through modification or reuse. An ordered base-derived pair therefore provides a more direct unit of analysis than an isolated artifact.

### Rule-Level and Category-Level Measurement

The method reports both levels because category-only comparisons can hide the introduction of a new rule inside an already-present category, while rule-only results may be too granular to summarize clearly.

### One Rule Catalog per Comparison and Run

Scanning both sides with the same rule definitions prevents catalog changes from being mistaken for changes in artifact content. A run should identify those definitions by code revision or an explicit catalog version; after a rule change, affected analyses must be rerun before comparison with newer outputs.

### SHA-Based Caching Without Statistical Deduplication

Within a family analysis, scanning a skill SHA once avoids redundant computation while preserving the selected artifact relationships. The broader census design should retain artifact and relationship occurrences when reusing profiles, so a cache does not silently redefine the research population.

### Census of Eligible Comparisons

The planned census will attempt to analyze every eligible comparison. Current family-level runs and development subsets support testing and exploration; they do not establish completion of the population-level run.

### Evidence Retention and Auditable Filtering

The family tools retain relationship bases, direction evidence, rule findings, and incomplete sibling coverage. The broader population pipeline also needs auditable eligibility and exclusion records; those records must be verified before claiming complete population accounting.

### Static Analysis and Cautious Interpretation

The project does not execute untrusted artifact content. Detected introductions are reported as static risk signals. They do not, by themselves, prove malicious intent, vulnerability, exploitability, or real-world impact.

## Generated Outputs

The broader study is expected to produce:

- an artifact table with traceability fields;
- a relationship table with ordering evidence and eligibility status;
- versioned scanner profiles;
- an ordered comparison table with introduced, removed, and retained signals;
- exclusion counts and reasons;
- aggregate summary tables;
- a seeded manual-validation sample;
- logs and run metadata; and
- report-ready tables and figures generated from structured results.

Currently implemented outputs include family-analysis JSON from `analyze_family`, paired comparison JSON from `scan_diff`, family review JSON from `scan_family`, and optional verbose evidence. These formats serve different purposes and are not interchangeable. A complete population comparison table, calibrated accuracy measures, and census summary figures remain deliverables to verify rather than completed results.

## Reproducibility

A reproducible run must identify:

- the dataset release or snapshot and integrity information;
- the required environment and dependency versions;
- configuration and command-line arguments;
- scanner and rule-catalog versions;
- random seeds used for validation sampling;
- executable commands for each pipeline stage and the complete pipeline;
- output locations and expected artifacts; and
- known platform, resource, or data-availability limitations.

[TODO: Add the final setup instructions and exact clean-environment execution command after the implementation is complete.]
