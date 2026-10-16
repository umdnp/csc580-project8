\clearpage

# Evaluation and Validation

## Evaluation Objectives

Evaluation separates three questions: whether extraction preserves the intended inputs, whether relatedness and direction are supported, and whether scanner findings correspond to the operational rule definitions. A correct count on an incorrectly ordered pair is not a valid introduction finding. A plausible relationship does not establish that a rule accurately captures the intended behavior. The broader census and manual-review plans remain distinct from the implemented test suite and illustrative local runs.

## Independent Database Reconstruction

Team members independently downloaded `agent_skills_release.db` and executed the project SQL queries on their own machines. The team reports that these independent runs accurately reproduced the results. This is a completed cross-machine reproducibility check of the data-preparation workflow, separate from automated scanner tests and the planned manual validation of lineage and security findings.

This observation supports repeatability in the tested setups. The available team account does not specify a per-field comparison protocol, so it is not presented as a documented exhaustive comparison of every artifact-to-ID mapping. A reproducibility record should preserve the dataset checksum, query revision, DuckDB version, and compared outputs alongside this observation.

## Automated Tests

The shared runner `tests/pytests/test_sample_skills.py` discovers JSON expectations under `tests/pytests/test_configs`, loads matching base and derived `SKILL.md` files, and invokes the `scan_diff` entry point. It checks successful completion, introduced-category membership, total base/derived match counts and their delta, and the full nonzero rule-delta mapping. This tests the file-input, scanning, comparison, and JSON-output path together.

A local verification at code revision `f2b4c7d` on October 15, 2026 passed all seven configured sample cases using:

```shell
uv run pytest tests/pytests/test_sample_skills.py -q
```

This result describes that test selection, not a claim that all project tests passed or that the scanner achieves a population-level accuracy target. Systematic tests for similarity boundaries, provenance conflicts, missing chronology, cycle avoidance, and incomplete sibling coverage are additional validation needs.

## Constructed Test Fixtures

Constructed cases isolate recognizable changes rather than reproduce the distribution of real-world artifacts. The configured cases cover command/network introductions, file-system/system-modification introductions, credential introduction, external-code introduction, an unchanged-capability control, frontmatter-only changes, and file-reading behavior. The frontmatter case checks that metadata does not create a behavioral finding; the control checks that expected unchanged behavior remains unchanged.

Expected outputs are assertions about the current rules. Passing them demonstrates regression consistency, not independent proof that the rules capture every intended behavior. Additional fixtures should cover removal, equal counts with different instructions, overlapping patterns, formatting variants, and unrecognized syntax. Dataset-derived examples must be labeled separately from constructed fixtures.

## Sprint 1 Sample as a Tool-Validation Dataset

### Purpose and Selection

Sprint 1 used 43 dataset artifacts across ten exact-name families to exercise the developing tools on real collected content. RDR-006 records why the team replaced an earlier roughly 1,400-row mixed selection with this compact purposeful sample: a manageable set could be inspected in context while preserving multiple artifacts per family. Screening sought package-installation variation, supported source-metadata fields, and variation in additional scanner rules. These heuristics selected informative cases; they did not establish lineage or scanner correctness.

The sample complements the constructed fixtures. Fixtures isolate an expected behavior in a small controlled input; the Sprint 1 artifacts expose combinations of metadata, repeated content, missing evidence, and instruction text that occur in the collected dataset. The sample was not randomly drawn and does not support estimates of population-wide risk prevalence.

### Two Workflows Exercised Different Parts of the Tools

The family-analysis workflow loaded the selected exact-name families, constructed skill and bundle variants, measured similarity, and attempted direction inference. The ten saved family reports contained 17 selected directed comparisons. Equivalent and ambiguous relationships remained visible without being forced into the directional scan. Selected comparisons were manually inspected in Mergely to compare reported changes with the source text. This was targeted inspection, not independent annotation of every relationship.

The extraction notebook used the same sample for a different integration task. It read `sample_artifacts` in view order, grouped by name while preserving that order, and compared each occurrence with its immediately preceding occurrence in the group. With 43 rows across ten groups, this produces 43 minus 10, or 33 adjacent comparisons: the first row in each group has no preceding row. The notebook then scanned both file bodies, recorded positive rule deltas and complete comparison JSON, wrote Parquet, reloaded it, and generated summary figures.

The 33 notebook pairs are ordering-based extraction comparisons, not the 17 edges selected by the family algorithm. Adjacency in the SQL view does not establish parentage. Their totals and positive-delta rates must therefore be reported separately, and notebook pairs must not be described as independently verified parent-child relationships.

### What the Sample Tested

