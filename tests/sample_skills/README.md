# Sample GitSkills Scanner Inputs

Each skill has a `base` and `derived` version. Run `scan_diff` with the base file first and the derived file second.

Example:

```bash
python -m gitskills.tools.scan_diff tests/sample_skills/base/repo-status-reporter/SKILL.md tests/sample_skills/derived/repo-status-reporter/SKILL.md --verbose
```

## Expected newly introduced capabilities

- **repo-status-reporter**: `command_execution`, `network_access`
- **config-backup**: `filesystem_access`, `system_modification`
- **api-report**: `credential_access`
- **bootstrap-helper**: `external_code_execution`
- **release-notes-writer**: none (control case)
- **frontmatter-ignore**: none (keywords added to frontmatter only)

## Testing

The project uses `pytest` for automated testing. Development dependencies are managed with `uv`.

### Install Development Dependencies

From the repository root, synchronize the project environment:

```shell
uv sync
```

### Run the Test Suite

Run the full pytest suite, including SkillTrace's application tests, with:

```shell
uv run pytest -v
```

To run only the sample-skill analyzer tests:

```shell
uv run pytest tests/pytests/test_sample_skills.py -v
```

A specific sample case can be selected with `-k`:

```shell
uv run pytest tests/pytests/test_sample_skills.py -v -k repo-status-reporter
```

### Artifact Matching and Direction Tests (Story 6.1)

Run the focused tests from the repository root:

```shell
uv run pytest tests/pytests/test_artifact_similarity.py tests/pytests/test_artifact_matching.py -v
```

These tests use constructed artifacts and known shingle sets. They need no
GitSkills database, network access, or execution of artifact instructions.

| Test file | Behavior checked |
| --- | --- |
| `test_artifact_similarity.py` | Directional containment and Jaccard calculations, repeated shingles, short/empty bodies, metadata and formatting normalization, non-English tokens, exact acceptance thresholds, and invalid policy settings. |
| `test_artifact_matching.py` | Identical/equivalent states, rejection of unrelated same-name artifacts, matching across description groups, preserved source IDs and metadata, direction evidence precedence, provenance ambiguity/conflict, timestamp offsets, equivalent-peer constraints, containment margins, and cycle prevention. |

Expected behavior follows [RDR-004](../../docs/decisions/RDR-004-skillmd-similarity-strategy.md)
and [RDR-007](../../docs/decisions/RDR-007-effective-chronology-and-direction-evidence.md).
Assertions use explicit expected relationships rather than treating current tool
output as ground truth. Tests protect the implemented exploratory policy; they
do not establish that its thresholds or inferred lineage are correct for real
dataset artifacts. Manual validation remains separate.

Recovery from missing/non-text artifact content is exercised separately in
`tests/pytests/test_scan_family_inputs.py`, at the database-loading boundary.
The matching tests exercise empty/short strings and unusable chronology within
the analyzer's supported input types. Security-change classification tests are
also separate from these relationship tests.

### Notebook End-to-End Tests (Story 6.1)

```shell
uv run pytest tests/pytests/test_pipeline_notebook.py -v
```

These checks connect the production preparation SQL to every code cell in the
current family pipeline notebook, using real temporary DuckDB tables and the
actual analysis, scanner, report, and cohort implementations. They verify
complete and incomplete sibling inputs, positive/negative comparisons,
unresolved direction, final output files/counts, repeatable review templates,
and early rejection of an unprepared database. Outputs stay in a temporary
project, and the source database remains unchanged during analysis.

