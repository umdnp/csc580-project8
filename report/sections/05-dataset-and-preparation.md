# Dataset and cohort

## Source and candidate construction

The study uses GitSkills version 1.0.0, released on Zenodo on August 10, 2026. The dataset records 3,797,117 skill-file occurrences collected from public GitHub repositories in July 2026 and retains occurrences separately from distinct content [@gitskills]. The project imports the released SQLite data into a local DuckDB database for analytical queries. The imported file is a prepared analysis artifact, not the original SQLite download.

Candidate construction requires valid frontmatter, a body longer than 50 characters, non-null content/name/description, and an exact name shared by at least two qualifying occurrences. Artifacts missing any of these attributes were considered unusable to meet the research question's intent.

Description text is normalized for subgrouping, but family analysis loads all qualifying description groups for the chosen name. These filters make comparisons feasible while excluding short, malformed, unnamed, or singleton artifacts that could still contain consequential instructions. They are eligibility criteria, not evidence of safety or copying.

A historical preparation audit on October 15 retained 943,257 candidate occurrences in 162,995 exact-name families. Those audit counts document an earlier local build and are not the denominator for the present cohort results. Appendix A preserves the SQL, cumulative selection counts, and build-local identity limitations. The current saved manifest identifies the cohort inputs and settings; the entire candidate population has not been established as analyzed.

## Saved exploratory cohort

The results below describe the saved `sprint2` end-to-end  pipeline output, inspected on October 26, 2026. Its manifest labels the selection **provisional**, with no approval reference. Thirty exact-name families were supplied, and the pipeline loaded 1,151 artifacts without skipping an artifact input. Family names span development, scientific, infrastructure, and security-oriented tasks. Selection was not established as random or representative, so a cohort percentage must not be presented as the prevalence of risk in GitSkills.

The run analyzes all supported primary and additional directed edges within the selected families. Primary edges are the chosen predecessor relationships; additional edges retain other supported comparisons. It records 3,997 analyzed directed pairs and 2,244 ambiguous edges excluded from directional scanning. These are graph-comparison counts rather than counts of unique modifications. Families can differ greatly in size, content repetition, direction evidence, and contribution to the totals.

## Evidence availability and handling

Skill bodies are available for the loaded artifacts, but availability of chronology and sibling content varies. A known empty sibling state differs from an unknown or truncated listing. Missing resources cannot be assumed absent historically, and an unmatched rule cannot compensate for unavailable source. The report presents input loading, extraction coverage, and sibling coverage separately because each describes a different boundary.

All dataset content is treated as untrusted text. The pipeline does not execute embedded commands, install referenced dependencies, clone repositories to complete missing records, or retrieve linked instructions. Aggregate tables and schematic examples are sufficient for the report; raw dataset content and credential values are not redistributed. Reproduction depends on the frozen source identities and hashes, not on numeric artifact IDs alone, because IDs can be reassigned in another database build.
