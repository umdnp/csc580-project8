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

Run all pytest tests with:

```shell
uv run pytest tests/pytests -v
```

To run only the sample-skill analyzer tests:

```shell
uv run pytest tests/pytests/test_sample_skills.py -v
```

A specific sample case can be selected with `-k`:

```shell
uv run pytest tests/pytests/test_sample_skills.py -v -k repo-status-reporter
```

### SQL Preparation Tests (Story 6.1)

Run the SQL preparation tests from the repository root:

```shell
uv run pytest tests/pytests/test_data_preparation.py -v
```

The tests execute the production `sql/create_analysis_tables.sql` and
`sql/update_artifact_groupings.sql` directly against synthetic records in an
isolated in-memory DuckDB. They do not read or alter the local GitSkills database,
download data, or execute artifact content.

Coverage includes description normalization, eligibility filters and the
50-character body boundary, exact-name selection, description variants, source
artifact/repository links, and retention of identical artifact occurrences.
Sibling tests check sorted multiset fingerprints, duplicate hashes, file renames,
directory exclusion, missing content versus missing hashes, known-empty versus
unknown composition, stale-value clearing, repeatable updates, and summary counts.
Group IDs are checked for consistent membership within a run, not fixed numeric
values across database builds.

The normalization regression checks that leading tabs and trailing newlines do
not split equivalent descriptions. Whitespace is collapsed before the final
trim. A scanner integration test checks that merging description groups preserves
the family scanner's full structured findings for a constructed comparison.
The [normalization change record](../../docs/decisions/RDR-010-description-whitespace-normalization.md)
documents database compatibility, measured population impact, and verification.
These checks exercise the preparation policy documented in
[RDR-003](../../docs/decisions/RDR-003-grouping-and-sibling-fingerprints.md);
they do not validate the research population or inferred relationships manually.

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
