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
