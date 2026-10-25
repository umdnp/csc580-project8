# Dataset content remains data (Story 5.2)

The implemented security-analysis workflow statically inspects dataset content.
It does not run a skill, execute a sibling script, install a referenced package,
or fetch a URL found in the content. Findings describe text patterns, not observed
execution or proof that an instruction is malicious.

This conclusion is supported by the source review below and regression tests at
the scanner entry points. The review covers the repository's default rules,
`scan_diff`, `scan_family`, the extraction notebook's scanner calls, and
SkillTrace's content/diff/scan paths. It is not a claim about arbitrary custom
Python rules, modified project code, or manually running an exported artifact.

## Reviewed content paths

| Path | How content is handled |
| --- | --- |
| [File CLI](../../src/gitskills/tools/scan_diff.py) | Reads files as UTF-8 text, calls `SkillAnalyzer.scan`, and compares results. Input filenames are not invoked as programs or imported as modules. |
| [Family loader](../../src/gitskills/data/families.py) and [sibling loader](../../src/gitskills/data/siblings.py) | Read stored content from DuckDB opened read-only. Candidate names and artifact IDs are bound query parameters. Content is returned as data, not submitted as SQL or written to an executable file. |
| [Analyzer](../../src/gitskills/analysis/analyzer.py), [default rules](../../src/gitskills/rules/registry.py), and [regex evaluation](../../src/gitskills/rules/base.py) | Mask skill frontmatter, match project-defined regular expressions against strings, and construct counts, profiles, and evidence. Default rules do not call a shell, Python evaluator, package installer, or network client. |
| [Provenance](../../src/gitskills/analysis/provenance.py) and [similarity](../../src/gitskills/analysis/similarity.py) | Parse selected scalar strings and tokenize text. Provenance does not use a YAML object constructor; YAML tags remain strings. URLs are parsed for metadata, not requested. |
| [Family scanner](../../src/gitskills/analysis/family_risk.py) and [comparator](../../src/gitskills/analysis/comparator.py) | Scan stored skill/sibling text and compare scan results. Sibling paths are evidence metadata, not instructions to open or run local scripts. |
| [Extraction notebook](../../notebooks/extraction_pipeline/samples_extraction_and_exploration.ipynb) | Calls the same analyzer and comparator on loaded text. Running the project's notebook code is distinct from executing dataset instructions. |
| [SkillTrace server](../../apps/skilltrace/app.py) | Returns content as JSON, builds text diffs, and calls the same scanner for on-demand comparisons. The scan handler does not launch a skill. |
| [SkillTrace viewer](../../apps/skilltrace/index.html) | Content dialogs, diff lines, and rule evidence use `textContent`. Dataset HTML/JavaScript is displayed as text rather than inserted as executable markup. Copying content copies text to the clipboard. This display path was source-reviewed; the Python tests do not execute a browser. |

A search of production Python under `src/gitskills` and `apps/skilltrace` found
one subprocess launcher: [the family picker](../../src/gitskills/tools/family_picker.py).
It starts the project's `gitskills.tools.analyze_family` module using a fixed
argument list and the default `shell=False`. A selected dataset family name is
one literal argument, not a shell command. It does not run artifact content.
Executing trusted project code and registered rule implementations is necessary
to perform analysis; dataset text is never promoted to that role in these paths.

## Repeatable verification

From the repository root:

```shell
uv run pytest tests/pytests/test_static_analysis_boundary.py -v
```

The six constructed test cases check:

- The file CLI reads Python and shell instructions without running them.
- Provenance extraction leaves Python object-construction tags inert.
- The family CLI loads skill and sibling payloads from a temporary DuckDB,
  reports scanner findings, and neither runs nor materializes the sibling script.
- SkillTrace's scan handler treats returned artifact text as data. Report and
  database lookups are substituted; the actual scanner and comparison run.
- The family picker passes a command-looking dataset name as a literal argument.

During the scan calls, tests reject `exec`, `eval`, common process-launch APIs,
and common network entry points. Python and shell payloads include a temporary
marker-file instruction; tests verify that no marker appears. Fixtures are
prepared before the guards are installed, and the guards are restored afterward.
The tests also require normal findings, so rejecting every input cannot satisfy
the scanner checks.

These guards cover specific runtime entry points and constructed inputs, not
every possible way Python or a browser could execute code. Source review supplies
the accompanying evidence about how untrusted text flows through the current
implementation. No runtime sandbox for user-supplied Python rules is provided.

Recheck this boundary when changing rule implementations, content parsers,
subprocess calls, fetching/export features, notebook execution paths, or viewer
rendering. Reviewers should inspect dataset text locally without following its
instructions or executing bundled scripts.