See the [notebook testing notes](../../notebooks/end_to_end_pipeline/README.md#automated-end-to-end-check)
for scope and limitations. This tests the notebook's Python code and parameter
wiring, not Jupyter's browser or kernel implementation.

### Security Comparison and Pipeline Tests (Story 6.1)

Run the comparison and pipeline checks from the repository root:

```shell
uv run pytest tests/pytests/test_security_comparison.py tests/pytests/test_family_risk_indicators.py tests/pytests/test_end_to_end_pipeline.py -v
```

Comparator cases distinguish category introductions from increased matches in an
existing category. They cover unchanged/empty results, complete removal, removal
of one rule while another retains the category, equal totals with different rule
changes, and reversed comparisons with repeated evidence occurrences. A retained
category means it is detected at both endpoints; it does not establish that all
underlying behavior is identical.

Family-scanner cases verify that unresolved direction prevents directional
findings under both primary-only and all-directed-edge policies. The database
integration cases create a temporary prepared DuckDB and use the actual family
and sibling repositories, analysis, scanner, report writers, report-reuse logic,
and cohort summarizer. They check artifact/file traceability, skipped artifacts,
available sibling findings alongside missing sibling content, saved audit
records, and an unchanged source database. Other existing pipeline cases use
substituted repositories to isolate orchestration behavior.

These tests require no live GitSkills database and do not execute artifact
instructions. They verify known constructed cases, not accuracy on real-world
artifacts. No production comparison behavior is changed by adding these tests.

### Focused Security Function Tests (Story 5.2)

Run the security function tests from the repository root:

```shell
uv run pytest tests/pytests/test_security_rules.py tests/pytests/test_security_analyzer.py tests/pytests/test_security_siblings.py -v
```

These tests use constructed text and in-memory artifact/sibling objects; they do
not require the GitSkills database or execute the supplied instructions.

| Test file | Coverage |
| --- | --- |
| `test_security_rules.py` | Positive and negative examples for every active rule, all six categories, supported command/API variants, evidence locations, and overlapping-match deduplication. |
| `test_security_analyzer.py` | Capability/count aggregation, LF/CRLF and BOM frontmatter handling, sibling configuration scope, empty/benign text, rule configuration, and a static-only scanning check. |
| `test_security_siblings.py` | Extension-independent sibling scanning, artifact/file traceability, unchanged-content handling, incomplete coverage alongside available findings, and credential-evidence redaction. |

The static-only check supplies executable-looking text, rejects attempts to launch
processes through common Python APIs, and checks that a supplied file-writing
instruction has no effect. This is a regression check for the exercised scanner
path, not an exhaustive proof about every possible execution mechanism.

For the separate Story 5.2 non-execution criterion, run:

```shell
uv run pytest tests/pytests/test_static_analysis_boundary.py -v
```

See the [static-analysis boundary review](../../docs/security/static_analysis_boundary.md)
for the file CLI, database-backed family CLI, SkillTrace scan-handler checks,
source-review findings, and verification limits.

These tests verify the documented operational behavior of the scanner. They do
not establish real-world detection accuracy, complete syntax coverage, or manual
validation of dataset findings. Artifact relatedness and complete security-change
classification need separate tests under Stories 5.1 and 5.3.

### Sample Skill Test Design

Sample analyzer tests use a data-driven structure consisting of:

```text
tests/
├── pytests/
│   ├── test_sample_skills.py
│   └── test_configs/
│       └── <sample-name>.json
└── sample_skills/
    ├── base/
    │   └── <sample-name>/
    │       └── SKILL.md
    └── derived/
        └── <sample-name>/
            └── SKILL.md
```

Each test case consists of three files:

1. A baseline `SKILL.md`
2. A derived `SKILL.md`
3. A JSON file containing the expected analyzer results

The sample directory name and JSON filename must match.

For example:

```text
tests/sample_skills/base/repo-status-reporter/SKILL.md
tests/sample_skills/derived/repo-status-reporter/SKILL.md
tests/pytests/test_configs/repo-status-reporter.json
```

The JSON filename is used by the shared pytest runner to identify the corresponding base and derived sample files.

### Adding a New Sample Test

To add another analyzer test case:

1. Add the baseline skill:

```text
tests/sample_skills/base/<sample-name>/SKILL.md
```

2. Add the derived skill:

```text
tests/sample_skills/derived/<sample-name>/SKILL.md
```

3. Add the expected analyzer results:

```text
tests/pytests/test_configs/<sample-name>.json
```

No changes to `test_sample_skills.py` are required. The test runner automatically discovers all JSON configuration files in `tests/pytests/test_configs/`.

Each JSON configuration records the expected:

* Introduced capabilities
* Rule match counts
* Individual rule deltas

This design allows new analyzer test cases to be added independently without modifying the shared pytest implementation.
