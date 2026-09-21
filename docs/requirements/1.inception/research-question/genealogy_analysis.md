# GitSkills Genealogy Analysis

- **Database:** `agent_skills_release.db`
- **Generated:** 2026-09-15T22:06:41

## 1. History Coverage

| Metric | Value |
|---|---:|
| total_artifacts | 3797117 |
| history_fetched | 458548 |
| multiple_commits | 154339 |
| max_commit_count | 708 |
| avg_commit_count | 2.23 |

### Top 25 Artifacts by Commit Count

#### 1. `jorcan/automejora_agentes`

- **Path:** `active_skills/invoice_organizer/skill.md`
- **Commit count:** 708
- **First commit:** 2026-03-14T21:36:07Z
- **Last commit:** 2026-03-15T06:09:11Z

**First commit message:**

```text
Auto-improvement: invoice_organizer score 1.0
```

**Last commit message:**

```text
Auto-improvement: invoice_organizer score 1.0
```

#### 2. `generalbusiness-ai/keep`

- **Path:** `SKILL.md`
- **Commit count:** 446
- **First commit:** 2026-01-30T21:34:57Z
- **Last commit:** 2026-07-21T21:17:15Z

**First commit message:**

```text
Draft
```

**Last commit message:**

```text
v0.162.0 — Add token-budgeted flow output and prevent guidance drift
```

#### 3. `daishiman/AIWorkflowOrchestrator`

- **Path:** `.claude/skills/aiworkflow-requirements/SKILL.md`
- **Commit count:** 406
- **First commit:** 2026-01-04T03:49:53Z
- **Last commit:** 2026-04-22T05:50:21Z

**First commit message:**

```text
refactor(skills): 18-skills.md仕様に準拠したスキル構造の大規模マイグレーション (#184)

* refactor(skills): 18-skills.md仕様に準拠したスキル構造の大規模マイグレーション

スキルフレームワークを18-skills.md仕様に完全準拠させるため、
以下の主要な変更を実施:

主な変更内容:
- SKILL.md: Anchors/Trigger形式のfrontmatterに統一
- Level*.md形式のreferencesを廃止、トピック別referencesに移行
- agents/: Task仕様書テンプレートに準拠したエージェント追加
- assets/: 実装テンプレートの追加・整理
- scripts/: log_usage.mjs等の標準スクリプト追加
- skill_list.md: event-driven-architecture, event-sourcingを追加

対象スキル（5スキル重点改善）:
- eslint-configuration: ESLint設定専門スキル
- estimation-techniques: 見積もり技法スキル
- event-driven-architecture: イベント駆動アーキテクチャ
- event-driven-file-watching: ファイル監視スキル
- event-sourcing: イベントソーシングパターン

全スキルバリデーション: ✓ 成功（0エラー, 0警告）

Note: テンプレートファイルは{{placeholder}}構文を使用しているため
Prettierのフォーマットチェックをスキップ

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <<redacted>>

* refactor(skills): 18-skills.md仕様への完全準拠マイグレーション（継続作業）

# 変更概要
- 残りのスキルファイルを18-skills.md仕様に準拠した構造に移行
- 階層的なreferences構造（Level1-4）を統合してSKILL.mdに集約
- 旧形式のagents、scripts、assetsを18仕様に適合
- 新規スキル`aiworkflow-requirements`を追加（プロジェクト要件管理用）
- 新規コマンド`diff-to-pr`を追加（差分→PR作成自動化）
- .claude/配下をlint/formatから除外（.prettierignore/.eslintignore追加）

# 主要変更
## スキル構造の統合
- `references/Level[1-4]_*.md` → `SKILL.md` 内に統合
- 不要なEVALS.json、LOGS.mdファイルを削除
- 重複するagentsファイルを整理・統合

## 新規追加
- `.claude/skills/aiworkflow-requirements/` - プロジェクト要件スキル
  - 45個以上のリファレンスドキュメント（API、アーキテクチャ、セキュリティ等）
  - エージェント定義（create-spec、update-spec、validate-spec）
  - インデックス（keywords.json、topic-map.md）
- `.claude/commands/ai/diff-to-pr.md` - 差分→PR作成自動化コマンド
- `.prettierignore` / `.eslintignore` - .claude/配下を除外

## 削除ファイル
- 600個以上の旧形式ファイルを削除（Level別references、古いagents等）
- 重複・非推奨のスクリプトファイルを削除

# 影響範囲
- 対象スキル: 200個以上
- 変更ファイル: 約440ファイル（新規追加+変更+削除）
- トークン効率化: references統合により大幅なコンテキスト削減

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <<redacted>>

---------

Co-authored-by: Claude <<redacted>>
```