| Tool behavior | How Sprint 1 exercised it | What the check can establish |
| --- | --- | --- |
| Candidate loading and grouping | Load multiple occurrences per exact name, including description variants | Whether the tools preserve the candidate context needed for comparison |
| Content and bundle representation | Compare repeated or differing skill states and available sibling fingerprints | Whether skill and bundle state are distinguished; unknown sibling evidence is not proof of equality |
| Similarity and direction reporting | Examine supported direction, equivalent peers, ambiguity, and cases without directed edges | Whether the tools expose their evidence and avoid forcing every candidate into a parent-child pair |
| Scanner and comparator output | Inspect positive, negative, or unchanged counts and category-introduction flags | Whether existing signals, count changes, and introduced categories are distinguished on selected cases |
| Extraction and output integration | Run the notebook from sample view through paired scans, Parquet, and figures | Whether stages can exchange and preserve the expected fields and result structures |
| Failure investigation | Inspect source diffs and retained formatting/coverage cases | Whether unexpected counts can be traced to inputs or rule behavior and turned into regression checks |

The earlier inspections exposed uneven recognition of equivalent operations and artificial count differences associated with line endings. The earlier wrapper was corrected and the formatting case retained for regression checking. The saved Sprint 1 reports showed delta variation in ten of the then-current twelve rules, while EXT-001 and SYS-001 lacked confirmed delta examples in that selection. These observations identify useful coverage and gaps; they do not provide a measured precision or recall for the current thirteen-rule catalog.

### Automated Support and Evidence Limits

`tests/pytests/test_extraction_pipeline.py` exercises the notebook's loader, validation, adjacent pairing, positive-delta accounting, and Parquet round trip against a temporary DuckDB fixture. These automated checks complement the dataset-based notebook run without requiring the full dataset. They verify implementation behavior rather than independently validating the sample's inferred ancestry or security significance. A local verification on October 15, 2026 passed all 21 extraction-pipeline test cases, using a writable temporary directory for the fixture database and generated files. The test selection can be run with `uv run pytest tests/pytests/test_extraction_pipeline.py -q`.

The saved notebook output can establish which comparisons were produced and how their scan results were summarized. It does not establish that every pair was manually reviewed, that the current rules match the definitions used in the saved run, or that findings generalize beyond this selected sample. Saved-run outcomes are reported separately in Results. Broader relationship review, scanner error estimation, and the planned population census remain additional evaluation tasks.

## Manual Validation Sample

The planned broader review comprises at least 100 eligible comparisons, divided initially between at least 50 with a reported rule/category introduction and at least 50 without one, as described in Dataset and Data Preparation. This review has not been established as completed. Before selection, the team must freeze the run, define relationship/category strata, record a random seed, and document allocation and replacement when a stratum is too small. Count increases within existing rules should be identified separately from introductions when constructing these strata.

## Annotation Protocol

The proposed protocol records two separate judgments per comparison. First, reviewers inspect candidate scope, similarity, provenance and chronology evidence, direction basis, and unresolved alternatives. Second, they inspect both file bodies and the relevant match locations, checking whether each reported rule and introduced category is supported. For sibling findings, reviewers also check which destination resources changed and whether either endpoint lacks required content.

Review records should distinguish supported findings, unsupported matches, missed in-scope patterns, uncertain direction, and incomplete inputs. Disagreements should retain both initial judgments and an adjudicated explanation. The number of reviewers, independence procedure, and final annotation form remain to be specified before claiming reviewer agreement.

## Validation Measures

For independently reviewed findings, precision is supported positive findings divided by all reviewed positive findings under the operational labeling protocol. Recall requires an independently annotated set of actual in-scope positives, including missed findings; reviewing only scanner hits cannot estimate it. A balanced or stratified review sample does not directly estimate population prevalence without accounting for selection probabilities.

Relationship support and direction agreement should be reported separately from scanner correctness. Ambiguous and incomplete cases require their own counts rather than automatic assignment as negatives. No numerical precision, recall, or reviewer-agreement result is claimed here before the corresponding annotations exist.

## Error Analysis

Error analysis should distinguish candidate-generation failures, source-resolution failures, ordering uncertainty, missing content, syntax coverage gaps, documentation-only matches, and formatting sensitivity. Fixes must be checked against frozen regression cases and affected analyses rerun. The earlier Sprint 1 inspections motivated a line-ending correction; that historical observation does not establish that all formatting or rule-coverage issues have been resolved.

## Risk-Signal Interpretation Disclaimer

A detected risk signal indicates that a skill contains an instruction pattern identified as security-relevant by the project's current rule catalog. It does not prove that the skill is malicious, vulnerable, exploitable, or unsafe.

Likewise, an introduced risk signal means that the scanner detected a rule or category in the derived artifact that it did not detect in the corresponding base artifact. This is a comparison of static artifact content, not evidence that the instruction was executed or caused harm.

The available evidence may not establish:

* whether the instruction is executable in the intended environment;
* whether an agent or user ever executed it;
* whether execution requires user approval or additional permissions;
* whether security controls would prevent or restrict the behavior;
* whether a referenced file, script, command, credential, or network resource is harmful;
* whether the behavior creates an exploitable condition; or
* whether the artifact's author intended malicious behavior.

Many legitimate skills require commands, file operations, network access, scripts, or authentication instructions to perform their intended functions. The project will therefore describe scanner findings as **security-relevant capabilities**, **risk signals**, or **patterns requiring review**. Terms such as **malicious**, **vulnerable**, and **exploitable** will be used only when supported by additional evidence beyond a static rule match.
