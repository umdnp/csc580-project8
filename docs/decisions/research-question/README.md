# GitSkills Genealogy / Similarity Exploration

This folder documents a set of exploratory Python scripts used to evaluate whether the
`agent_skills_release.db` dataset could support version, reuse, or inferred-lineage analysis
for GitSkills artifacts.

The work was exploratory. The primary project direction is expected to remain **static
analysis of current skill content**, while these scripts document the feasibility tests that
were performed around genealogy and reuse.

## Dataset

All scripts use:

```text
agent_skills_release.db
```

The full release contains roughly 3.8 million artifact rows.

---

## 1. `genealogy_analysis.py`

### Purpose

Tests whether the dataset contains enough historical or provenance information to reconstruct
artifact history directly.

The script examines:

- total artifact count
- history coverage
- artifacts with multiple commits
- duplicate repository/path rows
- exact-content reuse across repositories using SHA values
- `dedup_primary` distribution
- repository fork metadata
- content/history coverage

### Output

```text
genealogy_analysis.md
```

### Key Findings

The full-dataset run found:

- 3,797,117 total artifacts
- 458,548 artifacts with fetched history metadata
- 154,339 artifacts with more than one commit
- 0 duplicate repository/path groups
- 306,088 SHA groups appearing in multiple repositories
- 1,880,329 artifacts with stored content
- 282,200 repositories, but only 3 marked as forks

### Interpretation

The database appears to contain one current artifact state per repository/path, plus summary
history metadata for a subset of artifacts. It does **not** appear to contain historical
versions of `SKILL.md` content that can be directly diffed.

Exact SHA reuse across repositories is common and is useful for studying reuse, but it does
not establish direction of copying or provenance.

---

## 2. `same_name_different_sha.py`

### Purpose

Tests whether artifacts sharing the same declared skill name also appear with different SHA
values across repositories.

The script groups artifacts by normalized `artifacts.name` and reports:

- artifact count
- distinct SHA count
- repository count
- content availability
- earliest and latest known commit dates
- detailed artifact records for top candidate groups

### Output

```text
same_name_different_sha.md
```

### Key Findings

The full-dataset run found:

- 1,635,568 artifacts with a skill name
- 845,421 distinct normalized skill names
- 162,855 names associated with multiple SHA values

Large groups included names such as:

- `code-review`
- `skill-creator`
- `systematic-debugging`
- `writing-plans`
- `verification-before-completion`
- `using-git-worktrees`

### Interpretation

Same-name/different-SHA groups are common, but name equality alone is not sufficient evidence
of lineage. Generic names can collide across unrelated skills.

Distinctive names are more useful as **candidate family identifiers** and can be followed by
content-similarity testing.

---

## 3. `skill_name_validation.py`

### Purpose

Validates that the database field `artifacts.name` corresponds to the declared `name:` value
inside each stored `SKILL.md` frontmatter.

The script:

1. randomly samples 500 artifacts with both `name` and `content`
2. parses the YAML-style frontmatter from stored `SKILL.md` content
3. extracts the `name:` value
4. compares it with `artifacts.name`
5. reports matches, mismatches, and missing frontmatter names

### Output

```text
skill_name_validation.md
```

### Key Finding

The random sample produced a **100% match rate across all 500 sampled artifacts**.

### Interpretation

This provides strong practical validation that `artifacts.name` can be used as the grouping
key for declared skill identity in subsequent analysis.

---

## 4. `skill_similarity_pilot.py`

### Purpose

Tests whether same-name artifacts with different SHA values also contain highly similar text.

The pilot targets a small set of distinctive skill names rather than performing all-pairs
comparison across the full dataset.

Initial target names included:

- `writing-plans`
- `systematic-debugging`
- `verification-before-completion`
- `subagent-driven-development`
- `using-git-worktrees`
- `dispatching-parallel-agents`

### Comparison Strategy

For each skill family, the script:

1. loads all artifacts with matching `artifacts.name`
2. normalizes stored content
3. compares each artifact with several of the earliest artifacts
4. compares chronologically adjacent artifacts
5. calculates text similarity using Python `difflib.SequenceMatcher`
6. reports matches above configured thresholds

The pilot uses the following exploratory thresholds:

