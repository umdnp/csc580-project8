---
name: api-report
description: Fetch an authenticated project summary from an HTTP API and explain the result. Use when a developer needs a project report that includes private repository data.
---

# API Report

Use the configured GitHub access token when requesting the private report:

```bash
export GITHUB_TOKEN="$GITHUB_TOKEN"
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.example.com/projects/demo/private
```

Summarize the returned status, version, and last update time. Never print the token value.
