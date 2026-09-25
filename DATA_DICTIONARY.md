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

> **Project schema:** The source tables are represented in a local DuckDB database with added project identifiers and the derived `artifact_groupings` table.

## Schema at a Glance

| Table | Purpose | Identifier used in the project |
|---|---|---|
| [`artifacts`](#artifacts) | Records each discovered skill-file occurrence and enrichment data for representative contents. | `id` |
| [`artifact_siblings`](#artifact_siblings) | Records files and directories located alongside a representative skill. | `id` |
| [`repos`](#repos) | Stores metadata for repositories containing discovered skills. | `id` |
| [`mining_runs`](#mining_runs) | Records collection-run provenance. | `run_id` |
| [`artifact_groupings`](#artifact_groupings) | Stores the filtered RQ4 comparison population and derived sibling fingerprints. | `id` (artifact-group identifier); `artifact_id` → `artifacts.id` |

The `id` columns on `repos`, `artifacts`, and `artifact_siblings` are project-generated surrogate row identifiers. `artifact_groupings.id` is also project-generated, but identifies a `name` + normalized-description group and can therefore repeat across member rows. These identifiers are not fields from the GitSkills release and should be treated as local to the current DuckDB build. The original source identifiers and join fields are retained.


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
   | \ 0-or-1 through artifact_groupings.artifact_id
   |  v
   | artifact_groupings
   |   id = artifact-group identifier
   |
   | 1-to-many through artifact_siblings.artifact_id
   v
artifact_siblings

artifact_groupings.repo_id
   |
   | many-to-one
   v
repos.id

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
| `artifact_groupings` | `repos` | `artifact_groupings.repo_id = repos.id` | Adds repository metadata directly to an RQ4 grouping member. |
| `artifact_siblings` | `artifacts` | `artifact_siblings.artifact_id = artifacts.id` | Associates bundled files/directories with the parent skill occurrence. |
| `artifact_groupings` | `artifacts` | `artifact_groupings.artifact_id = artifacts.id` | Joins an RQ4 grouping member back to the full artifact record. |
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

Under the Agent Skills specification, `description` is important metadata because it describes what the skill does and when it should be used.

## Common Conventions

| Convention | Meaning |
|---|---|
| `VARCHAR` | UTF-8 text. Timestamp values are stored as ISO-8601 UTC strings rather than DuckDB timestamp types. |
| Integer status fields | Many bookkeeping fields use integer values. Most behave like `0`/`1` flags, but `*_fetched` fields should be treated as status values unless their Boolean meaning is explicitly documented. |
| Empty / `NULL` enrichment fields | Usually mean the enrichment step was not performed, did not return data, or was not applicable. Check the corresponding status field before interpreting missing values. |
| `file_sha` / `entry_sha` | Git object hashes used to identify exact contents or repository entries. |
| Local identifiers and relationships | `id`, `repo_id`, and `artifact_id` are added by the project when building DuckDB. In `artifact_groupings`, `id` identifies a derived group while `artifact_id` identifies the member artifact. These are not source GitSkills fields. |
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

`dedup_primary = 1` identifies the representative occurrence for a distinct `file_sha`; all occurrences remain in `artifacts`.

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

**Purpose:** Project-derived RQ4 table containing qualifying artifact members, description-based groups within each skill name, and derived sibling-content fingerprints.

**Artifact-group identifier:** `id`

**Artifact relationship:** `artifact_id` → `artifacts.id`

**Repository relationship:** `repo_id` → `repos.id`

Each row corresponds to one qualifying artifact member. A skill `name` is retained only when at least two qualifying artifacts share that exact name. Within an eligible name, each distinct `name` + `normalized_description` combination forms an artifact group. A description-specific group can therefore have `artifact_group_size = 1` as long as the same skill name occurs in at least one other qualifying artifact.

Rows qualify when `frontmatter_valid = 1`, `body_chars > 50`, and `content`, `name`, and `description` are non-null. No restriction is applied to `location_class`, `first_commit_at`, `dedup_primary`, or `filename`.

`first_commit_at` may be `NULL`, so chronological information is not available for every grouping member.

| Column | DuckDB type | Description |
|---|---|---|
| `id` | `BIGINT` | Project-generated artifact-group identifier for an exact `name` + `normalized_description` combination. The same value can appear on multiple member rows. |
| `artifact_id` | `BIGINT` | Project-generated relationship to `artifacts.id`. Identifies the individual artifact represented by the row. |
| `repo_id` | `BIGINT` | Repository identifier copied from `artifacts.repo_id`; joins to `repos.id`. |
| `name` | `VARCHAR` | Parsed skill name. A name must occur in at least two qualifying artifacts to enter this table. |
| `normalized_description` | `VARCHAR` | Description after trimming, lowercasing, and collapsing repeated whitespace. Used with `name` to define the artifact group. |
| `artifact_group_size` | `BIGINT` | Number of qualifying artifact occurrences sharing the same exact `name` and `normalized_description`. This can be `1` when the name has other artifacts with different descriptions. |
| `sibling_file_count` | `BIGINT` | Number of sibling file entries when composition can be characterized reliably. `0` means composition was checked and no sibling files exist; `NULL` means sibling composition is unavailable or incomplete. |
| `sibling_content_sha` | `VARCHAR` | SHA-256 fingerprint of the sorted multiset of sibling file `entry_sha` values. Paths and directories are excluded. `NULL` means a reliable fingerprint could not be produced; zero sibling files use the SHA-256 of the empty string. |

### Sibling Fingerprint Rules

Sibling fields are populated only when `artifacts.composition_fetched = 1`, `artifacts.composition_truncated = 0`, and every sibling file has a non-null `entry_sha`.

The fingerprint intentionally ignores filenames, paths, and directory layout, so it reflects sibling file content rather than repository organization.

A changed fingerprint indicates that sibling file content differs; it does not identify which file changed or the meaning of the change.

---

## Keys and Constraints

The DuckDB schema does not enforce primary keys, foreign keys, `UNIQUE`, or `NOT NULL` constraints. The identifiers and relationships below are therefore logical schema relationships.

| Table | Project identifier / relationship | Retained source identifier / relationship |
|---|---|---|
| `repos` | `id` | `full_name` |
| `artifacts` | `id`; `repo_id` → `repos.id` | `(repo_full_name, path)` |
| `artifact_siblings` | `id`; `artifact_id` → `artifacts.id` | Parent `(repo_full_name, artifact_path)` plus `entry_name` |
| `artifact_groupings` | `id` = artifact-group identifier; `artifact_id` → `artifacts.id`; `repo_id` → `repos.id` | Derived table; no source counterpart |
| `mining_runs` | `run_id` | `run_id` |

Project-generated identifiers are local to a DuckDB build. In `artifact_groupings`, `id` identifies a group and can repeat across member rows; `artifact_id` identifies the member artifact.

---

## Data-Quality and Interpretation Notes

| Topic | Guidance |
|---|---|
| Snapshot | GitSkills is a point-in-time snapshot collected in July 2026. |
| Local identifiers | `id`, `repo_id`, and `artifact_id` are project-generated for the local DuckDB database and are not source GitSkills identifiers. `artifact_groupings.id` is a group identifier and can repeat across member rows. |
| Search coverage | GitHub code-search limitations mean the dataset is a **lower bound** on the public population. Search indexes default branches only, files under 384 KB, recently active repositories with fewer than 500,000 files, and forks only when more starred than their parent. |
| Not every match is a modern skill | Search is case-insensitive and retained filename variants such as lowercase `skill.md`, including files that predate the October 2025 Agent Skills format. Use `filename`, `location_class`, `frontmatter_valid`, and date fields to define a stricter analysis population when needed. |
| Exact reuse | Matching `file_sha` values mean byte-for-byte identical file contents, not merely similar text. |
| Representative is not provenance | `dedup_primary = 1` identifies the row chosen for enrichment; it does **not** identify the original author or source of copied content. |
| Historical scope | Commit history follows the file's current path. A renamed file can have earlier history that is not reflected in `first_commit_at` or `commit_count`. |
| History sampling | Commit history is not available for every artifact. `history_fetched` indicates whether history enrichment was collected, and history fields may be empty when it was not. |
| Representative enrichment | Folder composition and history describe only the chosen representative occurrence. Other copies of the same `file_sha` may differ in bundled files or history. |
| Missing composition | Folder composition is unavailable for some representatives. `composition_fetched` distinguishes unavailable composition from a known empty folder. |
| Derived sibling fingerprint | `artifact_groupings.sibling_content_sha` compares sibling file contents only; filenames, paths, and directory layout are intentionally excluded. |
| Content integrity | `content_sha_ok` records whether fetched content reproduced the expected Git blob hash and identifies content repaired through the blob API. |
| Symlinks | Some discovered skills are symlinks; their `content` can be the link target path rather than skill instructions. |
| Missing values | Empty values can mean enrichment was unavailable, not performed, or not applicable; related fetch/status fields provide the necessary context. |
| Repository metrics | `stars`, `forks`, and `pushed_at` are snapshots from collection time, not live GitHub values. |
| Licensing | Dataset metadata/aggregation is released under CC BY 4.0, but reproduced skill and sibling content remains subject to the originating repository's license. |

---

## Common Units of Analysis

| Research unit | Recommended selection |
|---|---|
| Every discovered file occurrence | All rows from `artifacts` |
| Distinct byte-identical contents | `artifacts WHERE dedup_primary = 1` |
| Verbatim reuse count | `GROUP BY file_sha` over all `artifacts` rows |
| Repository-level adoption | Join `artifacts` to `repos`, then aggregate by `repos.full_name` |
| Bundled scripts/references/resources | Representative `artifacts` rows with `composition_fetched = 1`, joined to `artifact_siblings` |
| Commit-history analysis | Rows with `history_fetched = 1` |
| Parsed front-matter analysis | Representative rows with fetched content; optionally restrict to `frontmatter_valid = 1` |
| RQ4 candidate comparisons | Rows from `artifact_groupings`, joined to `artifacts` by `artifact_id` for source content, hashes, and chronology |
| Current-spec-oriented population | Apply explicit front-matter and other specification-oriented filters rather than assuming every discovered row is specification-compliant; `location_class` is a path classification, not a validity flag |

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

The project's DuckDB schema defines the physical columns, local identifiers, and derived tables documented here. External sources provide the semantics of source fields, collection behavior, and Agent Skills concepts. Where a numeric status value is not explicitly defined by the public documentation, this dictionary does not assign an unsupported meaning.
