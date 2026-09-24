# GitSkills Data Dictionary

This document describes the GitSkills schema used by this project. The source dataset is the MSR 2027 GitSkills release; the project builds a local DuckDB database from that source and adds project-specific identifiers, relationships, and analysis tables.

The physical column types below describe the locally built DuckDB database. Source-field meanings are based primarily on the official GitSkills dataset documentation and paper, with Agent Skills specification context added where it helps explain the data.

## Tables

- [`artifacts`](#artifacts) — one row per discovered skill-file occurrence
- [`artifact_siblings`](#artifact_siblings) — files and directories bundled alongside representative skills
- [`repos`](#repos) — GitHub repository metadata
- [`mining_runs`](#mining_runs) — dataset collection-run provenance
- [`artifact_groupings`](#artifact_groupings) — project-derived RQ4 comparison population and sibling fingerprints

## Dataset Context

The full GitSkills release contains:

| Item | Full dataset |
|---|---:|
| Discovered file occurrences | 3,797,117 |
| Distinct byte-identical contents | 1,877,981 |
| Repositories | 282,200 |
| Repository owners | 195,841 |
| Bundled sibling entries | 7,264,865 |
| Skill histories collected | 458,548 |

GitSkills was collected from public GitHub repositories in July 2026. Every discovered occurrence is retained with its repository and path. Files with identical Git content hashes are grouped together, and one representative occurrence per distinct content is enriched with the full text, parsed front matter, folder composition, repository metadata, and, for a subset, commit history.

> **Important:** The official release is distributed as SQLite and as table-oriented Parquet data. This project imports the source tables into DuckDB and extends them with local surrogate identifiers and derived analysis data.

## Schema at a Glance

| Table | Purpose | Identifier used in the project |
|---|---|---|
| [`artifacts`](#artifacts) | Records each discovered skill-file occurrence and enrichment data for representative contents. | `id` |
| [`artifact_siblings`](#artifact_siblings) | Records files and directories located alongside a representative skill. | `id` |
| [`repos`](#repos) | Stores metadata for repositories containing discovered skills. | `id` |
| [`mining_runs`](#mining_runs) | Records collection-run provenance. | `run_id` |
| [`artifact_groupings`](#artifact_groupings) | Stores the filtered RQ4 comparison population and derived sibling fingerprints. | `id` = `artifacts.id` |

The `id` columns on `repos`, `artifacts`, and `artifact_siblings` are project-generated surrogate identifiers. They are not fields from the GitSkills release and should be treated as local identifiers for the current DuckDB build. The original source identifiers and join fields are retained.

> **DuckDB constraint note:** The project database declares no primary keys, foreign keys, `UNIQUE`, `NOT NULL`, or secondary indexes. The surrogate identifiers and relationships described here are not enforced as database constraints.

## Entity Relationships

```text
repos
  id
   |
   | 1-to-many through artifacts.repo_id
   v
artifacts
  id
   |\
   | \ 0-or-1 through artifact_groupings.id
   |  v
   | artifact_groupings
   |
   | 1-to-many through artifact_siblings.artifact_id
   v
artifact_siblings

artifacts.file_sha
   |
   | groups byte-identical SKILL.md occurrences
   v
other artifacts rows with the same file_sha
```

### Relationship Summary

| From | To | Preferred DuckDB join | Meaning |
|---|---|---|---|
| `artifacts` | `repos` | `artifacts.repo_id = repos.id` | Adds repository metadata to a discovered skill occurrence. |
| `artifact_siblings` | `artifacts` | `artifact_siblings.artifact_id = artifacts.id` | Associates bundled files/directories with the parent skill occurrence. |
| `artifact_groupings` | `artifacts` | `artifact_groupings.id = artifacts.id` | Joins an RQ4 grouping row back to the full artifact record. |
| `artifacts` | `artifacts` | matching `file_sha` | Groups occurrences whose `SKILL.md` files contain exactly the same bytes. |
| `mining_runs` | other tables | no stored row-level foreign key | Provides collection provenance at the run level. |

The original source joins remain available, including `artifacts.repo_full_name = repos.full_name` and the composite `artifact_siblings.repo_full_name/artifact_path` relationship to `artifacts`.

## How Agent Skills Map to This Schema

The Agent Skills specification defines a skill as a directory containing a required `SKILL.md` file and optional supporting resources.

```text
skill-name/
├── SKILL.md
├── scripts/       # optional executable code
├── references/    # optional documentation
├── assets/        # optional templates/resources
└── ...            # other files/directories are allowed
```

GitSkills represents this structure as follows:

| Agent Skills concept | GitSkills representation |
|---|---|
| `SKILL.md` file | One or more rows in `artifacts` |
| Required YAML `name` | `artifacts.name` |
| Required YAML `description` | `artifacts.description` |
| Markdown instructions | Stored inside `artifacts.content`; `body_chars` records body length |
| `scripts/` resources | Rows in `artifact_siblings`; summarized by `artifacts.has_scripts` |
| `references/` resources | Rows in `artifact_siblings`; summarized by `artifacts.has_references` |
| `assets/` or other resources | Rows in `artifact_siblings`; no dedicated `has_assets` field |
| Optional front-matter fields such as `license`, `compatibility`, `metadata`, or `allowed-tools` | Not extracted into dedicated GitSkills columns; they may still be present in raw `artifacts.content` |

The Agent Skills specification uses **progressive disclosure**: an agent normally sees a skill's `name` and `description` first, then loads the full `SKILL.md` when the skill is activated, and loads supporting resources only as needed. This makes `description` particularly important when interpreting or analyzing the dataset.

## Common Conventions

| Convention | Meaning |
|---|---|
| `VARCHAR` | UTF-8 text. Timestamp values are stored as ISO-8601 UTC strings rather than DuckDB timestamp types. |
| Integer status fields | Many bookkeeping fields use integer values. Most behave like `0`/`1` flags, but code should not assume every `*_fetched` field is strictly Boolean unless verified. |
| Empty / `NULL` enrichment fields | Usually mean the enrichment step was not performed, did not return data, or was not applicable. Check the corresponding status field before interpreting missing values. |
| `file_sha` / `entry_sha` | Git object hashes used to identify exact contents or repository entries. |
| Local surrogate identifiers | `id`, `repo_id`, and `artifact_id` are added by the project when building DuckDB. They simplify joins but are not source GitSkills fields. |
| Representative skill | The single row for a distinct `file_sha` where `dedup_primary = 1`. Expensive enrichment is attached primarily to representative rows. |

---

## `artifacts`

**Purpose:** Central table containing one row for each discovered skill-file occurrence. Every occurrence retains its repository and path. Byte-identical files are grouped by `file_sha`, and one occurrence per group is selected as the representative (`dedup_primary = 1`) for enrichment.

**Project identifier:** `id`

**Source logical identifier:** `(repo_full_name, path)`

**Important:** Full text, folder composition, and other enrichment describe the **representative occurrence**. Other repositories containing the same `file_sha` can have different sibling files or histories.

| Column | DuckDB type | Description |
|---|---|---|
| `id` | `BIGINT` | Project-generated surrogate identifier for the artifact occurrence. Used for local joins and not present in the source GitSkills schema. |
| `repo_id` | `BIGINT` | Project-generated relationship to `repos.id`, populated by matching `repo_full_name`. |
| `repo_full_name` | `VARCHAR` | GitHub repository identifier in `owner/repository` form. Original source field; joins to `repos.full_name`. |
| `path` | `VARCHAR` | Repository-relative path of the discovered file. Together with `repo_full_name`, identifies the occurrence. |
| `filename` | `VARCHAR` | Exact basename returned by GitHub code search, preserving capitalization, such as `SKILL.md`, `skill.md`, or `Skill.md`. |
| `location_class` | `VARCHAR` | Classification of where the file appears in the repository. Values are `canonical`, `skills-dir`, or `other`. See [Location classes](#location-classes). |
| `file_sha` | `VARCHAR` | Git blob hash of the file content. Matching hashes mean the files contain exactly the same bytes. Used to group verbatim copies. |
| `discovered_at` | `VARCHAR` | ISO-8601 UTC timestamp when the collection process recorded the file occurrence. |
| `content` | `VARCHAR` | Full file text for enriched representative rows. For a small class of symlinked skills, this can be the symlink target path rather than skill instructions. |
| `content_fetched` | `BIGINT` | Content-retrieval bookkeeping/status field. A nonzero value indicates successful or otherwise recorded retrieval state; use with `content_sha_ok` rather than assuming a generic Boolean interpretation. |
| `frontmatter_valid` | `BIGINT` | Dataset flag indicating whether YAML front matter was successfully recognized/parsed as valid by the collection pipeline. See [Front-matter interpretation](#front-matter-interpretation). |
| `name` | `VARCHAR` | Skill name parsed from YAML front matter. Under the Agent Skills specification, `name` is required and is intended to match the parent directory name. |
| `description` | `VARCHAR` | Skill description parsed from YAML front matter. Under the Agent Skills specification, this required field describes what the skill does and when it should be used; agents use it when deciding whether to activate a skill. |
| `body_chars` | `BIGINT` | Character count of the Markdown body after front-matter processing. Useful as a simple size metric for the skill instructions. |
| `history_fetched` | `BIGINT` | Indicates whether commit-history enrichment was collected for this row. History was collected for standard-location skills plus a size-stratified sample of other skills. |
| `composition_fetched` | `BIGINT` | Indicates whether the surrounding skill-folder composition was inspected. |
| `dedup_primary` | `BIGINT` | `1` for the representative row selected for a distinct `file_sha`; `0` for other byte-identical occurrences. |
| `first_commit_at` | `VARCHAR` | ISO-8601 UTC timestamp of the earliest commit found for the file at its **current path**. A rename can therefore make this later than the file's true origin. |
| `last_commit_at` | `VARCHAR` | ISO-8601 UTC timestamp of the most recent commit found for the file at its current path. |
| `commit_count` | `BIGINT` | Number of commits found for the file at its current path during history enrichment. |
| `sibling_count` | `BIGINT` | Number of sibling file/directory entries recorded for the representative skill folder. |
| `sibling_bytes` | `BIGINT` | Total byte size of recorded sibling entries for the representative skill folder. |
| `has_scripts` | `BIGINT` | Indicates whether the representative skill folder contains bundled script material. |
| `has_references` | `BIGINT` | Indicates whether the representative skill folder contains bundled reference material. |
| `content_sha_ok` | `BIGINT` | Content-integrity bookkeeping. `1` means downloaded bytes reproduced `file_sha`; `2` means content was repaired/retrieved through the Git blob API. |
| `composition_truncated` | `BIGINT` | `1` when folder-composition collection exceeded the listing cap, so the recorded composition can be incomplete; otherwise `0`. |
| `first_commit_author` | `VARCHAR` | Anonymized code for the GitHub account associated with the first commit. The same account receives the same code throughout the dataset; bot accounts retain their login. |
| `first_commit_author_type` | `VARCHAR` | GitHub account type for the first commit: `User`, `Bot`, `Organization`, or empty when the commit has no linked GitHub account. |
| `first_commit_message` | `VARCHAR` | First commit message at the file's current path. Personal names and email addresses are masked; AI-assistant names in `Co-authored-by` trailers may remain. |
| `last_commit_author` | `VARCHAR` | Anonymized code for the GitHub account associated with the most recent commit. |
| `last_commit_author_type` | `VARCHAR` | GitHub account type for the most recent commit: `User`, `Bot`, `Organization`, or empty when unavailable. |
| `last_commit_message` | `VARCHAR` | Most recent commit message found for the file at its current path, with personal names and email addresses masked. |

### Location Classes

| Value | Meaning |
|---|---|
| `canonical` | File stored at the Claude-style canonical location `.claude/skills/<name>/SKILL.md`. |
| `skills-dir` | File stored somewhere under a directory named `skills/`, but not at the canonical path above. |
| `other` | File discovered outside those two location patterns. |

The location class is a **dataset classification**, not a guarantee that the file complies with the current Agent Skills specification.

### Front-Matter Interpretation

The current Agent Skills specification requires YAML front matter containing at least:

| Field | Current specification |
|---|---|
| `name` | Required; 1–64 characters; lowercase letters/numbers/hyphens; no leading, trailing, or consecutive hyphens; should match the parent directory name. |
| `description` | Required; 1–1024 characters; should describe both what the skill does and when to use it. |

Optional specification fields include `license`, `compatibility`, `metadata`, and the experimental `allowed-tools`.

GitSkills exposes only `name` and `description` as dedicated parsed columns. The optional fields are not separate schema columns.

> **Caution:** The GitSkills documentation describes `frontmatter_valid` as front-matter validity/parsing metadata but does not state that this flag certifies every rule in the current Agent Skills specification. Treat it as a dataset parsing/validation flag, not necessarily full specification compliance.

### Deduplication and Representatives

The dataset retains **every occurrence** of a discovered file. Exact duplicates are represented by multiple `artifacts` rows with the same `file_sha`.

For each content-hash group:

- exactly one row is selected as the representative with `dedup_primary = 1`;
- representative selection prefers an occurrence in `.claude/skills/` when one is available;
- a deterministic rule breaks remaining ties;
- the representative is **not assumed to be the original source**;
- full text, front-matter parsing, folder composition, and related enrichment are attached primarily to the representative;
- other rows preserve where additional byte-identical copies occurred.

For analyses whose unit is **distinct skill content**:

```sql
SELECT *
FROM artifacts
WHERE dedup_primary = 1;
```

For measuring **verbatim reuse**:

```sql
SELECT file_sha, COUNT(*) AS copies
FROM artifacts
GROUP BY file_sha
ORDER BY copies DESC;
```

---

## `artifact_siblings`

**Purpose:** Stores files and directories bundled alongside an enriched representative skill. These rows describe the contents of the representative skill's folder, including scripts, references, assets, templates, examples, and other neighboring resources.

**Project identifier:** `id`

**Project parent:** `artifact_id` → `artifacts.id`

**Source logical parent:** `artifacts`, using `repo_full_name` plus `artifact_path`

| Column | DuckDB type | Description |
|---|---|---|
| `id` | `BIGINT` | Project-generated surrogate identifier for the sibling entry. Used for local joins and not present in the source GitSkills schema. |
| `artifact_id` | `BIGINT` | Project-generated relationship to `artifacts.id`, populated from the source `repo_full_name` and `artifact_path` relationship. |
| `repo_full_name` | `VARCHAR` | Repository containing the representative skill. Original source field; joins to `artifacts.repo_full_name` and `repos.full_name`. |
| `artifact_path` | `VARCHAR` | Repository-relative path of the parent skill file. Joins to `artifacts.path` together with `repo_full_name`. |
| `entry_name` | `VARCHAR` | Path/name of the sibling entry relative to the skill folder, such as `scripts`, `references/safety.md`, `assets/template.docx`, or another bundled resource. |
| `entry_type` | `VARCHAR` | Repository entry type. Documented values are `file` and `dir`. |
| `entry_size` | `BIGINT` | Size of the sibling entry in bytes. Directory rows generally have no file content and can report `0`. |
| `entry_sha` | `VARCHAR` | Git object hash for the sibling entry. |
| `content` | `VARCHAR` | Text content for sibling files when fetched. The dataset collects sibling text only up to **100 KB per file**. |
| `content_fetched` | `BIGINT` | Content-retrieval bookkeeping/status field. The Hugging Face table reports integer values in the range `0`–`2`; because the public documentation does not define every numeric state, treat this as a status field rather than a strict Boolean. |
| `skipped_reason` | `VARCHAR` | Reason sibling content was not collected when applicable. Documented cases include binary content, oversized files, or a folder exceeding the listing cap. |

### Notes

- Both files and directories can appear as rows.
- `scripts/`, `references/`, and `assets/` are conventions from the Agent Skills specification, but a skill directory may contain arbitrary additional files and folders.
- `has_scripts` and `has_references` are summary fields on the parent `artifacts` row, not attributes of individual sibling rows.
- There is no corresponding `has_assets` column; assets can still be identified from `artifact_siblings.entry_name`.
- Folder composition describes the **representative occurrence** of a distinct content hash. Another repository containing the same `file_sha` may bundle different resources.

---

## `repos`

**Purpose:** Stores GitHub metadata for repositories containing discovered skill-file occurrences.

**Project identifier:** `id`

**Source logical identifier:** `full_name`

| Column | DuckDB type | Description |
|---|---|---|
| `id` | `BIGINT` | Project-generated surrogate identifier for the repository. Used by `artifacts.repo_id` and not present in the source GitSkills schema. |
| `full_name` | `VARCHAR` | Full GitHub repository name in `owner/repository` form. Original source identifier; joins to `artifacts.repo_full_name`. |
| `owner` | `VARCHAR` | Repository owner login. |
| `stars` | `BIGINT` | GitHub star count recorded when repository metadata was fetched. |
| `forks` | `BIGINT` | GitHub fork count recorded when repository metadata was fetched. |
| `is_fork` | `BIGINT` | Indicates whether the repository itself is a fork. |
| `language` | `VARCHAR` | Primary repository language reported by GitHub. May be empty when GitHub does not report one. |
| `license` | `VARCHAR` | Repository license identifier reported by GitHub. May be empty when no license is detected. |
| `description` | `VARCHAR` | GitHub repository description. Email addresses were masked by dataset processing. |
| `created_at` | `VARCHAR` | ISO-8601 UTC timestamp when the GitHub repository was created. |
| `pushed_at` | `VARCHAR` | ISO-8601 UTC timestamp of the repository's latest push at collection time. |
| `metadata_fetched` | `BIGINT` | Bookkeeping flag indicating whether repository metadata was fetched. |

### Typical Join

```sql
SELECT
    a.repo_full_name,
    a.path,
    a.file_sha,
    r.language,
    r.stars,
    r.is_fork
FROM artifacts AS a
JOIN repos AS r ON r.id = a.repo_id;
```

---

## `mining_runs`

**Purpose:** Records provenance for the collection runs used to discover GitSkills artifacts.

**Logical identifier:** `run_id`

| Column | DuckDB type | Description |
|---|---|---|
| `run_id` | `BIGINT` | Numeric identifier for a collection run. |
| `artifact_type` | `VARCHAR` | Artifact category collected by the run. The attached data uses `agent-skills`. |
| `query` | `VARCHAR` | GitHub code-search query used for discovery. The attached data uses `filename:SKILL.md`. |
| `started_at` | `VARCHAR` | ISO-8601 UTC timestamp when the collection run started. |
| `finished_at` | `VARCHAR` | ISO-8601 UTC timestamp when the run finished or was administratively closed. |
| `discovered` | `BIGINT` | Number of file occurrences recorded as discovered by that run. |
| `note` | `VARCHAR` | Optional collection note. The attached data contains notes marking crashed runs that were closed retroactively during repair. |

### Notes

The full release contains seven collection-run rows. The paper reports that four crashed runs were closed retroactively with a discovered count of zero.

`mining_runs` is a provenance table. There is no `run_id` stored on individual `artifacts` rows, so it cannot be joined to artifacts as a row-level foreign key.

---

## `artifact_groupings`

**Purpose:** Project-derived working table for RQ4. It materializes the filtered artifact population used for candidate comparisons and stores derived sibling-content fingerprints.

**Identifier:** `id`, using the same value as `artifacts.id`

Each row corresponds to one artifact. The table includes valid `SKILL.md` artifacts from `canonical` or `skills-dir` locations with usable content, metadata, and `first_commit_at`, and retains only metadata groups containing at least two artifacts. Grouping uses exact `name` plus a normalized description. The grouping step does **not** filter to `dedup_primary = 1`.

| Column | DuckDB type | Description |
|---|---|---|
| `id` | `BIGINT` | Artifact identifier copied from `artifacts.id`. Joins directly back to the full artifact row. |
| `repo_id` | `BIGINT` | Repository identifier copied from `artifacts.repo_id`. |
| `name` | `VARCHAR` | Parsed skill name used as part of the grouping key. |
| `normalized_description` | `VARCHAR` | Description after trimming, lowercasing, and collapsing repeated whitespace. Used with `name` as the grouping key. |
| `artifact_group_size` | `BIGINT` | Number of filtered artifact occurrences sharing the same `name` and `normalized_description`. |
| `sibling_file_count` | `BIGINT` | Number of sibling file entries when composition can be characterized reliably. `0` means composition was checked and no sibling files exist; `NULL` means sibling composition is unavailable or incomplete. |
| `sibling_content_sha` | `VARCHAR` | SHA-256 fingerprint of the sorted multiset of sibling file `entry_sha` values. Paths and directories are excluded. `NULL` means a reliable fingerprint could not be produced; zero sibling files use the SHA-256 of the empty string. |

### Sibling Fingerprint Rules

Sibling fields are populated only when `artifacts.composition_fetched = 1`, `artifacts.composition_truncated = 0`, and every sibling file has a non-null `entry_sha`.

The fingerprint intentionally ignores filenames, paths, and directory layout. It is used as a low-cost exact-content comparison before similarity and security-delta analysis.

A changed fingerprint shows that sibling file content differs; it does not by itself establish that the change is security-relevant.

---

## Indexes, Constraints, and Query Optimization

### Declared DuckDB Constraints

The project build scripts currently define:

- no declared primary keys;
- no declared foreign keys;
- no `UNIQUE` constraints;
- no `NOT NULL` constraints;
- no secondary indexes.

The project-generated surrogate identifiers are therefore used by convention rather than enforced as keys by DuckDB.

### Project and Source Identifiers

| Table | Project identifier / relationship | Retained source identifier / relationship |
|---|---|---|
| `repos` | `id` | `full_name` |
| `artifacts` | `id`; `repo_id` → `repos.id` | `(repo_full_name, path)` |
| `artifact_siblings` | `id`; `artifact_id` → `artifacts.id` | Parent `(repo_full_name, artifact_path)` plus `entry_name` |
| `artifact_groupings` | `id` = `artifacts.id`; `repo_id` = `artifacts.repo_id` | Derived table; no source counterpart |
| `mining_runs` | `run_id` | `run_id` |

The generated `id` values are local to a DuckDB build and should not be treated as stable identifiers across independent rebuilds.

### Useful Filtering Strategies

For large analyses:

- use `dedup_primary = 1` when the unit of analysis is **distinct skill content**;
- use all `artifacts` rows when studying **occurrences, copying, reuse, or repository distribution**;
- use `artifact_groupings` as the materialized RQ4 candidate-comparison population rather than rebuilding its filters in each query;
- check `content_fetched` before analyzing `content`;
- check `composition_fetched = 1` before interpreting composition fields;
- check `history_fetched = 1` before analyzing commit-history fields;
- exclude or separately handle `composition_truncated = 1` when complete folder composition is required;
- join `repos` only when repository-level variables such as language, stars, fork status, license, or repository age are needed.

---

## Data-Quality and Interpretation Notes

| Topic | Guidance |
|---|---|
| Snapshot | GitSkills is a point-in-time snapshot collected in July 2026. |
| Local surrogate identifiers | `id`, `repo_id`, and `artifact_id` are project-generated for the local DuckDB database and are not source GitSkills identifiers. |
| Search coverage | GitHub code-search limitations mean the dataset is a **lower bound** on the public population. Search indexes default branches only, files under 384 KB, recently active repositories with fewer than 500,000 files, and forks only when more starred than their parent. |
| Not every match is a modern skill | Search is case-insensitive and retained filename variants such as lowercase `skill.md`, including files that predate the October 2025 Agent Skills format. Use `filename`, `location_class`, `frontmatter_valid`, and date fields to define a stricter analysis population when needed. |
| Exact reuse | Matching `file_sha` values mean byte-for-byte identical file contents, not merely similar text. |
| Representative is not provenance | `dedup_primary = 1` identifies the row chosen for enrichment; it does **not** identify the original author or source of copied content. |
| Historical scope | Commit history follows the file's current path. A renamed file can have earlier history that is not reflected in `first_commit_at` or `commit_count`. |
| History sampling | Commit history is not available for every artifact. Use `history_fetched` when defining the analysis population. |
| Representative enrichment | Folder composition and history describe only the chosen representative occurrence. Other copies of the same `file_sha` may differ in bundled files or history. |
| Missing composition | The paper reports missing folder listings for a small number of representatives; check `composition_fetched` before assuming an empty folder. |
| Derived sibling fingerprint | `artifact_groupings.sibling_content_sha` compares sibling file contents only; filenames, paths, and directory layout are intentionally excluded. |
| Content integrity | `content_sha_ok` records whether fetched content reproduced the expected Git blob hash and identifies content repaired through the blob API. |
| Symlinks | Some discovered skills are symlinks; their `content` can be the link target path rather than skill instructions. |
| Missing values | Empty values should not automatically be interpreted as a negative condition. Check the relevant fetch/status field first. |
| Repository metrics | `stars`, `forks`, and `pushed_at` are snapshots from collection time, not live GitHub values. |
| Licensing | Dataset metadata/aggregation is released under CC BY 4.0, but reproduced skill and sibling content remains subject to the originating repository's license. |

---

## Examples of Common Analysis Units

| Research unit | Recommended selection |
|---|---|
| Every discovered file occurrence | All rows from `artifacts` |
| Distinct byte-identical contents | `artifacts WHERE dedup_primary = 1` |
| Verbatim reuse count | `GROUP BY file_sha` over all `artifacts` rows |
| Repository-level adoption | Join `artifacts` to `repos`, then aggregate by `repos.full_name` |
| Bundled scripts/references/resources | Representative `artifacts` rows with `composition_fetched = 1`, joined to `artifact_siblings` |
| Commit-history analysis | Rows with `history_fetched = 1` |
| Parsed front-matter analysis | Representative rows with fetched content; optionally restrict to `frontmatter_valid = 1` |
| RQ4 candidate comparisons | Rows from `artifact_groupings`, joined to `artifacts` by `id` for source content, hashes, and chronology |
| Current-spec-oriented population | Apply explicit filters for filename/path/front matter rather than assuming every discovered row is specification-compliant |

---

## Sources

The field definitions and interpretation notes in this dictionary are based on:

- **GitSkills dataset card (Hugging Face):** https://huggingface.co/datasets/mvaccargiu/gitskills
- **GitSkills paper:** https://arxiv.org/abs/2608.10906
- **GitSkills sample/schema documentation:** https://github.com/giuseppedestefanis/gitskills-sample
- **Agent Skills overview:** https://agentskills.io/home
- **Agent Skills specification:** https://agentskills.io/specification
- **MSR 2027 Mining Challenge:** https://2027.msrconf.org/track/msr-2027-mining-challenge
- **Dataset archive:** https://doi.org/10.5281/zenodo.21875637

The project's DuckDB build and analysis SQL define the **physical schema used by this project**, including local surrogate identifiers and derived tables. External documentation is used to explain source-field semantics, collection behavior, and Agent Skills concepts. Where a numeric status value is not explicitly defined by the public documentation, this dictionary avoids assigning a meaning that cannot be verified.
