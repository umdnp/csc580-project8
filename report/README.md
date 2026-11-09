# Research report

## Main narrative and appendices

The report centers on the research question, the eleven risk indicators (RIs),
the three Sprint 3 trials, results, validation, and interpretation. The main
narrative flows in a compact two-column layout; references and appendices are
outside that narrative. Page counts depend on fonts and the final build, so
inspect the rendered PDF rather than targeting a page count at the expense of
readability.
Word and PDF pagination can differ.

`pandoc.yaml` defines the reading order. Section filenames run from 01 through
12 in that same order, ending with the conclusion (11) and references (12).
Appendices A-F are stored together in `appendices/`. Background precedes the dataset and
method; results precede validation, discussion, and validity limits. Main
sections flow without forced page breaks. References and the first appendix
begin on new pages; later appendices use the available space. Large PlantUML
diagrams have dedicated pages.

| Appendix | Supporting material | Source |
| --- | --- | --- |
| A | Selection SQL, preparation workflow, and selection audit | [Dataset preparation](appendices/A-dataset-and-preparation.md) |
| B | Extraction rule definitions, pipeline settings, and component diagrams | [Implementation](appendices/B-implementation-details.md) |
| C | Validation scope and current status | [Validation materials](appendices/C-validation-materials.md) |
| D | Current family, direction, and RI tables | [Extended results](appendices/D-extended-results.md) |
| E | Links to supporting repository material and result artifacts | [Supporting material](appendices/E-reproducibility-and-artifacts.md) |
| F | AI assistance in development and report preparation | [Disclosures](appendices/F-disclosures.md) |

The report now describes the three saved Sprint 3 trials (300 distinct
families, 2,157 primary directed comparisons). The abstract, evaluation,
discussion, validity, and conclusion have been synchronized provisionally with
the Sprint 3 counts, but the team's adjudicated manual review remains pending.
Sections 02–04 still need a separate readability and related-work pass before
final submission. Editing or building the report does not rerun the pipeline
or adjudicate review labels.

## Build the project report

The report is assembled from `sections/*.md` and `appendices/*.md` using `pandoc.yaml`. Pandoc includes
Lua; no separate Lua installation is required. The Lua filter renders PlantUML
figures locally using portable Java and PlantUML with the bundled Smetana layout
engine. Diagram text never goes to a public rendering service.

Run commands from the repository root. The Python build helper also works when
invoked by its absolute path from another directory.

## Portable setup on Windows x64

With the project Python environment available, run:

```shell
uv run python bin/setup_report_tools.py
```

This downloads the official, pinned Pandoc ZIP, PlantUML JAR, and Eclipse Temurin
Java 21 JRE ZIP and verifies their SHA-256 checksums against `report/toolchain.json`.
It extracts them into `.cache/report-tools/`, which is ignored by Git. It makes no
system installation, registry changes, or persistent PATH changes. Internet access
is needed for the initial downloads; rendering and subsequent report builds are
local. Existing verified downloads are reused.

The configured versions are Pandoc 3.12.1 and PlantUML 1.2026.8; the exact Java
release and all download URLs/checksums are recorded in `toolchain.json`.

Pandoc 3.11+ on PATH can also be used. On other operating systems, use installed
Pandoc and Java 21 and obtain the pinned PlantUML JAR from the manifest. Set
`PANDOC_BIN`, `PLANTUML_JAVA`, and `PLANTUML_JAR` to override executable/JAR paths
when needed. These are file paths, not shell command strings. The build helper
selects installed Pandoc first and otherwise uses the portable Windows copy.

## Generate the report

HTML preview (diagrams are embedded, so the HTML can be moved or shared):

```shell
uv run python bin/build_report.py --format html
```

Word output:

```shell
uv run python bin/build_report.py --format docx
```

Official PDF:

```shell
uv run python bin/build_report.py --format pdf
```

PDF generation additionally requires XeLaTeX from MiKTeX or TeX Live on PATH.
The PDF preamble uses `fvextra` to wrap long appendix code lines; this standard
package must be available in the TeX installation.
The portable setup does not install a TeX distribution. HTML and Word builds do
not need TeX. To inspect the generated LaTeX without a TeX installation:

```shell
uv run python bin/build_report.py --format latex
```

HTML, Word, and LaTeX outputs go to `report/generated-report/`. The PDF goes to
`report/final.pdf`. The existing direct Pandoc commands still work when Pandoc
and the local renderer are configured:

```shell
pandoc --defaults report/pandoc.yaml -o report/generated-report/final.html
pandoc --defaults report/pandoc.yaml -o report/generated-report/final.docx
pandoc --defaults report/pandoc.yaml --pdf-engine=xelatex -o report/final.pdf
```

For direct commands without environment overrides, the filter uses `java` on
PATH and `.cache/report-tools/plantuml.jar`. The Python helper supplies the
portable Java executable automatically. `pandoc --version` reports the built-in
Lua engine; the portable copy can be checked with
`.cache/report-tools/pandoc.exe --version` in PowerShell.

## Edit or add a PlantUML diagram

Keep editable source files in `report/diagrams/`. Insert a marked code block in
the relevant report section, with its source path relative to the repository root:

````markdown
```{#fig-example .plantuml source="report/diagrams/example.puml" caption="An explanatory caption."}
```
````

