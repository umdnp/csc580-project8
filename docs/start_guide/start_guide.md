# Project guide: from setup to SkillTrace

**Start with [data/README.md](../../data/README.md).** Follow its instructions to
download the dataset, create the separate DuckDB database, build the analysis
tables, and update the artifact groupings. Then return here for a guided first run.

This guide takes you through four tools and then the SkillTrace app. We use
**`cometchat-core`**, a small family with **five artifacts**, throughout the
database examples. You will analyze that family, compare two of its files,
scan its directed relationships, and explore the same results in your browser.

## 1. Finish setup and check that you are ready

You need the repository on your computer and its Python environment installed.
The main [README's Getting Started section](../../README.md#getting-started) explains
cloning the repository and installing `uv`. From the repository's main folder,
install the project dependencies:

```shell
uv sync
```

The **repository root** means the folder containing `pyproject.toml`, `TOOLS.md`,
`src/`, and `apps/`. Run every command in this guide from that folder. In a
terminal, use `cd` to move into it; in an editor, open a terminal for that folder.

We use `uv run` so commands use the project's Python environment. You do not
need to activate `.venv` manually. In `uv run python -m gitskills.tools.analyze_family`,
`python -m` means "run this project's Python module."

### Use the correct database file and path

The downloaded file is **SQLite**. The database produced by the setup scripts
is **DuckDB**. They may have the same filename, but they are different files.
The tools and SkillTrace need the generated DuckDB file.

The setup documentation uses `/c/data/...` paths. These are Git Bash paths on
Windows. WSL normally uses `/mnt/c/data/...`; update the configuration at the
top of `bin/create_gitskills_db.sh` and the database paths in setup commands if
you use WSL. Use a path your Python interpreter can read when setting
`GITSKILLS_DB` below.

Choose **one** block for the terminal you are using. Substitute your own path
if you stored the database elsewhere.

**Windows PowerShell:**

```powershell
$env:GITSKILLS_DB = "C:/data/duckdb/agent_skills_release.db"
```

**Git Bash on Windows, using Windows Python:**

```bash
export GITSKILLS_DB="C:/data/duckdb/agent_skills_release.db"
```

**WSL, using Linux Python:**

```bash
export GITSKILLS_DB="/mnt/c/data/duckdb/agent_skills_release.db"
```

An **environment variable** is a setting your terminal passes to commands.
This one tells the tools where the database lives. Set it again when you open
a new terminal, including the terminal you use to start SkillTrace.

Check Python, the configured path, and whether that file exists:

```shell
uv run python --version
uv run python -c "import os; from pathlib import Path; p = os.environ.get('GITSKILLS_DB'); print('Database:', p); print('File exists:', bool(p) and Path(p).is_file())"
```

You should see Python **3.12 or newer**, your DuckDB path, and `File exists: True`.
This checks the path; the family analysis below also checks that the database
has the required tables. The Sprint 1 sample view in `data/README.md` is needed
for the Sprint 1 notebook, but these family tools do not require that view.

## 2. Learn the few terms you will see

| Term | What it means here |
|---|---|
| Skill | Instructions stored in a `SKILL.md` file. |
| Artifact | One collected occurrence of a skill file, identified by a database ID. |
| Candidate family | Qualifying artifacts with the same exact skill name. A shared name is a starting point for comparison. |
| Skill variant | A distinct raw skill-file state, grouped by its file SHA. |
| Sibling file | Another file associated with a skill, such as a script or reference file. |
| Bundle variant | A skill state together with its known sibling-file state. |
| Cluster | Artifacts connected through qualifying similarity relationships. |
| Base / derived | The source and destination of a directional comparison. |
| Rule match | Text matched by a scanner rule, such as a package-install command or credential reference. |
| Delta | Derived count minus base count. `+2` means two more matches. |

Family relationships are **inferred**. An arrow does not prove someone copied
another repository, and a root candidate is not a verified original author.
Scanner findings identify text for review; they do not prove malicious behavior.
The tools read and scan stored text without executing its instructions.

## 3. Choose the right tool

| Tool | Use it when you want to… | Input |
|---|---|---|
| `analyze_family` | Find similar artifacts and inferred relationships. | Exact family name + DuckDB |
| `scan_diff` | Compare security-rule counts for two skill files. | Two local files, base first |
| `scan_family` | Scan the selected directed relationships in a family, including changed siblings. | Exact family name + DuckDB |
| `family_picker` | Browse family names interactively and generate analysis reports. | DuckDB |

The full command reference is [TOOLS.md](../../TOOLS.md). For help with an individual
tool, add `--help`, for example:

```shell
uv run python -m gitskills.tools.analyze_family --help
```

## 4. Analyze a small family

Run:

```shell
uv run python -m gitskills.tools.analyze_family cometchat-core --output apps/skilltrace/reports
```

This loads the five artifacts, compares their skill bodies, and prints a readable
report. It also saves `apps/skilltrace/reports/cometchat-core.json`, which we will
open in SkillTrace later. Repeating this command replaces that report.

Here is an excerpt from a verified run with the local GitSkills database and
the current code on **October 11, 2026**. Counts can change with a different
dataset, scanner, or analysis policy. Extra output is omitted below.

```text
Candidate family: cometchat-core
Artifacts:        5
Artifact groups:  1
Skill variants:   5
Bundle variants:  5
Clusters:         1
Policy:           5-token shingles, containment >= 0.80, Jaccard >= 0.30, shared >= 5

Related skill pairs: 10
Directed edges: 2
Equivalent undirected edges: 1
Ambiguous edges: 2

Family clusters
  Cluster 1: artifacts=5, skills=5, bundles=5
    Root candidates: [3485370, 3498417, 3498458]
    Directed edges:
      3498417 -> 3602273 change=skill-only containment=0.962 jaccard=0.414 basis=containment
      3498458 -> 3572584 change=skill-only containment=1.000 jaccard=0.676 basis=chronology
```

Read this as follows:

- **Five artifacts, one cluster:** all five are connected through similarity relationships.
- **Ten related skill pairs:** all ten possible pairs pass the similarity criteria;
  only two become selected directed parent relationships.
- **`3498417 -> 3602273`:** artifact `3498417` is the inferred base and `3602273`
  is the derived side. We will use this exact pair for `scan_diff`.
- **`skill-only`:** the skill text changes while the known sibling state matches.
- **`basis=containment`:** direction is inferred from how much of one body is
  contained in the other. This pair's arrow is not an established chronological order.
- **`basis=chronology`:** the other pair uses observed file-commit timing.
- **Equivalent / ambiguous:** one peer relationship is equivalent and two have
  unresolved direction. These are separate from the two selected arrows.

### Understand Jaccard and containment

The tool first removes the leading YAML frontmatter from the comparison, breaks
the skill body into tokens, and lowercases those tokens. A token is usually a
word or a technical item such as a path, URL, or command flag. It then builds
overlapping groups of five consecutive tokens, called **shingles**. For example,
six tokens produce two five-token shingles: tokens 1–5 and tokens 2–6.

The comparison uses a **set of distinct shingles**. Repeating the exact same
shingle does not increase the set's size. Whitespace and token case differences
do not affect these scores. A score of `1.0` describes this representation;
it does not necessarily mean the original files are identical byte for byte.

Let `A` and `B` be the two files' shingle sets. "Shared" means shingles found in
both; "combined" means all distinct shingles found in either, counting a shared
shingle only once.

| Measure | Calculation | What it tells you |
|---|---|---|
| Containment A → B | Shared shingles ÷ shingles in A | How much of A appears in B? |
| Containment B → A | Shared shingles ÷ shingles in B | How much of B appears in A? |
| Jaccard | Shared shingles ÷ combined distinct shingles | How much overlap is there relative to both files together? |

**Containment is directional.** A shorter skill can be largely preserved inside
a longer skill. In that case, containment from the shorter file to the longer
one can be high while containment in the reverse direction is low.

**Jaccard is symmetric.** Swapping A and B does not change it. Adding substantial
new text to B makes the combined set larger, so Jaccard can decrease even when
most of A is still present in B.

For a concrete example, suppose A has **100** distinct shingles, B has **250**,
and **90** are shared:

```text
Containment A → B = 90 / 100 = 0.90
Containment B → A = 90 / 250 = 0.36
Combined shingles = 100 + 250 - 90 = 260
Jaccard           = 90 / 260 ≈ 0.346
```

This looks like much of A is retained in a substantially expanded B. It passes
the default relatedness requirements: maximum containment is at least `0.80`,
Jaccard is at least `0.30`, and there are at least five shared shingles.

Both scores matter. If all 100 shingles in A appear in a 400-shingle B,
containment A → B is `1.0`, but Jaccard is only `100 / 400 = 0.25`. That pair
**fails** the default Jaccard threshold. Conversely, two 100-shingle files
sharing 60 shingles have Jaccard `60 / 140 ≈ 0.429`, but both containment scores
are `0.60`, so they **fail** the containment threshold. The minimum shared count
also prevents a very small overlap from qualifying merely because its ratios
look high.

In our actual `3498417 -> 3602273` result, containment `0.962` means about
**96.2% of the base's distinct shingles** appear in the derived file. Jaccard
`0.414` means shared shingles make up about **41.4% of the combined set**.
These percentages measure token-pattern overlap, not the percentage of lines
copied or a probability that one author copied another.

You can start with the defaults. The thresholds are exploratory and need
validation for final research conclusions.

**This command analyzes relationships; it does not run a security scan.**

### Other useful analysis options

```shell
uv run python -m gitskills.tools.analyze_family cometchat-core --verbose
uv run python -m gitskills.tools.analyze_family cometchat-core --json
uv run python -m gitskills.tools.analyze_family cometchat-core --min-containment 0.90 --min-jaccard 0.50
```

`--verbose` adds metadata and relationship evidence. `--json` prints structured
data instead of the readable report. The last command tries stricter similarity
thresholds and may change the graph; it does not overwrite our saved report.

For reference, both family tools accept these analysis settings:

| Option | Default | Meaning |
|---|---:|---|
| `--shingle-size` | `5` | Tokens per comparison shingle. |
| `--min-containment` | `0.80` | Minimum containment in at least one direction. |
| `--min-jaccard` | `0.30` | Minimum shared-to-combined shingle ratio. |
| `--min-shared-shingles` | `5` | Minimum number of shared shingles. |
| `--direction-margin` | `0.10` | Minimum containment difference used for direction when stronger evidence is unavailable. |

### Follow the analysis decision order

`analyze_family` answers three questions in sequence: **which artifacts should
be compared, which pairs are related, and whether a related pair has a supported
direction.** Here is the process:

1. **Load the exact-name candidate family.** Only qualifying artifacts with the
   requested name in `artifact_groupings` are loaded. Matching names identify
   candidates; they do not establish relatedness by themselves.
2. **Group file states.** Identical raw skill content is grouped by `file_sha`
   into skill variants. The tool also forms bundle variants using the skill
   state and known sibling state. Description-based artifact groups provide
   context but do not restrict comparisons within the family.
3. **Prepare body shingles and compare every distinct skill-variant pair.**
   Frontmatter is excluded and tokens are lowercased as described above. The
   tool computes both containment scores, Jaccard, and the shared-shingle count.
4. **Apply the relatedness checks.** For distinct skill variants, the code checks
   maximum containment, then Jaccard, then the shared-shingle count. All three
   must pass; a strong score on one does not compensate for failing another.
5. **Form similarity clusters.** Qualifying pairs connect their variants into
   clusters. If A relates to B and B relates to C, all three can share a cluster
   even when A and C do not directly pass the pairwise checks.
6. **Classify bundle changes and resolve direction.** For a related pair, the
   tool considers equivalent state, sibling changes, and the evidence below.
   Bundles sharing the same raw skill variant can still be compared for sibling
   changes without a separate distinct-skill similarity test.
7. **Select parent relationships.** From the supported directed candidates, the
   tool selects at most one predecessor per target bundle while avoiding cycles.
   Other supported directed candidates remain available as additional related
   comparisons. A related pair does not automatically become a selected arrow.

The relatedness checks in step 4 are an **AND** condition:

```text
max(containment A → B, containment B → A) >= 0.80
AND Jaccard                             >= 0.30
AND shared shingles                     >= 5
```

The evaluation order is not a ranking of evidence: failure of any requirement
rejects a distinct-variant pair under the current policy. Dates or declared
sources do not rescue a pair that fails these similarity requirements. Use the
same settings across analysis and scanning when you want comparable results.

### Understand how direction is determined

Relatedness asks whether two skill bodies overlap enough. Direction asks whether
the evidence supports treating one related bundle as the source and the other
as the destination. Jaccard cannot establish direction because it is symmetric.

For a qualifying pair, the tool first checks declared provenance. Conflicting
declared sources leave the relationship unresolved. A supported declared source
can establish direction; otherwise, equivalent skill-and-sibling states remain
equivalent peers rather than being forced into an earlier/later relationship.
For other related pairs, the remaining evidence is considered in this order:

| Priority | Report basis | How it supports a direction |
|---|---|---|
| 1 | `declared-source` | Supported frontmatter provenance identifies a source artifact. This is checked before the remaining evidence. |
| 2 | `chronology` | Different observed `first_commit_at` dates establish an earlier and later file state. |
| 3 | `equivalent-peer-chronology` | An equivalent bundle with known sibling state supplies an earlier observed chronology proxy. The chronology comparison uses that effective date and records its source. |
| 4 | `repo-created-boundary` | An observed state predates the other repository's creation, providing a conservative boundary when chronology did not establish direction. |
| 5 | `containment` | The two containment scores differ by at least `--direction-margin`, which defaults to `0.10`. The more-contained side is treated as the source. |

For the hypothetical `0.90` versus `0.36` example above, the containment gap is
`0.54`. If no stronger evidence resolves direction, that exceeds the default
margin and supports A → B. If both containment scores were `0.90`, there would
be no directional gap: the files could still be related, but containment would
not provide an arrow. Stronger supported evidence takes precedence over this
fallback; the tool does not simply assume the shorter file came first.

If the available evidence does not resolve direction, the pair stays undirected.
`first_commit_at` is the earliest commit observed at the file's current path,
not proof of original authorship. Repository creation dates are boundaries,
not skill creation dates. Sibling state helps classify bundle changes and
equivalence; the similarity scores themselves come from the `SKILL.md` body.

The change labels you may see in other families are:

| Label | Meaning |
|---|---|
| `skill-only` | Skill content changes; known sibling state matches. |
| `siblings-only` | Skill content is equivalent; known sibling state changes. |
| `skill+siblings` | Both change. |
| `equivalent` | Skill and known sibling state are equivalent. |
| `unknown` | Sibling information is insufficient to classify the bundle change. |

## 5. Run scan_diff on two files from that same family

`scan_diff` takes **file paths**, not a family name or database IDs. First export
our chosen pair from DuckDB using the companion script:

```shell
uv run python docs/start_guide/export_guide_pair.py
```

The script opens the database read-only and saves these two local text files
under the repository root, regardless of the terminal's current directory:

```text
tests/temp/
├── base/cometchat-core/SKILL.md       (artifact 3498417)
└── derived/cometchat-core/SKILL.md    (artifact 3602273)
```

These are copies of stored dataset text for the walkthrough. `tests/temp/` is
ignored by Git, and repeating the export replaces these temporary copies.
`scan_diff` accepts any two file paths, so this location does not change its behavior.

The automated regression test uses separate fixtures under `tests/sample_skills/`
and expected results in `tests/pytests/test_configs/cometchat-core.json`. Run it with:

```shell
uv run pytest tests/pytests/test_sample_skills.py -v -k cometchat-core
```

Now compare them. **Keep the base file first and the derived file second.**

```shell
uv run python -m gitskills.tools.scan_diff tests/temp/base/cometchat-core/SKILL.md tests/temp/derived/cometchat-core/SKILL.md --output output/start_guide/diff-scans
```

The tool prints JSON and diagnostic lines. It saves the JSON to
`output/start_guide/diff-scans/cometchat-core.json`. For a file named `SKILL.md`,
the output name comes from its parent folder.

The verified result for this pair is:

```json
{
  "introduced": {
    "command_execution": false,
    "network_access": false,
    "filesystem_access": false,
    "credential_access": false,
    "external_code_execution": false,
    "system_modification": false
  },
  "rule_match_count": {"base": 23, "derived": 46, "delta": 23},
  "rule_deltas": {
    "CMD-001": {"base": 3, "derived": 5, "delta": 2},
    "CMD-002": {"base": 1, "derived": 5, "delta": 4},
    "CRED-001": {"base": 11, "derived": 14, "delta": 3},
    "CRED-002": {"base": 5, "derived": 12, "delta": 7},
    "EXT-002": {"base": 1, "derived": 3, "delta": 2},
    "NET-001": {"base": 2, "derived": 7, "delta": 5}
  }
}
```

| Rule | What it detects | Base | Derived | Delta |
|---|---|---:|---:|---:|
| `CMD-001` | Shell command blocks | 3 | 5 | +2 |
| `CMD-002` | Command invocations | 1 | 5 | +4 |
| `CRED-001` | Credential or secret references | 11 | 14 | +3 |
| `CRED-002` | Credential-file references | 5 | 12 | +7 |
| `EXT-002` | External package installation | 1 | 3 | +2 |
| `NET-001` | URL references | 2 | 7 | +5 |

**Why are all introduced capabilities false when counts increased?**
Each category with increased matches was already present in the base. An
introduced capability means a previously absent category appears; a positive
rule delta means an existing rule has more matches. This example has increased
signals without a newly introduced category.

Counts are textual matches, not unique actions. Rules can overlap. A credential
reference can be documentation rather than a real secret. Read the surrounding
text before drawing conclusions. A zero or negative delta also does not prove
that the content is safe or that its behavior is unchanged.

For matching-line detail, repeat the comparison with `--verbose`:

```shell
uv run python -m gitskills.tools.scan_diff tests/temp/base/cometchat-core/SKILL.md tests/temp/derived/cometchat-core/SKILL.md --verbose
```

Credential-related excerpts are redacted. Skill frontmatter (the YAML metadata
at the top of the file) is excluded from behavioral scanning. This comparison
scans the two skill bodies; it does not scan their sibling files.

## 6. Scan the family's directed relationships

Run:

```shell
uv run python -m gitskills.tools.scan_family cometchat-core --output output/start_guide/family-scans
```

This repeats family analysis and scans its **selected directed pairs**. It also
scans new or changed sibling content when applicable. Equivalent peers and
direction-unknown relationships are not treated as directed scan pairs.

For this family, the verified summary is:

```text
Candidate family:        cometchat-core
Pairs analyzed:          2
Pairs flagged:           2
Pairs incomplete:        0
Ambiguous edges skipped: 2
Scanner scope:           SKILL.md body + changed sibling files
```

The flagged pairs are `3498417 -> 3602273` (our example) and
`3498458 -> 3572584`. Both have increased skill-body matches. Use `--verbose`
to see rule descriptions, direction evidence, and matching-line details, or
`--json` for structured output:

```shell
uv run python -m gitskills.tools.scan_family cometchat-core --verbose
uv run python -m gitskills.tools.scan_family cometchat-core --json
```

For another family, a changed sibling may be flagged even if its net rule count
does not increase. An incomplete sibling scan means some required content or
SHA information was unavailable; it is not a clean result.

Keep `scan_family` output separate from `analyze_family` reports: both use
`<NAME>.json`, but SkillTrace needs the **analysis** format. Writing a family
scan into `apps/skilltrace/reports` could overwrite the graph report.

## 7. Browse other families with family_picker

```shell
uv run python -m gitskills.tools.family_picker
```

The picker shows ten randomly chosen family names and their artifact counts.
At its prompt:

- Enter `1` through `10` to analyze a displayed family.
- Type an exact name, such as `cometchat-core`, to analyze that family directly.
- Enter `R` to get another random list.
- Enter `Q`, or press `Ctrl+C`, to quit.

After each analysis it returns to the selection screen. Reports are saved in
`apps/skilltrace/reports`. For custom thresholds, a different database path, or
a different output directory, use `analyze_family` directly.

## 8. Start SkillTrace

SkillTrace is a local web app: Python serves it on your computer and your browser
displays it. It loads family relationships from saved analysis reports and uses
DuckDB for content, metadata, search, diffs, and scans.

You already have the dependencies, database setting, and
`apps/skilltrace/reports/cometchat-core.json` from the earlier steps. No separate
frontend installation is needed.

From the repository root, in a terminal with `GITSKILLS_DB` set, run:

```shell
uv run python -m apps.skilltrace --host 127.0.0.1 --port 8000
```

Leave that terminal running. Open [SkillTrace](http://127.0.0.1:8000) in your
browser. `127.0.0.1` means your own computer; `8000` is the server's port.
Return to the terminal and press `Ctrl+C` when you want to stop the app.

You can also use `bash bin/start_skilltrace_server.sh` from a Bash terminal with
the project environment active. The module command above works in PowerShell,
Git Bash, or WSL through `uv` and avoids the script's default `/c/data/...` path.

**Database setting priority:** SkillTrace uses `GITSKILLS_DB` first, then
`--db PATH`, then `C:/data/duckdb/agent_skills_release.db`. A stale environment
variable overrides `--db`. For the family command-line tools, an explicit
`--db` takes priority over the environment variable.

## 9. Explore the same family in SkillTrace

### Open the graph

1. Choose `cometchat-core.json` in the **Report** dropdown. If it is missing,
   click **Refresh reports** after generating the analysis report.
2. Check the database path and connection status at the bottom of the page.
3. Choose **Entire cluster** in the **View** dropdown to see all five artifacts.
4. Click **Fit visible family** if you need to bring the nodes into view.

Each node is an artifact. Directed connections are inferred parent-to-derived
relationships; equivalent and direction-unknown peers are also represented.
Use the graph legend and relationship details to distinguish them. The footer
shows the similarity settings stored in the report.

### Inspect a skill and its metadata

1. Select artifact **`3602273`**, our derived artifact, by clicking its node or
   entering its ID in the search box and clicking **Search**, then the result.
2. Read its repository, path, and artifact details. The relationship panel shows
   the base/derived IDs, direction basis, change type, and similarity values.
3. Click **View content** in the selected-artifact panel to read its `SKILL.md`.
4. Use **Copy Contents** if you want the original database text. Close the dialog
   to return to the graph.

Database-backed search also accepts names, repositories, paths, filenames, and
SHAs. Artifact-ID search is a convenient way to repeat this example.

### View the text diff

1. Keep **`3602273`** selected.
2. In **Compare To**, choose its **parent `3498417`** if it is not already selected.
3. Click **View diff**.
4. Confirm that the base is `3498417` and the derived side is `3602273`, then
   review added, removed, and changed text side by side.

The panes have alignment rows to make changes easier to read. **Copy Contents**
copies the raw file text rather than those display rows.

### Run the same scan in the app

1. Close the diff dialog and keep the same derived artifact and parent selected.
2. Click **Run scan**.
3. Confirm the heading says **`3498417 → 3602273`**.
4. Compare the results with section 5: **23 base matches**, **46 derived matches**,
   **+23 total match delta**, and **no introduced capabilities**. The changed-rule
   table should contain the six rules shown earlier.
5. Review the matching-line details alongside the text diff to understand the changes.

SkillTrace's **Run scan** compares the two `SKILL.md` bodies, matching the
`scan_diff` example. It does not include the changed-sibling scanning performed
by `scan_family`. Use that command when you need the broader bundle scan.

The app shows **Run scan** for a selected derived artifact's parent comparison.
Choosing an equivalent, direction-unknown, or additional related peer permits
text comparison but does not enable the scan button.

### Inspect sibling files and larger relationships

If the selected artifact has content-bearing sibling files, choose one in the
sibling selector and use its **View content** or **View diff** button. Sibling
diffs can show files that were added, removed, or changed. `NONE` means there are
no content-bearing sibling files available for that selection.

Try **Direct relationships** for immediate neighbors and **Direct and indirect
relationships** for a broader lineage view. **Focus selected**, the zoom buttons,
and **Fit visible family** help navigate larger graphs.

SkillTrace reads valid current `analyze_family` JSON reports only from
`apps/skilltrace/reports`. It remembers the last selected valid report when you
refresh the browser. See [the SkillTrace README](../../apps/skilltrace/README.md) for
additional reference and [local API documentation](http://127.0.0.1:8000/docs)
while the server is running.

## 10. Fix common first-run problems

For `scan_diff`, `analyze_family`, and `scan_family`, `--output DIR` saves JSON
in that directory; `--output` without a directory uses `output/`. Existing
directories are reused and same-name reports are replaced. `--verbose` adds
detail, and `--help` shows command usage. Only the family tools accept `--json`;
`scan_diff` already prints JSON.

A command's **exit status** tells the terminal whether it completed:

| Tool | Status 0 | Status 1 | Status 2 |
|---|---|---|---|
| `analyze_family` / `scan_family` | Completed | Lookup, database, analysis/scan, or write failure | Path, arguments, or output-directory setup error |
| `scan_diff` | Completed | Input-read or output-write failure | Arguments or output-directory setup error |

Read the report's completeness fields as well as the exit status. In particular,
`scan_family` can report incomplete sibling coverage even when the command completes.

| What you see | What to check or do |
|---|---|
| `uv` is not recognized | Install `uv` using the main README, then open a new terminal. |
| `No module named gitskills`, `duckdb`, or `apps.skilltrace` | Run `uv sync` from the repository root, and use the guide's `uv run` commands from that folder. |
| Database path required / database not found | Set `GITSKILLS_DB` in this terminal and repeat the path check in section 1. |
| An error opening the database or missing tables | Confirm you selected DuckDB rather than SQLite and completed the import, analysis-table, and artifact-grouping steps in `data/README.md`. |
| Candidate family not found | Use the exact name `cometchat-core`; confirm the grouping update ran against this database. |
| Input file cannot be read by `scan_diff` | Run the export helper first and check that you are in the repository root. |
| Empty Report dropdown | Generate an `analyze_family` report in `apps/skilltrace/reports`, then click **Refresh reports**. Scan reports are ignored. |
| Graph appears but content/diffs fail | Check the DuckDB connection status. The graph comes from JSON; file content requires the database. |
| No **Run scan** button | Select the derived artifact `3602273`, then its parent `3498417` in **Compare To**. |
| Browser cannot connect | Keep the server terminal running and look there for startup errors. |
| Port 8000 is already in use | Start with `--port 8001`, then open `http://127.0.0.1:8001`. |
| Your counts differ | Confirm the pair order, dataset, checkout, and similarity settings. Record differences instead of assuming the example counts always apply. |

You have completed the walkthrough when you can generate the five-artifact
family report, reproduce the same pair's scan in the terminal and SkillTrace,
and explain why increased rule matches can occur without an introduced category.