**Last commit message:**

```text
docs(evals-schema): UNASSIGNED-EVALS-SPEC-SNAKE-CASE-V1-DOCUMENT-001 snake_case v1 EVALSスキーマ正本追記 (#2403)

* docs(evals-schema): UNASSIGNED-EVALS-SPEC-SNAKE-CASE-V1-DOCUMENT-001 snake_case v1 EVALSスキーマ正本追記・Phase12完了

- evals-schema-spec.md §3.3新設: metrics.average_satisfactionの型・値域・v1固有定義を追記
- evals-schema-spec.md §3.4新設: levelsフィールドのLegacyLevelEntry型・完全ツリー構造を定義
- §3対照テーブルのlevels行誤記修正（「配列構造」→「静的オブジェクト（レベル番号文字列キー）」）
- generate-index.js: MANUAL_KEYWORDS定数追加（アンダースコア含む複合語の恒久ホワイトリスト）
- .claude ↔ .agents parity確認済み（diff -qr 差分ゼロ）
- 後続タスク: UNASSIGNED-EVALS-SCHEMA-DIALECT-UNIFICATION-001 / UNASSIGNED-EVALS-VALIDATOR-GUARD-001

Co-Authored-By: Claude Sonnet 4.6 <<redacted>>

* docs(evals-schema): .claude ↔ .agents parity修復（sync-skills-mirror実行）

- topic-map.md / keywords.json の .claude→.agents ミラー同期
- pre-push parity checkをPASSするため再コミット

Co-Authored-By: Claude Sonnet 4.6 <<redacted>>

---------

Co-authored-by: Claude Sonnet 4.6 <<redacted>>
```

#### 4. `daishiman/AIWorkflowOrchestrator`

- **Path:** `.claude/skills/task-specification-creator/SKILL.md`
- **Commit count:** 383
- **First commit:** 2026-01-04T03:49:53Z
- **Last commit:** 2026-04-22T03:05:47Z

**First commit message:**

