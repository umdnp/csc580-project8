# [Project-8] CSC 580 Group Assignment 2_ Requirements Engineering - Gemini Notebook

Exported on: 9/21/2026, 2:58:32 PM

---

### User

Would it make sense to exclude any data that has no frontmatter or is an exact match from my study? that might drastically reduce my dataset size.

---

### Model

**Yes, filtering out files without frontmatter and deduplicating exact matches makes complete sense.** In fact, this is the standard filtering methodology recommended by the dataset creators and dataset documentation \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

Here is how each filter impacts your study, dataset size, and compute performance:

* * *

1\. Excluding Data Without Valid Frontmatter (`frontmatter_valid = 0`)

-   **Why it makes sense**: The official Agent Skills specification requires YAML frontmatter containing `name` and `description` \[Source: 4: Specification - Agent Skills\] . In GitSkills, **86.6% of distinct contents (1.62M files)** carry valid frontmatter, while the remaining 13.4% are malformed, unparsed, or legacy files (such as generic Markdown files named `skill.md` created prior to the October 2025 specification) \[Source: 7: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Impact on your study**: Filtering for `frontmatter_valid = 1` eliminates non-compliant noise and ensures your static analyzer only evaluates actual, structured agent skills \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

2\. Handling Exact Matches (`file_sha` and `dedup_primary = 1`)

-   **Why deduplicating makes sense**: Over **50.5% of all file occurrences** in GitSkills are exact, byte-for-byte copies \[Source: 7: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] . Running static security rules over millions of identical files would waste significant time and compute.-   **How to implement this**: Filter your static scanning population to **dedup\_primary = 1** \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 11: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . This selects exactly one representative skill file per unique Git content hash (`file_sha`), instantly cutting your scanning workload in half (from 3.8 million total occurrences down to 1.88 million unique files in the full dataset, or down to 13,000 unique files in the sample database) \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Important nuance for RQ4**: While you exclude verbatim duplicates from *scanner execution*, you keep their row entries in the database to calculate copy counts (`COUNT(*) GROUP BY file_sha`) \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . This allows you to evaluate whether a risky skill variant was mass-copied across hundreds of repositories or isolated to a single project \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

3\. Recommended SQL Filter Baseline

To create a clean, lightweight analysis population, your data loading pipeline can run:

```
SELECT repo_full_name, path, file_sha, name, description, content
FROM artifacts
WHERE dedup_primary = 1 
  AND frontmatter_valid = 1
  AND content IS NOT NULL;
```

This query isolates distinct, valid skill instructions, providing a defensible dataset that runs efficiently on a personal laptop \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

4\. How to Document This in Course Deliverables

-   **Requirements & Data Filtering (****RESEARCH\_SPEC.md** **/ Phase C & E)**: Record `dedup_primary = 1` and `frontmatter_valid = 1` under your explicit inclusion/exclusion criteria \[Source: 14: Requirements Engineering V2.pdf\] .-   **Threats to Validity (****THREATS\_TO\_VALIDITY.md****)**: Note that excluding non-frontmatter files omits malformed or legacy skills, limiting findings strictly to specification-compliant skills \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

💡 Would you like an example DuckDB / Pandas script to extract this filtered population from the sample database?

---

### User

Is there anything else I should filter out? Some content seems to be in foreign languages. Could that cause problems when scanning?

---

### Model

How Foreign Languages Affect Static Scanning

For **Research Question 4** (static analysis of executable commands, URLs, file operations, and credentials) \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] , foreign language text in `SKILL.md` files **will generally not cause significant issues for your scanner**:

-   **Command & URL Syntax is Universal**: Executable CLI commands (`curl`, `wget`, `sudo`, `rm`, `python`, `pip`), shell flags, file paths (`/etc/passwd`, `~/.ssh`), and URLs (`https://...`) follow standardized code syntax regardless of whether the surrounding natural-language instructions are in English, Chinese, or Spanish \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] . A rule-based regex scanner targeting executable patterns will catch these commands anywhere in the text \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **Where Foreign Languages Might Cause Noise**: Foreign language text only becomes an issue if your rules rely on natural-language English keywords (e.g., searching for phrased instructions like *"enter your API key here"* or *"send credentials to"*).-   **Should You Filter by Language?**: You do not strictly need to filter them out. However, if you prefer an English-only cohort, you can either filter using repository metadata (`repos.language`) \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] or apply a lightweight Python language-detection library (like `langdetect`) on `artifacts.content`. If you do exclude non-English skills, document this under your inclusion/exclusion criteria in `RESEARCH_SPEC.md` and address it in `THREATS_TO_VALIDITY.md` \[Source: 6: Requirements Engineering V2.pdf\] .

* * *

Additional Recommended Filters for Your Security Pipeline

Beyond excluding malformed frontmatter (`frontmatter_valid = 0`) and scanning only primary deduplicated representatives (`dedup_primary = 1`), consider filtering out these specific noise sources:

-   **Symlinks (****body\_chars** **Threshold)**
    -   **The Issue**: A small subset of discovered skills are symbolic links where `artifacts.content` contains only a target relative file path (e.g., `../../other/path/SKILL.md`) rather than actual instructions \[Source: 7: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Filter**: Exclude rows with extremely short body lengths (e.g., `body_chars < 50` or `body_chars IS NULL`) \[Source: 9: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Non-Standard Location Classes (****location\_class = 'other'****)**
    -   **The Issue**: 34.8% of files in GitSkills live in arbitrary repository paths (`location_class = 'other'`), which include legacy or accidental markdown files matching the search term \[Source: 10: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .-   **Filter**: Restrict your primary dataset to canonical or skills-directory paths (`location_class IN ('canonical', 'skills-dir')`) to focus strictly on intended agent skill folders \[Source: 11: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Non-Standard Basenames (****filename****)**
    -   **The Issue**: The collection search matched files containing the string `SKILL.md` (such as `coding-skill.md` or legacy lowercase files that predate the October 2025 specification) \[Source: 12: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 13: mvaccargiu/gitskills · Datasets at Hugging Face\] .-   **Filter**: Filter for standard basenames (e.g., `filename IN ('SKILL.md', 'skill.md')`) \[Source: 9: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 12: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Skipped or Binary Bundled Files (****artifact\_siblings****)**
    -   **The Issue**: When scanning bundled scripts or reference files in `artifact_siblings`, binary files or files exceeding 100 KB have `content = NULL` and record a `skipped_reason` (e.g., `binary` or `oversize`) \[Source: 14: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 15: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Filter**: Ensure your sibling script scanner queries `WHERE content IS NOT NULL` to avoid processing empty rows \[Source: 15: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

Summary Filter Query Example

```
SELECT 
    a.repo_full_name, 
    a.path, 
    a.file_sha, 
    a.name, 
    a.content
FROM artifacts AS a
WHERE a.dedup_primary = 1
  AND a.frontmatter_valid = 1
  AND a.location_class IN ('canonical', 'skills-dir')
  AND a.filename IN ('SKILL.md', 'skill.md')
  AND a.body_chars > 50
  AND a.content IS NOT NULL;
```

* * *

💡 Would you like to outline the regular expression patterns for your rule-based scanner (e.g., regexes for network requests, credential leaks, and system commands)?

---

### User

repos.language is programming language not foreign language. I don't think that would help. The other filter criteria is a good idea. Now, assume we filter like so: select \* from artifacts as a where a.dedup\_primary = 1 and a.frontmatter\_valid = 1 and a.location\_class in ('canonical', 'skills-dir') and a.filename in ('SKILL.md', 'skill.md') and a.body\_chars > 50 and a.content is not null; Would it make sense to also group these artifacts by their name and path and order by first\_commit\_at? Then we could go through each group and check similarity and scan for risky behavior in the "copies"? Is it safe to assume though that the name alone is sufficient for assuming that later skills identified might be copies if the first one commited? Would we still need to do a similarity scan before trying to scan for risky behavior? I feel like a similarity scan would slow things down significantly.

---

### Model

**No, relying on** **name** **alone is not safe to assume two skills are copies**, but you can use `name` to make text similarity checks extremely fast and lightweight.

* * *

1\. Why `name` Alone Is Not Sufficient

While the Agent Skills specification requires a slugified `name` in the YAML frontmatter \[Source: 1: Specification - Agent Skills\] \[Source: 2: Specification - Agent Skills\] , matching on `name` alone creates false positives:

-   **Name Collisions on Common Terms**: Simple or generic names (e.g., `test`, `helper`, `demo`, `deploy`, `api-client`) are frequently chosen by completely unrelated developers building skills from scratch \[Source: 2: Specification - Agent Skills\] .-   **Independent Implementations**: Two developers might independently create a skill named `code-review` or `pdf-processing` with 0% textual overlap \[Source: 2: Specification - Agent Skills\] \[Source: 3: Specification - Agent Skills\] . Treating the newer one as a "modified copy" of the older one would invalidate your security diff.

* * *

2\. Why Grouping by Both `name` AND `path` May Be Too Restrictive

Grouping by `path` alongside `name` can miss valid cross-repository copies:

-   Repository A might store the skill at `.claude/skills/pdf-processing/SKILL.md` (`location_class = 'canonical'`) \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   Repository B might copy that same skill to `skills/pdf-processing/SKILL.md` (`location_class = 'skills-dir'`) \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

If you group by `(name, path)` together, these two occurrences will not end up in the same bucket, even though one is a direct derivative of the other. **Grouping by** **name** **alone is much better for finding candidates across repositories** \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 6: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] **.**

* * *

3\. How to Make Similarity Scanning Fast (The 2-Stage Bucketing Pattern)

A similarity scan does **not** have to slow down your pipeline if you use a two-stage approach rather than an all-pairs $O(N2)$ search:

-   **Stage 1 (Bucket by** **name****)**: Filter your population with your SQL query and group rows by `artifacts.name` \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 6: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] . This reduces comparison groups from hundreds of thousands of files down to tiny clusters of 2 to 20 files sharing the same name.-   **Stage 2 (Fast Intra-Bucket Similarity)**: Run a lightweight text similarity algorithm (such as Jaccard similarity on word n-grams or Python's `difflib.SequenceMatcher`) **only within each name bucket**. Because each group is tiny, calculating similarity across 5 files takes a fraction of a millisecond.-   **Stage 3 (Diff Security Rules)**: If the text similarity between an earlier skill and a later skill exceeds your threshold (e.g., $≥60%$ or $70%$), mark the later skill as a "modified variant." Then, compare their static security scan results to flag added commands, URLs, or file operations \[Source: 7: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

4\. Establishing Timeline with `first_commit_at`

Ordering each verified variant group by `first_commit_at` provides a chronological sequence to identify which skill appeared first ("source/parent") and which appeared later ("modified child") \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 6: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .

**Key limitation for your** **THREATS\_TO\_VALIDITY.md**: Remember that `first_commit_at` tracks when the file was committed at its *current path* \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . If a developer renamed or moved a skill folder in a later commit, `first_commit_at` records the timestamp of the rename rather than the original authoring date \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

💡 Would you like a Python snippet demonstrating how to run intra-bucket similarity checks and diff security findings across chronological variants?

---

### User

so maybe I group by name and order by repo\_full\_path, first\_commit\_at, path. That way if a path was changed I will be able to identify it since it's name would likely be the same? the first thing committed for that artifact name would likely be the oldest version. If the path then changed I could see what it changed to assuming the repo name is the same. would that work? would it help?

---

### Model

**Yes, that strategy works very well and will significantly streamline your analysis pipeline.**

* * *

Why This Strategy Helps

-   **Detecting Intra-Repository Path Changes & Renames** If you group by `(repo_full_name, name)` and order by `first_commit_at`, you can easily spot skill files within the *same* repository that share the same frontmatter `name` \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . Because GitSkills records `first_commit_at` for a file at its current path, a relocated or refactored skill folder will show an older timestamp for the initial path and a newer timestamp for the updated path \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Establishing Cross-Repository Lineage** Grouping by `name` across *different* repositories and ordering by `first_commit_at` creates a chronological sequence \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . The entry with the earliest `first_commit_at` serves as the candidate "original source," while entries in other repositories with later commit timestamps serve as candidate "downstream copies" \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

Important Dataset Nuances to Keep in Mind

-   **Path-Specific Timestamps**: As noted in the GitSkills schema documentation, `first_commit_at` records the earliest commit found for the file at its **current path** \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . If a developer renamed or moved a skill folder, `first_commit_at` reflects when the file appeared at that new path rather than its original commit date \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Snapshot Nature**: GitSkills is a point-in-time snapshot collected in July 2026 \[Source: 4: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . If an old file path was completely deleted rather than remaining in the tree, only the surviving file at collection time is present in the `artifacts` table \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

Do You Still Need a Text Similarity Scan?

-   **Within the Same Repository**: If two files in the *same* repository share a frontmatter `name`, you can safely assume they represent the same skill undergoing edits or moves without needing a text similarity scan.-   **Across Different Repositories**: For generic names (e.g., `deploy`, `test`, `helper`), two unrelated developers might independently author skills from scratch. A quick, lightweight text-overlap check (such as comparing body character lengths via `body_chars` or word Jaccard similarity) takes microseconds and will prevent grouping completely unrelated skills together \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

This `GROUP BY name` SQL bucketing approach gives your group a clean, fast foundation for your Phase D operational definitions and Sprint 2 mining pipeline \[Source: 6: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

💡 Would you like to draft the SQL query that extracts these candidate skill clusters and orders them chronologically?

---

### User

yes please

---

### Model

Here is the SQL query to extract and cluster candidate skill variants, ordered chronologically for your analysis pipeline \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] :

```
SELECT 
    a.name,
    a.repo_full_name,
    a.path,
    a.file_sha,
    a.first_commit_at,
    a.last_commit_at,
    a.body_chars,
    a.content
FROM artifacts AS a
WHERE a.dedup_primary = 1
  AND a.frontmatter_valid = 1
  AND a.location_class IN ('canonical', 'skills-dir')
  AND a.filename IN ('SKILL.md', 'skill.md')
  AND a.body_chars > 50
  AND a.content IS NOT NULL
  AND a.name IS NOT NULL
ORDER BY 
    a.name ASC,
    a.repo_full_name ASC,
    a.first_commit_at ASC,
    a.path ASC;
```

* * *

How This Query Operates

-   **Focuses on Unique Content Blobs (****dedup\_primary = 1****)**: Because GitSkills assigns a unique `file_sha` to every distinct byte sequence, any skill that was copied and subsequently modified will have a different `file_sha` and will be retained as a representative row \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Filters Noise & Invalid Skill Artifacts**: Restricting to `frontmatter_valid = 1`, standard location classes (`canonical`, `skills-dir`), standard filenames, and non-trivial body size (`body_chars > 50`) strips out malformed Markdown files and symlinks \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Chronological Clustering**: Grouping by `name` buckets candidate variants together \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . Ordering by `repo_full_name` and `first_commit_at` lets you trace path edits within the same repository or establish an "earliest source vs. downstream copy" timeline across repositories \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 5: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] .

* * *

Downstream Python Execution Workflow

In your Python mining script, you can process the query results group-by-group:

-   **Iterate over** **name** **clusters**: Read candidate variants sharing the same YAML `name` \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Intra-Repository Tracking**: Entries sharing the same `(repo_full_name, name)` represent path updates or internal edits over time \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Cross-Repository Similarity Check**: For entries in different repositories under the same `name`, compute a lightweight Jaccard text similarity on word n-grams between the baseline skill (oldest `first_commit_at`) and newer skills \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 8: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .-   **Security Risk Diffing**: If text similarity exceeds your threshold (e.g., $≥70%$), pass both versions through your static regex scanner (searching for `curl`, `sudo`, `rm`, path traversal, or credential patterns) to detect whether risky behavior was introduced in the modified variant \[Source: 9: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

💡 Would you like to outline the threat model taxonomy or specific regular expressions for your rule-based static scanner next?

---

### User

shouldn't that query group by name and repo\_full\_name though?

---

### Model

It depends on whether you are looking for **intra-repository updates** (changes made within the same project) or **cross-repository propagation** (a skill copied from one project to another) \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

Here is why the SQL grouping level matters for both cases:

* * *

1\. Why `GROUP BY name` Alone Is Needed for Cross-Repository Reuse

Research Question 4 focuses on whether modified or reused skills across repositories introduce new security risks \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

-   If you group strictly by `(name, repo_full_name)`, SQL isolates each repository into its own separate bucket.-   To detect **cross-repository copies** (e.g., Repo B copying a skill created earlier in Repo A), candidate skills with the same `name` from **different repositories** must be in the same cluster.-   Grouping by `name` across all repositories puts Repo A's version and Repo B's version into the same processing bucket so you can compare Repo A (the earlier baseline) against Repo B (the modified copy).

* * *

2\. When `GROUP BY name, repo_full_name` Makes Sense

Grouping by `(name, repo_full_name)` is helpful if you want to collapse internal activity within a single repository first:

-   **Intra-Repository Path Changes**: If a single project moved a skill from `skills/pdf/SKILL.md` (`skills-dir`) to `.claude/skills/pdf/SKILL.md` (`canonical`), `(name, repo_full_name)` isolates that specific project's internal refactoring \[Source: 2: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Single Representative Per Repo**: If a repository contains multiple copies of the same skill, grouping by `(name, repo_full_name)` lets you select the earliest or canonical path within that repository before running cross-repo comparisons \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

3\. The Combined 2-Level Processing Pattern

To handle both without losing cross-repository visibility, the query retrieves rows ordered by `name, repo_full_name, first_commit_at` \[Source: 2: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . In Python, you process the results at two levels:

```
# Level 1: Outer loop clusters ALL skills sharing the same name (across ALL repos)
for skill_name, name_group in df.groupby('name'):
    
    # Level 2: Inner loop inspects skills within each specific repository
    for repo_name, repo_group in name_group.groupby('repo_full_name'):
        # Identify path changes or internal edits within this repo
        latest_repo_version = repo_group.sort_values('first_commit_at').iloc[-1]
    
    # Cross-Repo Comparison: Compare the oldest repo's skill against newer repos
    baseline_skill = name_group.sort_values('first_commit_at').iloc
    newer_skills = name_group[name_group['repo_full_name'] != baseline_skill['repo_full_name']]
    
    # Run similarity check & static security scan between baseline and copies...
```

* * *

Summary

-   Use **ORDER BY name, first\_commit\_at** in your base SQL query to fetch all candidates \[Source: 2: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   Use **groupby('repo\_full\_name')** **in Python** to summarize or deduplicate within individual repositories before comparing across different repositories.

💡 Would you like to draft the Python function that performs the cross-repository diffing and flags added executable commands?

---

### User

shouldn't that query group by name and repo\_full\_name though?

---

### Model

Adding a SQL `GROUP BY name, repo_full_name` clause to that query would actually work against your research goals for two reasons:

* * *

1\. SQL `GROUP BY` Collapses Rows

In SQL (including SQLite and DuckDB \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] ), `GROUP BY` collapses all matching records into a single summary row per group.

-   If you run `GROUP BY name, repo_full_name`, SQL requires every non-grouped column (`path`, `file_sha`, `content`, `first_commit_at`) to be wrapped in an aggregate function (like `MIN()`, `MAX()`, or `STRING_AGG()`).-   You would lose the individual file rows and text contents required for static scanning \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

2\. It Would Break Cross-Repository Comparison

To answer Research Question 4—detecting whether a modified copy in **Repository B** added risky behavior absent from **Repository A** \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] —you need skills from *different* repositories to end up in the same candidate comparison bucket \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

If SQL groups strictly by `repo_full_name`, Repository A and Repository B are isolated into separate groups, preventing cross-repository lineage comparisons.

* * *

What `ORDER BY name, repo_full_name, first_commit_at` Accomplishes Instead

Using `ORDER BY` returns **all individual skill occurrences** while sorting them logically for Python processing \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] :

-   **Primary Cluster (****name****)**: Places all skills across GitHub that share the same frontmatter `name` sequentially in your result set \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   **Sub-Cluster (****repo\_full\_name****)**: Groups records from the same repository together within that name bucket.-   **Chronology (****first\_commit\_at****)**: Orders the cluster by earliest commit timestamp, putting candidate "original" skills before "modified copies" \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 6: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

How to Group in Python

Once the query returns the ordered rows, you can perform the logical grouping cleanly in Python without losing row detail:

```
import pandas as pd
from itertools import groupby

# If using Pandas:
df = duckdb.query(sql_query).df()

for skill_name, cluster in df.groupby('name'):
    # 'cluster' contains ALL occurrences across ALL repos for this skill name,
    # ordered chronologically by first_commit_at.
    records = cluster.to_dict('records')
    
    baseline_skill = records  # Earliest committed skill
    
    for candidate_copy in records[1:]:
        # Compare text similarity between baseline_skill and candidate_copy
        # If similar, run static security diff (added commands, URLs, etc.)
```

This approach preserves every file occurrence while allowing your script to evaluate both **intra-repository path updates** and **cross-repository modified copies** \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

💡 Would you like to draft the Python function that diffs security scanner results between a baseline skill and its modified variants?

---

### User

shouldn't that query group by name and repo\_full\_name though?

---

### Model

**No, using an explicit SQL** **GROUP BY name, repo\_full\_name** **clause in that query would actually break your static analysis pipeline.**

There are two key reasons for this—one related to **SQL behavior** and one related to **your research question**.

* * *

1\. SQL Reason: `GROUP BY` Collapses Rows

In SQL, a `GROUP BY` clause collapses all matching rows into a single summary row per group. If you ran `GROUP BY name, repo_full_name`, SQL would require you to wrap all other fields (`content`, `path`, `file_sha`, `first_commit_at`) in aggregate functions like `MIN()`, `MAX()`, or `STRING_AGG()`.

That would destroy the individual file records you need to perform static regex scanning, text similarity checks, and security diffing.

By using **ORDER BY name, repo\_full\_name, first\_commit\_at** without a `GROUP BY` clause:

-   You preserve every distinct `SKILL.md` file occurrence \[Source: 1: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .-   The database returns rows sorted into contiguous blocks, making it trivial to process them in logical groups downstream in Python (e.g., using `df.groupby('name')` or `itertools.groupby`).

* * *

2\. Research Reason: You Need Cross-Repository Comparisons

Research Question 4 explicitly investigates whether modified skills introduce risky behavior across reused versions or source artifacts \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

-   **Grouping strictly by** **(name, repo\_full\_name)**: Isolates skills **within the same repository**. This only lets you compare edits or path moves made inside a single project.-   **Grouping by** **name** **across repositories**: Connects skills that share the same frontmatter name across **different repositories** \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

Sorting by `name` first and `first_commit_at` second allows you to trace a skill from its earliest appearance (e.g., in `repo_A`) to later modified copies in `repo_B` or `repo_C`, enabling you to detect if new network calls, file access, or executable commands were added in downstream copies \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 3: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

Summary Workflow in Python

After fetching the rows sorted by `ORDER BY name ASC, repo_full_name ASC, first_commit_at ASC`:

```
import pandas as pd

# 1. Load sorted candidate rows from SQL
df = pd.read_sql(query, conn)

# 2. Iterate through each skill name cluster
for skill_name, group in df.groupby('name'):
    if len(group) < 2:
        continue  # Skip singletons (no copies to compare)
    
    # Earliest committed skill in the cluster acts as the baseline candidate
    baseline = group.iloc
    
    # Compare against subsequent variants
    for idx, variant in group.iloc[1:].iterrows():
        # Perform lightweight similarity check & static security diff
        pass
```

* * *

💡 Would you like to write the Python static analyzer function to scan `content` for risky command execution and network access patterns?

---

### User

shouldn't that query group by name and repo\_full\_name though?

---

### Model

**It depends on which phase of the pipeline you are running.**

If you apply a SQL `GROUP BY name, repo_full_name`, SQL collapses all matching files into a single summary row per repository, which can either help or hinder your workflow depending on your exact analysis goal:

* * *

1\. When `GROUP BY name, repo_full_name` Works Against You

For Research Question 4, the primary objective is to detect whether a modified copy in **Repository B** introduced risky behavior absent from the original skill in **Repository A** \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

-   **Cross-Repository Isolation**: If you group strictly by `(name, repo_full_name)` in SQL, Repository A and Repository B are isolated into separate groups. You lose the ability to compare skills sharing the same `name` across different repositories in a single cluster.-   **Row Collapse**: SQL requires every non-grouped column (`path`, `file_sha`, `content`, `first_commit_at`) to be wrapped in an aggregate function (e.g., `MIN()`, `MAX()`, or `STRING_AGG()`) \[Source: 2: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . This destroys the individual file records and text content needed for static regex scanning \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 3: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

2\. When `GROUP BY name, repo_full_name` Is Useful (Intra-Repository Deduplication)

Grouping by `(name, repo_full_name)` **is** valuable if a single repository contains multiple edits, moves, or duplicate paths for the same skill, and you want to collapse those internal occurrences down to **one representative version per project**:

-   **Selecting One Version Per Repo**: If Repository A moved a skill from `skills/pdf/SKILL.md` to `.claude/skills/pdf/SKILL.md` \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] , grouping or partitioning by `(name, repo_full_name)` allows you to select just the latest or earliest path within that repository before making cross-repository comparisons.

* * *

3\. The Recommended Alternative: Window Functions or Python Bucketing

Instead of a SQL `GROUP BY` that collapses rows, you can use two cleaner approaches:

Option A: SQL Window Function (To get 1 row per repo)

If you want exactly one file per repository per skill name, use `ROW_NUMBER()` instead of `GROUP BY`:

```
SELECT * FROM (
    SELECT 
        a.name,
        a.repo_full_name,
        a.path,
        a.file_sha,
        a.first_commit_at,
        a.content,
        ROW_NUMBER() OVER (
            PARTITION BY a.name, a.repo_full_name 
            ORDER BY a.first_commit_at ASC
        ) as rn
    FROM artifacts AS a
    WHERE a.dedup_primary = 1
      AND a.frontmatter_valid = 1
      AND a.location_class IN ('canonical', 'skills-dir')
      AND a.filename IN ('SKILL.md', 'skill.md')
      AND a.body_chars > 50
      AND a.content IS NOT NULL
) sub
WHERE rn = 1
ORDER BY name ASC, first_commit_at ASC;
```

*This selects the earliest committed file path for each* *(name, repo\_full\_name)* *pair while keeping full row details intact.*

Option B: Sort in SQL, Group in Python (To preserve all cross-repo copies)

Use `ORDER BY name ASC, repo_full_name ASC, first_commit_at ASC` in SQL, and then let Python handle both levels of grouping:

```
# Group 1: Outer loop groups ALL repos sharing the same skill name
for skill_name, name_cluster in df.groupby('name'):
    
    # Group 2: Optional inner loop inspects occurrences within the same repo
    for repo_name, repo_cluster in name_cluster.groupby('repo_full_name'):
        # Track path edits or moves inside this specific repo
        pass
        
    # Cross-repo analysis: Compare baseline repo vs downstream repos
```

* * *

💡 Would you like to draft the Python function that scans `content` for executable commands, file operations, and network requests across these skill clusters?

---

### User

Really what I want to do is group the skills that are likely to be versions of one another. The repo name will likely be different for those skills, so that's not a good grouping criteria, I agree. I was thinking the description field is probably a better grouping criteria. It's likely that if two skills have the same name and description, and not the same file\_sha that is probably a case where one was a clone of the other and probably had some changes made to it afterwards. That's exactly the scenario that we want to address in research questions #4, no? Here's the query I was thinking of using: WITH filtered AS ( SELECT a.name, regexp\_replace( lower(trim(a.description)), '\\s+', ' ', 'g' ) AS normalized\_description, a.repo\_full\_name, a.path, a.file\_sha, a.first\_commit\_at, a.last\_commit\_at, a.body\_chars, a.content FROM artifacts AS a WHERE a.dedup\_primary = 1 AND a.frontmatter\_valid = 1 AND a.location\_class IN ('canonical', 'skills-dir') AND a.filename IN ('SKILL.md', 'skill.md') AND a.body\_chars > 50 AND a.content IS NOT NULL AND a.name IS NOT NULL AND a.description IS NOT NULL AND a.first\_commit\_at IS NOT NULL ), candidate\_families AS ( SELECT name, normalized\_description FROM filtered GROUP BY name, normalized\_description HAVING COUNT(\*) > 1 ) SELECT f.name, f.normalized\_description, f.repo\_full\_name, f.path, f.file\_sha, f.first\_commit\_at, f.last\_commit\_at, f.body\_chars, f.content FROM filtered AS f JOIN candidate\_families AS c ON f.name = c.name AND f.normalized\_description = c.normalized\_description ORDER BY f.name, f.normalized\_description, f.first\_commit\_at, f.repo\_full\_name, f.path; What are your thoughts? any issues you foresee with this approach?

---

### Model

**Yes, this approach is a strong, highly practical strategy for Research Question 4.**

By grouping skills that share both an exact frontmatter `name` and a normalized `description`—but possess different `file_sha` content hashes—you isolate **true functional variants** where a developer cloned a skill template and modified its body or code \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] .

* * *

Why This Query Strategy Works Well

-   **High Precision**: Generic skill names (e.g., `test`, `deploy`, `helper`) often cause false positives when grouped by `name` alone. Requiring an exact match on `(name, normalized_description)` almost entirely eliminates false matches between unrelated skills.-   **Computes at Scale**: SQL exact string matching on indexed/hashed strings executes in seconds on a personal laptop, bypassing the need for computationally heavy $O(N2)$ natural-language text similarity searches across the dataset.-   **Leverages Built-in Deduplication**: Because your `filtered` CTE restricts candidates to `dedup_primary = 1`, every row in a candidate family represents a **distinct** **file\_sha** **blob** \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] \[Source: 5: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . Consequently, `HAVING COUNT(*) > 1` inherently flags groups where the skill instructions or scripts were modified across copies \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 4: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

Potential Issues & Limitations to Keep in Mind

-   **Missed Variants (False Negatives)**
    -   **Modified Descriptions**: If a developer copied a skill and edited *both* the body and a few words of the `description`, your query will miss that pair because `normalized_description` no longer matches.-   **Template Boilerplate Collisions (False Positives)**
    -   **Scaffolding Defaults**: The official Agent Skills template contains default placeholder text (e.g., `"A clear description of what this skill does and when to use it"`) \[Source: 6: GitHub - anthropics/skills: Public repository for Agent Skills · GitHub\] . If multiple developers create different skills from the template and leave the default description unchanged while keeping a generic name, unrelated skills could be grouped together.-   **DuckDB Regex Syntax Adjustment**
    -   If you are running this in DuckDB, `regexp_replace(lower(trim(a.description)), '\s+', ' ')` works directly without requiring the PostgreSQL-style 4th argument `'g'`.-   **Lineage & Timestamp Boundaries**
    -   Ordering by `first_commit_at` establishes a chronological baseline (the candidate "original" vs. "modified copies") \[Source: 1: CSC\_580\_Group\_Project\_V2026.09.10.pdf\] \[Source: 7: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] . However, remember that `first_commit_at` records the earliest commit at the file's *current path* \[Source: 7: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] . If a skill folder was renamed in a later commit, `first_commit_at` reflects the rename timestamp rather than original authoring date \[Source: 7: GitHub - giuseppedestefanis/gitskills-sample: Sample dataset for the MSR'27 mining challenge · GitHub\] \[Source: 8: csc580-project8/DATA\_DICTIONARY.md at main · umdnp/csc580-project8 · GitHub\] .

* * *

💡 Would you like to draft the regular expressions for your rule-based static scanner to run against these identified skill variants?