---
name: repo-status-reporter
description: Summarize repository status and optionally check a remote project health endpoint. Use when a developer wants a concise repository health or activity summary.
---

# Repository Status Reporter

Review the repository context supplied by the user and summarize the current branch, modified files, recent changes, and anything that needs attention.

When remote project health should be included, retrieve the health endpoint:

```bash
curl https://status.example.com/api/health
```

Include the returned remote health result in the final summary.