Inline PlantUML inside a `.plantuml` code block also works. Sources must contain
`@startuml` and `@enduml`. Use unique figure identifiers. Images are sized
by the two-column LaTeX figure filter. Ordinary figures stay in one column;
`.wide` spans both columns, and `.fullpage .wide` reserves a page for a
large diagram. This prevents figures from overlapping adjacent columns.

On a normal build, `filters/plantuml.lua` reuses an existing PNG or invokes local
Java/PlantUML if the diagram changed. It uses Smetana rather than an external
Graphviz installation. Failures stop the build instead of substituting an older
image. Unmarked SQL, Python, and shell blocks remain ordinary code blocks.

Generated PNGs are kept in `report/diagrams/rendered/`. Commit these together with
sources, the filter, and `toolchain.json`. Their filenames hash the normalized
source and pinned toolchain manifest, so edits or toolchain changes select a new
cache entry. Changing only a caption does not require rerendering.

To build exclusively from cached images without invoking Java:

```shell
uv run python bin/build_report.py --format html --cached-only
```

This mode requires only Pandoc and the committed PNGs. A missing or invalid cache
entry is an error. The toolchain manifest pins the portable renderer, but a custom
runtime supplied through environment variables must match it for comparable
output. Use a deliberate manifest update when upgrading the rendering toolchain.

## Diagrams included

- `preparation-activity.puml`: candidate reduction and end-to-end cohort analysis,
  in Dataset and Data Preparation.
- `relationship-state.puml`: conceptual relationship classification, in Method
  and Implementation. These are classification outcomes, not stored mutable states.
- `family-scan-sequence.puml`: the successful family-scan component interactions,
  including conditional sibling review, in Method and Implementation.

## Two-column table and figure layout

The PDF uses the new two-column typography configured in `metadata.yaml`
(9-point TeX Gyre Pagella and a quarter-inch column gutter). The
`two_column_tables.lua` filter is active in `pandoc.yaml` for all direct and
scripted Pandoc builds. It wraps long table-cell text, adds light alternating
row shading and breathing room, and constrains image width and height.

Write tables as normal Markdown. Mark a table to span both columns by adding
`{.wide}` to its caption line:

```markdown
| Category | Rules | Detection | Limitation |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

: Scanner rule coverage {.wide}
```

The marker is hidden from the rendered caption. Tables with four or more
columns also span both columns by default. Shorter tables normally stay within
one column; when their descriptions are long, give them a `{.wide}` caption.
Figures work similarly: `![Caption](path){.wide}` spans both columns, while
small figures default to one column. A `.fullpage .wide` PlantUML block is
placed on a dedicated figure page.

References and the first appendix start on new pages; appendix tables and
short narrative sections do not add automatic page breaks. Large diagrams are
the deliberate exceptions. Wide LaTeX floats may move to the top of a nearby
page to fit without clipping, so visually inspect the generated PDF.

The report files in this directory are the editable sources. Rebuild the PDF
with the project's normal build helper after edits; do not treat an older
`final.pdf` as evidence of the latest report text.

## Heading and paragraph pagination

Pagination is configured centrally; individual Markdown paragraphs need no extra
markup. PDF/LaTeX output receives `\clubpenalty=10000`,
`\widowpenalty=10000`, and `\displaywidowpenalty=10000` from
`filters/pagination.lua`. These prevent single first/last paragraph lines at page breaks,
targeting at least two lines on each side when a paragraph splits. Standard
LaTeX section headings already discourage internal splitting and keep the
heading with the beginning of its following paragraph.

Word output uses `reference.docx`, based on Pandoc's default reference styles.
Normal body styles explicitly enable Widow/Orphan control while allowing long
paragraphs to split. Heading 1 through Heading 9 additionally enable Keep with
next and Keep lines together. This keeps multiline headings intact and attached
to following content. Word's standard widow/orphan setting is a boolean rather
than a configurable numeric line count; it normally prevents a single isolated
first or last line. The settings do not glue entire body paragraphs together.

For future style edits, modify the relevant paragraph styles in
`report/reference.docx`, preserving their existing names. The same defaults apply
to both the build helper and direct Pandoc commands. Final page breaks depend on
the output renderer, fonts, tables, and available page space; inspect a rendered
PDF/Word document before submission.

## Filter integration tests

```shell
uv run pytest tests/pytests/test_report_diagrams.py -q
```

These use synthetic cached images to check captions, cache invalidation,
line-ending normalization, HTML embedding, and Word/LaTeX image handling.
They require Pandoc but do not invoke Java or contact a rendering service.

## References

- [Pandoc Lua filters](https://pandoc.org/lua-filters.html)
- [PlantUML Smetana layout](https://plantuml.com/smetana02)
- [Official Pandoc releases](https://github.com/jgm/pandoc/releases)
- [Official PlantUML releases](https://github.com/plantuml/plantuml/releases)
- [Eclipse Temurin](https://adoptium.net/temurin/releases/)

## Sprint 3 figures

The two cross-trial figures referenced in `sections/07-results.md` are kept in
`figures/` and regenerated from the pinned Sprint 3 `review/families.csv` and
`review/directed_pairs.csv` files with:

```shell
uv run python report/figures/generate_sprint3_figures.py
```

The script reads the three saved trials and does not select families, scan
artifacts, or modify trial outputs. `pandas` and `matplotlib` are required.