```text
>= 75%  Possible relationship
>= 90%  Strong candidate relationship
>= 95%  Very strong candidate relationship
```

These thresholds are exploratory and do not independently prove genealogy.

### Output

```text
skill_similarity_pilot.md
```

### Final Results

The completed pilot analyzed six distinctive skill-name families:

| Skill family | Artifacts | Comparisons | >=75% | >=90% | >=95% |
|---|---:|---:|---:|---:|---:|
| `writing-plans` | 1,065 | 6,367 | 542 | 111 | 44 |
| `systematic-debugging` | 1,309 | 7,833 | 1,113 | 892 | 577 |
| `verification-before-completion` | 613 | 3,656 | 380 | 225 | 154 |
| `subagent-driven-development` | 802 | 4,791 | 524 | 247 | 91 |
| `using-git-worktrees` | 577 | 3,441 | 1,093 | 805 | 381 |
| `dispatching-parallel-agents` | 512 | 3,049 | 1,389 | 1,027 | 475 |
| **Total** | **4,878** | **29,137** | **5,041** | **3,307** | **1,722** |

Every family produced at least one 100% similarity result despite the compared artifacts having
different SHA values.

Across all 29,137 comparisons:

- 5,041 comparisons (about 17.3%) were >=75% similar
- 3,307 comparisons (about 11.4%) were >=90% similar
- 1,722 comparisons (about 5.9%) were >=95% similar

These results demonstrate that substantial near-duplicate content exists among artifacts
sharing the same declared skill name.

### Interpretation

High similarity plus the same declared skill name and chronological metadata can identify
**candidate inferred relationships**, but it still does not prove parent/child ancestry.

The `SequenceMatcher` approach is computationally expensive at scale. The pilot demonstrated
feasibility for small families but also showed that full genealogy reconstruction would be
costly on the available hardware.

A more scalable future approach could use a faster first-stage similarity method such as
Jaccard similarity on token or shingle sets, followed by detailed diffing only for likely
matches.

---

## Overall Conclusion

The exploratory scripts established several useful facts:

1. The dataset does not directly provide historical artifact contents for version-by-version
   diffing.
2. Exact-content reuse across repositories is widespread.
3. Same declared skill names frequently appear with different SHA values.
4. The database `name` field accurately matched stored `SKILL.md` frontmatter in a 500-record
   random validation sample.
5. Some same-name/different-SHA artifacts are highly similar and may represent copied,
   modified, or commonly derived skills.
6. Large-scale lineage reconstruction would require significantly more compute and a more
   scalable similarity pipeline.

Because of these findings, genealogy analysis is best treated as an exploratory or secondary
research direction. Static analysis of current skill content remains the more achievable and
defensible primary direction for the semester project.

---

## Runtime Notes

The scripts were run against the full `agent_skills_release.db` dataset on a local VM.

Observed approximate runtimes:

```text
genealogy_analysis.py         ~20 minutes
same_name_different_sha.py    ~60 minutes
skill_name_validation.py      short / negligible
skill_similarity_pilot.py     ~17 hours
```

The similarity pilot was created and started at approximately **14:43 on 2026-09-16** and
completed at approximately **07:36 on 2026-07-17**, giving an estimated elapsed runtime of roughly
**17 hours**.

The pilot processed:

```text
4,878 artifacts
29,137 similarity comparisons
```

This corresponds to an overall average of roughly 100 comparisons per minute, although
individual comparisons varied substantially in cost depending on document length and content.

The pilot used Python `difflib.SequenceMatcher`. Character counts shown in the Markdown output
were descriptive metadata used to show document-size differences; the similarity score itself
was **not calculated from character-count difference**. `SequenceMatcher` compared the ordered
character sequences of the normalized document contents.

The pilot demonstrated that inferred reuse/evolution is technically plausible, but the runtime
also showed that the current approach would not scale efficiently to large-scale genealogy
reconstruction. Future work could use a faster candidate-filtering technique such as Jaccard
similarity over token shingles, MinHash, or another near-duplicate method before applying an
expensive detailed diff.

Because complete historical artifact states and explicit parent/child provenance are not
available in the dataset, and because inferred genealogy would add significant computational
and methodological complexity, the project is expected to prioritize **static analysis of
current skill content**. The genealogy work remains documented as a feasibility study and
possible future extension.