```text
refactor(skills): 18-skills.md仕様に準拠したスキル構造の大規模マイグレーション (#184)

* refactor(skills): 18-skills.md仕様に準拠したスキル構造の大規模マイグレーション

スキルフレームワークを18-skills.md仕様に完全準拠させるため、
以下の主要な変更を実施:

主な変更内容:
- SKILL.md: Anchors/Trigger形式のfrontmatterに統一
- Level*.md形式のreferencesを廃止、トピック別referencesに移行
- agents/: Task仕様書テンプレートに準拠したエージェント追加
- assets/: 実装テンプレートの追加・整理
- scripts/: log_usage.mjs等の標準スクリプト追加
- skill_list.md: event-driven-architecture, event-sourcingを追加

対象スキル（5スキル重点改善）:
- eslint-configuration: ESLint設定専門スキル
- estimation-techniques: 見積もり技法スキル
- event-driven-architecture: イベント駆動アーキテクチャ
- event-driven-file-watching: ファイル監視スキル
- event-sourcing: イベントソーシングパターン

全スキルバリデーション: ✓ 成功（0エラー, 0警告）

Note: テンプレートファイルは{{placeholder}}構文を使用しているため
Prettierのフォーマットチェックをスキップ

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <<redacted>>

* refactor(skills): 18-skills.md仕様への完全準拠マイグレーション（継続作業）

# 変更概要
- 残りのスキルファイルを18-skills.md仕様に準拠した構造に移行
- 階層的なreferences構造（Level1-4）を統合してSKILL.mdに集約
- 旧形式のagents、scripts、assetsを18仕様に適合
- 新規スキル`aiworkflow-requirements`を追加（プロジェクト要件管理用）
- 新規コマンド`diff-to-pr`を追加（差分→PR作成自動化）
- .claude/配下をlint/formatから除外（.prettierignore/.eslintignore追加）

# 主要変更
## スキル構造の統合
- `references/Level[1-4]_*.md` → `SKILL.md` 内に統合
- 不要なEVALS.json、LOGS.mdファイルを削除
- 重複するagentsファイルを整理・統合

## 新規追加
- `.claude/skills/aiworkflow-requirements/` - プロジェクト要件スキル
  - 45個以上のリファレンスドキュメント（API、アーキテクチャ、セキュリティ等）
  - エージェント定義（create-spec、update-spec、validate-spec）
  - インデックス（keywords.json、topic-map.md）
- `.claude/commands/ai/diff-to-pr.md` - 差分→PR作成自動化コマンド
- `.prettierignore` / `.eslintignore` - .claude/配下を除外

## 削除ファイル
- 600個以上の旧形式ファイルを削除（Level別references、古いagents等）
- 重複・非推奨のスクリプトファイルを削除

# 影響範囲
- 対象スキル: 200個以上
- 変更ファイル: 約440ファイル（新規追加+変更+削除）
- トークン効率化: references統合により大幅なコンテキスト削減

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <<redacted>>

---------

Co-authored-by: Claude <<redacted>>
```

**Last commit message:**

```text
docs(skill): UNASSIGNED-EVALS-SPEC-QUALITY-INSIGHTS-DOCUMENT-001 qualityInsights仕様策定・skill-feedback反映・Phase12完了 (#2408)
```

#### 5. `agentskillexchange/skills`

