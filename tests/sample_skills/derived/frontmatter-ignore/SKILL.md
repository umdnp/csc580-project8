---
name: frontmatter-ignore
description: Test skill for verifying that frontmatter is ignored by the analyzer.
allowed-tools:
  - "curl https://frontmatter-only.example.com"
  - bash
---

# Frontmatter Ignore Test

Retrieve the example status endpoint:

```bash
curl https://example.com/status