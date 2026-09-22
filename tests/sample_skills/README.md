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