- **Path:** `skills/sendgrid-mcp-server/SKILL.md`
- **Commit count:** 257
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-18T19:25:48Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
chore: sync published skills from ASE
```

#### 6. `agentskillexchange/skills`

- **Path:** `skills/atlassian-rovo-mcp-server/SKILL.md`
- **Commit count:** 246
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 7. `agentskillexchange/skills`

- **Path:** `skills/slack-mcp-server/SKILL.md`
- **Commit count:** 243
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 8. `nikhgarg/EconCSLib`

- **Path:** `skills/econcs-formalizer/SKILL.md`
- **Commit count:** 241
- **First commit:** 2026-04-23T23:19:51Z
- **Last commit:** 2026-07-10T02:17:28Z

**First commit message:**

```text
Initial EconCSLean formalization library
```

**Last commit message:**

```text
Stop README prose checks in status tooling
```

#### 9. `agentskillexchange/skills`

- **Path:** `skills/docker-compose-generator-skill/SKILL.md`
- **Commit count:** 229
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 10. `agentskillexchange/skills`

- **Path:** `skills/queue-backup-runbook/SKILL.md`
- **Commit count:** 220
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 11. `agentskillexchange/skills`

- **Path:** `skills/clickhouse-query-agent/SKILL.md`
- **Commit count:** 219
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 12. `agentskillexchange/skills`

- **Path:** `skills/pulumi-drift-detector-reconciler/SKILL.md`
- **Commit count:** 218
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 13. `agentskillexchange/skills`

- **Path:** `skills/pagerduty-incident-runbook-automator/SKILL.md`
- **Commit count:** 217
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 14. `agentskillexchange/skills`

- **Path:** `skills/kubernetes-pod-diagnostics-skill/SKILL.md`
- **Commit count:** 216
- **First commit:** 2026-03-20T21:17:14Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 12 new skills from Agent Skill Exchange

New skills:
- kubernetes-pod-diagnostics-skill
- aws-cloudwatch-log-analyzer-skill
- prometheus-alert-resolver-skill
- pagerduty-incident-runbook-skill
- terraform-cloud-orchestrator-skill
- jenkins-pipeline-debugger-skill
- codecov-coverage-tracker-skill
- github-actions-workflow-builder-skill
- semgrep-sast-scanner-skill
- argocd-sync-manager-skill
- eslint-rule-enforcer
- sonarqube-pr-gate-skill
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 15. `agentskillexchange/skills`

- **Path:** `skills/wp-abilities-api/SKILL.md`
- **Commit count:** 215
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 16. `agentskillexchange/skills`

- **Path:** `skills/semgrep-custom-rule-runner-2/SKILL.md`
- **Commit count:** 215
- **First commit:** 2026-03-20T10:16:13Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 23 new skills from agentskillexchange.com

Automated sync: 2026-03-20
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 17. `agentskillexchange/skills`

- **Path:** `skills/stripe-reporting-agent/SKILL.md`
- **Commit count:** 214
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 18. `agentskillexchange/skills`

- **Path:** `skills/sonarqube-rule-enforcement-agent/SKILL.md`
- **Commit count:** 214
- **First commit:** 2026-03-21T18:57:42Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 12 new skills from agentskillexchange.com
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 19. `agentskillexchange/skills`

- **Path:** `skills/semgrep-rule-runner/SKILL.md`
- **Commit count:** 214
- **First commit:** 2026-03-20T20:15:15Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 12 new skills from agentskillexchange.com

New skills:
- terraform-cloud-run-trigger
- jenkins-pipeline-orchestrator
- argocd-deployment-sync-skill
- salesforce-crm-sync-agent
- aws-s3-sqs-pipeline-connector
- github-actions-workflow-generator
- codecov-coverage-analyzer
- stripe-payments-connector
- semgrep-rule-runner
- twilio-sms-voice-bridge
- sonarqube-scanner-skill
- eslint-auto-fix-agent-2
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 20. `agentskillexchange/skills`

- **Path:** `skills/owasp-zap-scanner/SKILL.md`
- **Commit count:** 213
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 21. `agentskillexchange/skills`

- **Path:** `skills/falco-runtime-security/SKILL.md`
- **Commit count:** 212
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 22. `agentskillexchange/skills`

- **Path:** `skills/datadog-apm-anomaly-detector/SKILL.md`
- **Commit count:** 212
- **First commit:** 2026-03-23T19:03:12Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
feat: add 12 new skills from agentskillexchange.com

New skills:
- Grafana Dashboard JSON Migrator
- Argo Workflows DAG Optimizer
- Datadog APM Anomaly Detector
- AsyncAPI Event Catalog Builder
- Buf Protobuf Linter
- PagerDuty Incident Runbook Linker
- Swagger OpenAPI Schema Validator
- Prometheus AlertManager Rule Generator
- OpenTelemetry Trace Aggregator
- Terraform Module Registry Browser
- Helm Chart Template Scaffolder
- GraphQL Introspection Documenter
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 23. `agentskillexchange/skills`

- **Path:** `skills/pagefind-static-low-bandwidth-search-engine/SKILL.md`
- **Commit count:** 211
- **First commit:** 2026-03-29T07:14:47Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
feat: add 4 new skills from ASE marketplace

- astro-content-driven-web-framework
- hugo-static-site-generator-cms-framework
- mermaid-cli-diagram-as-code-renderer
- pagefind-static-low-bandwidth-search-engine
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 24. `agentskillexchange/skills`

- **Path:** `skills/discord-moderation-ai-classification/SKILL.md`
- **Commit count:** 210
- **First commit:** 2026-03-20T09:03:31Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
Add 491 skills from Agent Skill Exchange

Sync 491 new skills from https://agentskillexchange.com
Total skills in repo: 591
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

#### 25. `agentskillexchange/skills`

- **Path:** `skills/datadog-monitor-sync/SKILL.md`
- **Commit count:** 210
- **First commit:** 2026-03-24T04:08:32Z
- **Last commit:** 2026-07-10T13:21:34Z

**First commit message:**

```text
feat: add 12 new skills from ASE

