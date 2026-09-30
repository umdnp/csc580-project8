# SKILL.md Base vs. Derived Comparison

## Overview

This project analyzes and compares `SKILL.md` files from the `base` and `derived` sample skill folders.

The analysis identifies what changed between each base and derived skill and checks newly added content against a set of regex-based security detection rules.

The dataset content is treated strictly as **plain text**. No commands, code blocks, or instructions contained in any `SKILL.md` file are executed.

## Folder Structure

The expected dataset structure is:

```text
sample_skills/
├── base/
│   ├── config-backup/SKILL.md
│   ├── repo-status-reporter/SKILL.md
│   ├── api-report/SKILL.md
│   ├── bootstrap-helper/SKILL.md
│   └── release-notes-writer/SKILL.md
│
└── derived/
    ├── config-backup/SKILL.md
    ├── repo-status-reporter/SKILL.md
    ├── api-report/SKILL.md
    ├── bootstrap-helper/SKILL.md
    └── release-notes-writer/SKILL.md
```

## Setup

Python 3.10 or later is recommended.

Install the required packages:

```bash
pip install jupyter pandas
```

Start Jupyter:

```bash
jupyter notebook
```

Open:

```text
skill_md_comparison.ipynb
```

## Running the Analysis

1. Place the `sample_skills` folder in the project directory.
2. Open `skill_md_comparison.ipynb`.
3. Run the notebook cells from top to bottom.
4. Review the comparison table and detection results.
5. Check the generated CSV and JSON output files.

The notebook automatically matches:

```text
base/<skill>/SKILL.md
```

with:

```text
derived/<skill>/SKILL.md
```

## Extracted Information

For each skill pair, the notebook extracts information including:

- Skill identifier
- Base and derived file paths
- Base and derived content
- Content hashes
- Comparison status
- Added lines
- Removed lines
- Unified diff
- Detection rule matches
- Risk categories
- Matching evidence
- Invalid-record status and skip reason

## Detection Model

The detector uses regex-based rules grouped by risk category.

### Command Execution

- `CMD-001` — Shell code block detected
- `CMD-002` — Command invocation detected

### Network Access

- `NET-001` — HTTP/HTTPS URL detected
- `NET-002` — Network client usage detected

### Filesystem Access

- `FS-001` — File-system command detected
- `FS-002` — File-writing API detected

### Credential Access

- `CRED-001` — Credential or secret reference detected
- `CRED-002` — Credential file reference detected

### External Code Execution

- `EXT-001` — Downloaded content piped to a shell interpreter
- `EXT-002` — External package installation detected

### System Modification

- `SYS-001` — Privilege-elevation command detected
- `SYS-002` — System modification command detected

## Change Detection

Detection rules are applied to the **newly added content in the derived file**.

This is important because the goal is to identify risky capabilities introduced by the derived version rather than reporting behavior that was already present in the base version.

For example:

```text
base/SKILL.md
        ↓
      compare
        ↓
derived/SKILL.md
        ↓
   added content
        ↓
 detection rules
        ↓
Rule ID + Risk Category + Evidence
```

## Invalid Records

Invalid records are not silently ignored.

If a base or derived `SKILL.md` cannot be loaded, the analysis records:

- `status = invalid`
- A clear `skip_reason`

Examples include missing files, invalid paths, unreadable files, or invalid UTF-8 content.

## Output

The notebook saves the extracted analysis records in machine-readable formats:

```text
analysis_output/
├── skill_comparisons.csv
└── skill_comparisons.json
```

These files contain the extracted comparison and detection results for further analysis.

## Tests

The notebook contains automated assertions that verify the loader, comparison, extraction, and detection logic.

Run all notebook cells to execute the tests.

Successful tests display confirmation that the expected behavior passed.

## Safety

`SKILL.md` files may contain shell commands, URLs, package installation instructions, or other potentially sensitive operations.

The notebook **does not execute any content from the dataset**.

Files are read only as UTF-8 text and analyzed using Python string processing, regular expressions, hashing, and diff operations.