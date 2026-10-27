# Sprint 2 Manual Validation Protocol

## Purpose and scope

This protocol defines a repeatable, pair-level manual review of the two key parts
of the analysis:

1. whether candidate skill artifacts are sufficiently related to compare; and
2. whether the family analysis, security scanner, and change classification
   correctly report security-sensitive behavior and changes.

This is a purposeful method-validation sample, not a random or population-
representative sample. It contains 13 fixed comparison cases drawn from the
43-artifact Sprint 1 sample in `sample_artifacts`. The review itself is a
separate activity: reviewer and adjudication columns in
[`validation_sample.csv`](../../data/validation/validation_sample.csv) were
initially blank. See the review status below for the current completion state.

The sample was prepared against GitSkills dataset release
[21875637](https://zenodo.org/records/21875637), the default analysis policy
(shingle size 5, minimum containment 0.80, minimum Jaccard 0.30, minimum 5
shared shingles, direction margin 0.10), and project revision
`1f59206526de4d0502bc972f19cd22464c554fe2`. Artifact IDs, file hashes, source
repositories, and paths are included so every item can be traced to the local
dataset.

## Selection procedure

Use the frozen `sample_artifacts` view created by
[`sql/create_sprint1_samples_view.sql`](../../sql/create_sprint1_samples_view.sql).
For each exact-name family in that view, run `analyze_family` and `scan_family`
with their default policy. Selection is purposeful and follows these fixed
rules:

1. **Positive (5 cases):** for each of the first five family names, in
   alphabetical order, that has a flagged directed edge, select its first
   flagged edge ordered by source artifact ID and then destination artifact ID.
2. **Negative (4 cases):** select the first unflagged directed edge, ordered by
   source and destination artifact ID, from each of the first three families
   that has one. Also include the `A/B Test Setup` pair (1244165, 2690162),
   which has no related edge in the automated analysis.
3. **Ambiguous (4 cases):** select the first `similarity-only` ambiguous edge,
   ordered by artifact IDs, from each of the first three qualifying family
   names. Also select the first `equivalent-state` edge, ordered by family name
   and artifact IDs.

Each selected result is frozen in the CSV. If a future dataset or code revision
changes the output, retain the original rows, document the new revision and
differences, and create a separately versioned sample rather than silently
replacing this one. The fixed sample does not support population prevalence,
recall, or risk estimates.

## Reproducing and locating the automated results

Set `GITSKILLS_DB` to the local DuckDB database as described in
[`data/README.md`](../../data/README.md), then create the analysis tables,
groupings, and Sprint 1 sample view if needed. To reproduce the selection from
scratch, run both tools for all ten family names in `sample_artifacts`. To
recheck a particular case, run them for that case's `skill_name`. In PowerShell:

```powershell
$env:GITSKILLS_DB = "C:\path\to\agent_skills_release.db"
uv run analyze_family "003-create-golang-project" --json
uv run scan_family "003-create-golang-project" --json
```

In Bash or WSL, set the variable with `export GITSKILLS_DB=/path/to/agent_skills_release.db`
and run the same two `uv run` commands. The tools read `GITSKILLS_DB` by
default; `--db <path>` can be used instead when preferred.

For convenience, the corresponding Unix-style example is:

```bash
export GITSKILLS_DB=/path/to/agent_skills_release.db
uv run analyze_family "003-create-golang-project" --json
uv run scan_family "003-create-golang-project" --json
```

The CSV's `automated_*` columns record the output used to select each case.
Directed cases keep the source artifact in column A and destination in column
B. For ambiguous and no-edge cases, A and B are ordered by artifact ID; that
order does not imply chronology or direction. Read
`automated_scan_coverage` before interpreting a missing finding: it distinguishes
a complete skill scan, a skipped sibling scan, incomplete sibling data, and a
pair that was not scanned.

`automated_security_findings` uses
`RULE_ID:surface:source_count->destination_count`, with multiple rules separated
by semicolons. `none` means the automated scan emitted no flagged rule for that
pair and scope; it is not human ground truth. `automated_relationship` records
whether the method emitted a directed related edge, an ambiguous edge, an
equivalent-state edge, or no related edge.

Use each artifact ID to retrieve `content`, `repo_name`, `path`, timestamps, and
sibling records from the local database. Review the source artifact and relevant
sibling files locally; do not copy dataset source text, scanner excerpts, or
credentials into this CSV, the repository, or shared review notes. Dataset
content remains subject to its original repository license. If an artifact or
required sibling content is unavailable, record `uncertain` rather than
interpreting missing content as absence of a signal.

## Review instructions

Each reviewer works independently and fills only their own columns before
discussion. Do not change the case IDs, artifact metadata, or `automated_*`
columns.

For each case:

1. **Check identity and availability.** Confirm both artifact IDs, repository
   paths, and file hashes against the local dataset. Read both `SKILL.md`
   contents and the relevant sibling files. Note missing or inaccessible
   content.
2. **Judge relatedness.** Use the whole artifact, not the shared name or
   similarity score alone. Decide whether the artifacts plausibly represent
   comparable skill behavior. Record `related`, `not_related`, or `uncertain`.
3. **Review the reported scanner output.** For each rule in
   `automated_security_findings`, compare the matched behavior with the rule's
   description and the artifact context. Decide whether it is a genuine
   security-sensitive behavior or a contextual match such as quoted example
   text. For cases with no reported findings, look for relevant behavior the
   active scanner rules should have detected. Judge only surfaces included in
   `automated_scan_coverage`; do not treat an unscanned or unavailable sibling
   as a negative result.
4. **Judge change and direction.** For comparable artifacts, check the
   `automated_direction_basis` and its supporting timestamps, provenance, or
   containment evidence. Do not infer direction from repository age or artifact
   ID. Record whether the behavior was introduced, removed, retained, or whether
   direction is unknown. If relationship or ordering cannot be established,
   retain that uncertainty.
5. **Record the result.** Use the controlled labels below. Use the per-rule
   field to distinguish mixed outcomes, for example
   `FS-001=correct;NET-001=false_positive`. Add a concise explanation in the
   notes field for uncertain, partial, or non-obvious judgments.

### Controlled labels

| Field | Allowed values | Meaning |
| --- | --- | --- |
| `reviewer_N_relatedness` | `related`, `not_related`, `uncertain` | Human judgment about whether the artifacts can be meaningfully compared. |
| `reviewer_N_security_signal` | `present`, `absent`, `uncertain`, `not_applicable` | Whether a relevant security-sensitive behavior is present in the reviewed scope of the pair. Use `not_applicable` when no meaningful comparison or scan is available. |
| `reviewer_N_scanner_correctness` | `correct`, `partially_correct`, `incorrect`, `uncertain`, `not_applicable` | Pair-level correctness of the automated security result. Use per-rule judgments for mixed results. |
| `reviewer_N_change_direction` | `introduced`, `removed`, `retained`, `direction_unknown`, `not_applicable` | Human judgment about the behavior's change between source and destination. |
| `reviewer_N_rule_judgments` | `RULE_ID=correct`, `RULE_ID=false_positive`, `RULE_ID=false_negative`, `RULE_ID=uncertain`, or `RULE_ID=not_applicable`; multiple entries separated by `;` | Per-rule assessment. A false positive is a reported rule without the corresponding behavior; a false negative is relevant behavior in the reviewed scan scope that the automated result missed. |

Use `not_applicable` rather than `correct` or `incorrect` when a pair is not
related, has only an unresolved relationship, or was not scanned. Use
`uncertain` when evidence is incomplete or the reviewer cannot make a reliable
judgment. Do not force uncertain items into a binary result.

## Disagreements and uncertain cases

Keep both reviewers' original fields unchanged. After independent review, compare
judgments and fill `adjudication_status` with `agreed`, `resolved_after_discussion`,
or `unresolved`. Record the final judgment and a short rationale in
`adjudication_notes`; do not overwrite either reviewer's values. An unresolved
case remains uncertain and is reported as such. Preserve disagreements as
validation evidence, especially when they arise from ambiguous similarity,
direction, rule context, or incomplete data.

## Review status

On 2026-10-20, `Copilot (AI-assisted)` filled only the `reviewer_1` fields for
all 13 cases using the local SkillTrace content, comparison, metadata, sibling,
and pair-scan APIs at project revision
`04efa93ffe87d7f62f6a361cf7f49e39237ce11a`. Artifact identities and timestamps
were checked against the frozen CSV. Local read-only sibling metadata also
confirmed the four unavailable source files in P04, which SkillTrace's
content-bearing sibling list does not display. Frozen automated fields were
preserved; dataset contents were inspected statically and never executed.

These entries are one explicitly identified AI-assisted review, not two
independent human reviews or completed manual validation. `reviewer_2` and
adjudication fields remain blank pending independent review and discussion.
The notes distinguish positive match-count deltas from newly introduced
capabilities, preserve uncertainty about containment-only direction and missing
siblings, and do not treat unscanned pairs as negative security results.

## Sample interpretation

The positive, negative, and ambiguous labels describe the automated output used
to select a case; they are not human ground truth. Positive cases have at least
one automated flagged rule. Negative cases include directed pairs with no
flagged rule and a same-name pair for which the method emitted no related edge.
Ambiguous cases include unresolved similarity-only relationships and an
equivalent-state pair without a direction. Manual reviewers can confirm,
contradict, or leave each automated result uncertain.

This protocol defines the review process and frozen sample only. Record actual
review results separately from automated outputs and do not describe this sample
as a completed validation until reviewers have filled and adjudicated its rows.