New skills: cloudwatch-anomaly-detector, cookiecutter-project-scaffold-2, datadog-monitor-sync, github-actions-workflow-builder-3, grafana-dashboard-generator-3, makedown-task-runner, mdn-web-api-reference-fetcher, npm-registry-explorer, prometheus-alert-router-3, pypi-package-inspector-2, rust-crate-analyzer, terraform-module-registry-2
```

**Last commit message:**

```text
revert: restore canonical skill files after unsafe sync
```

## 2. Multiple Rows for the Same Repository and Path

**Duplicate repository/path groups found:** 0

## 3. Exact Content Reuse Across Repositories

**Total SHA groups appearing in multiple repositories:** 306088

### Top 50 Cross-Repository SHA Groups

| SHA | Artifacts | Repositories |
|---|---:|---:|
| `5be498e2585843c7137bf9a74e262f57415de5ce` | 1245 | 951 |
| `2f14076e59e6ce5cd6f88007421a85f0bd772520` | 1252 | 914 |
| `4726215301db64a0cc4d41fc3219c61f37a30f4a` | 1176 | 781 |
| `f6a22ddf88fdc7e7b7603f4c9064cc51bd930ad9` | 1409 | 661 |
| `111d2a98c2698b5a202ddae8906f75f16ecfcffd` | 885 | 656 |
| `4ea72cdf014d6b18223e4248ed9444bd3953445a` | 795 | 584 |
| `48cfdabb87941fdce350f3d84b8e51f08b51eab9` | 617 | 573 |
| `7a751fa946b7fd801feb504cb1af6b5b62adcf43` | 772 | 571 |
| `df5000e17ef60ecf400e65bfcd3c58ff88b604c3` | 719 | 564 |
| `8a1a77a47d141967b246adb4da4f91037578ff7d` | 745 | 555 |
| `c5c881be9ebaa2bfcdd02f97de2ebd711ab78803` | 737 | 554 |
| `9f63fee82de84cd4230e1d0e322247b61eb4c94c` | 796 | 550 |
| `65b3a402dbd09b8e83f9d637c6b553875189085c` | 663 | 532 |
| `d3e046a5ae107a6cb23cfb16c219837094ab35d3` | 633 | 493 |
| `2951e559989765293b6fbf83942378a3c2d0cba6` | 598 | 472 |
| `16660d8ceb77af47986bba1c9176c2ff3f287a91` | 647 | 469 |
| `634f6fa42e4e697fa6afd293acd7fb8246574876` | 614 | 458 |
| `22db189c8b17d48f94f11fa0c45343441239ff40` | 708 | 451 |
| `a6a3f5a0798318edb6ccef716cfecce92a50d914` | 531 | 435 |
| `bd04394c675ee54173a093c50eb74da01a2940fa` | 497 | 420 |
| `06cd0a21ee771f6bb7aaba9341a77ca09a8c7d04` | 508 | 415 |
| `a5a69839ef4a161131d80b6daef10037a9686f4a` | 544 | 410 |
| `600b6db41fac7e2081c7528ec6982960892c819d` | 558 | 408 |
| `50a4f9b104357d96361e257adb70454604cd15c0` | 615 | 398 |
| `b93b875fe11cf805bdfbbe5f0e7878a7562896ac` | 591 | 391 |
| `b7f86598b002c99a6be96026443217b6af3c561d` | 594 | 390 |
| `56ea935b74f371bfeb4c7d3c19d5139df866e73b` | 534 | 378 |
| `664663895bcd11b88a632301d830b313cbabb845` | 556 | 367 |
| `a64d6c233a6293c05ab70f67156cc7e30284232a` | 495 | 367 |
| `ceae92ab319216a68274168fba9b63b998b65997` | 488 | 359 |
| `c3b73d8b10ba2539da543f069aabf1d156071176` | 452 | 358 |
| `114c6637a18676ac99b8bd34ffc7c9da61d072cb` | 460 | 350 |
| `d07025bf943345bc1cf15eb923594f889ff881f0` | 451 | 322 |
| `d9ef1949f807d0b41ca85d9a0837ad78bf1c58de` | 492 | 320 |
| `9470cfcfe231a35e46494cddbacdd395991afb1e` | 380 | 307 |
| `c797184ee66bbfd8b60c58b5efdb91880ae8e991` | 372 | 300 |
| `33b14859f2bcd944e800d9f4dc4d71940100effa` | 439 | 294 |
| `ed55bda2fdb0d690ea3b80a1cf28bf848c5ad2b5` | 341 | 294 |
| `c308b43b4b6a856f8d721c594f0907af614b8e2e` | 402 | 287 |
| `e153843cd17ae234c1f2446ba55019d6a128e18e` | 350 | 286 |
| `237988de4a66dd8a71d30a2c24ebe1a86b58d04e` | 320 | 284 |
| `44ead27ef04ffe79ade0c6df7fd696dbcf7b246b` | 396 | 282 |
| `1e7a5dc728fed0a85a28c9dfb6e78ce5a81da7db` | 332 | 278 |
| `c8a857024b80bd3a3553cdfac9a92bec3bd0175e` | 315 | 273 |
| `f5375b908340e1376ed391232a31c5d82d5babfb` | 393 | 266 |
| `decdff43d05908b4c1fc2cfd2d80fc5743440934` | 309 | 265 |
| `c8304f0c9301385e3641b052d6b25b8af11cb6c1` | 357 | 258 |
| `73401865dd7440a43c5243b107a3763e0d2f4aae` | 340 | 255 |
| `85770a38992a7c74d2b3467b03fe5bd4b1287fe6` | 311 | 251 |
| `d056bd183229ca93bd41cf1b8c10c6fd1f30e75f` | 264 | 250 |

## 4. `dedup_primary` Distribution

| dedup_primary | Count |
|---:|---:|
| 0 | 1919136 |
| 1 | 1877981 |

### Top 25 Duplicate SHA Groups and Primary Counts

| SHA | Total | Primaries | Repositories |
|---|---:|---:|---:|
| `f6a22ddf88fdc7e7b7603f4c9064cc51bd930ad9` | 1409 | 1 | 661 |
| `2f14076e59e6ce5cd6f88007421a85f0bd772520` | 1252 | 1 | 914 |
| `5be498e2585843c7137bf9a74e262f57415de5ce` | 1245 | 1 | 951 |
| `4726215301db64a0cc4d41fc3219c61f37a30f4a` | 1176 | 1 | 781 |
| `60251f16a662bacd9fe9556505f6220a2778b592` | 1074 | 1 | 29 |
| `111d2a98c2698b5a202ddae8906f75f16ecfcffd` | 885 | 1 | 656 |
| `9f63fee82de84cd4230e1d0e322247b61eb4c94c` | 796 | 1 | 550 |
| `4ea72cdf014d6b18223e4248ed9444bd3953445a` | 795 | 1 | 584 |
| `7a751fa946b7fd801feb504cb1af6b5b62adcf43` | 772 | 1 | 571 |
| `8a1a77a47d141967b246adb4da4f91037578ff7d` | 745 | 1 | 555 |
| `c5c881be9ebaa2bfcdd02f97de2ebd711ab78803` | 737 | 1 | 554 |
| `df5000e17ef60ecf400e65bfcd3c58ff88b604c3` | 719 | 1 | 564 |
| `313626ac2f4c9c65f7b8267fdc974abb1dc797d3` | 709 | 1 | 211 |
| `22db189c8b17d48f94f11fa0c45343441239ff40` | 708 | 1 | 451 |
| `65b3a402dbd09b8e83f9d637c6b553875189085c` | 663 | 1 | 532 |
| `857c32d0feac93d984e06fbc7c3c5658b9aa2751` | 656 | 1 | 39 |
| `16660d8ceb77af47986bba1c9176c2ff3f287a91` | 647 | 1 | 469 |
| `d3e046a5ae107a6cb23cfb16c219837094ab35d3` | 633 | 1 | 493 |
| `48cfdabb87941fdce350f3d84b8e51f08b51eab9` | 617 | 1 | 573 |
| `50a4f9b104357d96361e257adb70454604cd15c0` | 615 | 1 | 398 |
| `634f6fa42e4e697fa6afd293acd7fb8246574876` | 614 | 1 | 458 |
| `7b44b52b22deff946953dbac8f4aa969ed46104e` | 606 | 1 | 55 |
| `2951e559989765293b6fbf83942378a3c2d0cba6` | 598 | 1 | 472 |
| `72bc0b97e7a6476254a9d5c424c9971748402ec3` | 596 | 1 | 97 |
| `b7f86598b002c99a6be96026443217b6af3c561d` | 594 | 1 | 390 |

## 5. Repository Forks

- **Repositories:** 282200
- **Forks:** 3

### Sample Artifacts from Forked Repositories

#### 1. `azkore/ccusage`

- **Path:** `.claude/skills/use-gunshi-cli/SKILL.md`
- **SHA:** `2cb2545a64508f534c468b55ccaa3914a4675795`
- **Commit count:** N/A
- **First commit:** N/A
- **Last commit:** N/A

#### 2. `ghassanelgendy/egyptian-premier-league-schedule-optimizer`

- **Path:** `.gemini/skills/streamlit-dashboard-builder/SKILL.md`
- **SHA:** `55d75c6db20241c44db0c26e8f02d34de9d9e1d8`
- **Commit count:** N/A
- **First commit:** N/A
- **Last commit:** N/A

#### 3. `ghassanelgendy/egyptian-premier-league-schedule-optimizer`

- **Path:** `gemini-skills/cp-sat-optimizer/SKILL.md`
- **SHA:** `eb976112d103d1c1c5a17b3bacfa88eb871884b1`
- **Commit count:** N/A
- **First commit:** N/A
- **Last commit:** N/A

#### 4. `ghassanelgendy/egyptian-premier-league-schedule-optimizer`

- **Path:** `.gemini/skills/cp-sat-optimizer/SKILL.md`
- **SHA:** `eb976112d103d1c1c5a17b3bacfa88eb871884b1`
- **Commit count:** 1
- **First commit:** 2026-05-16T15:02:29Z
- **Last commit:** 2026-05-16T15:02:29Z

#### 5. `ghassanelgendy/egyptian-premier-league-schedule-optimizer`

- **Path:** `gemini-skills/pandas-data-wrangler/SKILL.md`
- **SHA:** `c1b61b0e68896d991784c93fbc8f12c1f5f5d6c4`
- **Commit count:** N/A
- **First commit:** N/A
- **Last commit:** N/A

#### 6. `ghassanelgendy/egyptian-premier-league-schedule-optimizer`

- **Path:** `.gemini/skills/pandas-data-wrangler/SKILL.md`
- **SHA:** `c1b61b0e68896d991784c93fbc8f12c1f5f5d6c4`
- **Commit count:** 1
- **First commit:** 2026-05-16T15:02:29Z
- **Last commit:** 2026-05-16T15:02:29Z

#### 7. `azkore/ccusage`

- **Path:** `.claude/skills/byethrow/SKILL.md`
- **SHA:** `a62cfce4147908cec27402a3b3ed36802871caae`
- **Commit count:** N/A
- **First commit:** N/A
- **Last commit:** N/A

#### 8. `ProgMastermind/ATOM`

- **Path:** `.claude/skills/atom-patterns/SKILL.md`
- **SHA:** `fc7b48e4f1a5cccd3f22828f74aa23d633358a92`
- **Commit count:** 2
- **First commit:** 2026-05-19T08:52:08Z
- **Last commit:** 2026-05-23T16:05:12Z

## 6. Summary Counts for Content and History

| Metric | Count |
|---|---:|
| total_artifacts | 3797117 |
| with_content | 1880329 |
| with_sha | 3797117 |
| with_commit_count | 458548 |
| with_first_commit | 458548 |
| with_last_commit | 458548 |

---

Analysis complete.
