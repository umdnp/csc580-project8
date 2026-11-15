# Individual Contribution and Reflection — Vaisnavii Mohanraj (`@vaisnaviim`)

**CSC 580 · Group 8 · November 2026**

Throughout the project, I contributed to research planning, threat-model development, data preparation, exploratory analysis, the integrated analysis pipeline, reproducibility documentation, manual validation, and team coordination. My work covered all three sprints and included both technical implementation and the communication needed to keep the project moving.

## Research planning and threat model

- Participated in selecting Research Question 4 and helped define the project's focus on potentially risky changes rather than proving that artifacts were malicious. This decision was documented in the [September 13 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-09-13-meeting-minutes.md).
- Reviewed the initial Markdown backlog and provided feedback about scope, story structure, assignments, and project requirements. I also helped clarify backlog expectations with the instructor, as recorded in the [September 13 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-09-13-meeting-minutes.md).
- Defined the initial threat model and detection categories for command execution, file-system access, network access, credential handling, bundled or invoked scripts, and other risky behavior in [Story 1.2](https://github.com/umdnp/csc580-project8/issues/28).
- Documented the project's trust boundary: dataset content is untrusted, and commands, scripts, URLs, and helper files from the dataset must not be executed or contacted in [`THREAT_MODEL.md`](https://github.com/umdnp/csc580-project8/blob/main/THREAT_MODEL.md).
- Added examples, likely false positives, detection rules, scope boundaries, and interpretation limits in [`THREAT_MODEL.md`](https://github.com/umdnp/csc580-project8/blob/main/THREAT_MODEL.md).
- Revised the threat model as the analysis evolved, including explicit script-detection guidance. This work was reviewed through [PR #56](https://github.com/umdnp/csc580-project8/pull/56) and [PR #61](https://github.com/umdnp/csc580-project8/pull/61).

## Data setup and exploratory analysis

- Set up DuckDB and the local GitSkills analysis environment on macOS, including troubleshooting the shared `GITSKILLS_DB` environment-variable configuration. This work is described in the [October 5 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-10-05-meeting-minutes.md).
- Built the initial SKILL.md comparison notebook and extraction workflow for the approved sample in [Story 2.3](https://github.com/umdnp/csc580-project8/issues/31).
- Created the initial comparison notebook in [`skill_md_comparison.ipynb`](https://github.com/umdnp/csc580-project8/blob/main/notebooks/extraction_pipeline/skill_md_comparison.ipynb).
- Documented the extraction workflow, database setup, generated outputs, tests, and reproduction steps in [`extraction_pipeline/README.md`](https://github.com/umdnp/csc580-project8/blob/main/notebooks/extraction_pipeline/README.md).
- Loaded the approved sample from DuckDB in read-only mode, preserved source identifiers and repository metadata, and compared artifacts within skill-name groups.
- Added validation and skip handling for incomplete records and saved extracted comparison data in machine-readable formats.
- Ran the initial exploratory analysis and generated comparison outputs, risk-category summaries, and figures for the Sprint 1 review in [Story 3.2](https://github.com/umdnp/csc580-project8/issues/33).
- Created a notebook-based workflow for manually inspecting results and identifying possible false positives, false negatives, and scanner-rule gaps, as discussed in the [September 28 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-09-28-meeting-minutes.md).
- Used static text analysis only, keeping the pipeline safe from execution of commands or scripts embedded in the dataset.
- Moved and organized the extraction pipeline under the notebooks directory through [PR #126](https://github.com/umdnp/csc580-project8/pull/126).

## Sprint 2 pipeline and results

- Facilitated the Sprint 2 backlog review and helped clarify story dependencies, blockers, acceptance criteria, and assignments. This work is documented in the [October 11 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-10-11-meeting-minutes.md).
- Built the Sprint 2 end-to-end analysis pipeline in [Story 5.4](https://github.com/umdnp/csc580-project8/issues/96).
- Generated and documented preliminary analysis results, including analyzed and excluded artifacts, detected security signals, artifact comparisons, and security-sensitive changes in [Story 7.1](https://github.com/umdnp/csc580-project8/issues/101).
- Produced reproducible tables and figures with explicit sample sizes and denominators in [Story 7.2](https://github.com/umdnp/csc580-project8/issues/102).
- Created the Sprint 2 results documentation in [`sprint2/README.md`](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/results/sprint2/README.md), which was submitted through [PR #186](https://github.com/umdnp/csc580-project8/pull/186).
- Added documentation describing the generated figures and their interpretation in [`end_to_end_pipeline/README.md`](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/README.md), reviewed through [PR #187](https://github.com/umdnp/csc580-project8/pull/187).
- Troubleshot the SkillTrace and DuckDB configuration so the visualization and artifact-review tools could access the correct local database, as documented in the [October 25 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-10-25-meeting-minutes.md).
- Contributed to the final result documentation for the final sample, directed comparisons, risk indicators, validation results, primary-versus-all-edge comparisons, and seeded random-family runs in [Story 10.3](https://github.com/umdnp/csc580-project8/issues/210).
- Kept observations separate from interpretations: scanner matches and detected changes were reported as static evidence, not proof of malicious intent, compromise, or runtime behavior.

## Validation and limitations

- Manually inspected representative GitSkills artifacts and used those inspections to identify scanner gaps, missed behaviors, and possible false positives.
- Used the existing manual annotation protocol and previous review files as references when completing the Sprint 3 sample 3 validation work. The assignment of sample 3 is documented in the [November 8 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-11-08-meeting-minutes.md).
- Submitted relationship-pair review annotations in [`relationship_annotations.csv`](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/sprint3/results3/manual-review/relationship-pairs/relationship_annotations.csv) through [PR #241](https://github.com/umdnp/csc580-project8/pull/241).
- Submitted directed-pair review annotations in [`annotations.csv`](https://github.com/umdnp/csc580-project8/blob/main/notebooks/end_to_end_pipeline/sprint3/results3/manual-review/directed-pairs/annotations.csv) through [PR #243](https://github.com/umdnp/csc580-project8/pull/243).
- Completed independent review annotations for Sprint 3 relationship-pair and directed-pair samples, including relatedness, chronology uncertainty, scanner judgments, coverage, and indicator-level observations. The related work is tracked in [Story 9.2](https://github.com/umdnp/csc580-project8/issues/206).
- Reviewed flagged, unflagged, uncertain, incomplete, and missing-evidence cases rather than considering only positive findings.
- Contributed to the final limitations work in [Story 11.2](https://github.com/umdnp/csc580-project8/issues/212).
- Helped document purposeful sampling, measurement error, false positives, missed detections, incomplete source evidence, uncertain provenance and direction, dependent comparisons, reproducibility constraints, and limits on generalization in [`THREATS_TO_VALIDITY.md`](https://github.com/umdnp/csc580-project8/blob/main/THREATS_TO_VALIDITY.md) and [`report/sections/10-threats-to-validity.md`](https://github.com/umdnp/csc580-project8/blob/main/report/sections/10-threats-to-validity.md).
- Helped preserve the distinction between an inferred relationship and proven copying, and between a static risk indicator and a confirmed security incident.

## Team coordination and project process

- Participated in early discussions about research scope, backlog organization, story assignments, sprint timing, and technical responsibilities. These discussions are recorded in the [September 13 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-09-13-meeting-minutes.md), [September 20 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-09-20-meeting-minutes.md), and [September 28 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-09-28-meeting-minutes.md).
- Facilitated the Sprint 2 backlog meeting and helped the team identify dependencies between scanner development, sample selection, pipeline integration, validation, and report preparation.
- Communicated setup issues and blockers early, especially problems involving DuckDB, notebook environments, SkillTrace, and shared configuration.
- Took responsibility for documenting how to reproduce Sprint 2 analysis outputs, tables, and figures, as recorded in the [October 11 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-10-11-meeting-minutes.md).
- Coordinated with teammates through story acceptance criteria, meeting discussions, Discord communication, and the manual-review protocol.
- Prepared a draft for the separate product-scenario/UML assignment and shared it with the team for review, as documented in the [November 8 meeting minutes](https://github.com/umdnp/csc580-project8/blob/main/docs/meeting-minutes/2026-11-08-meeting-minutes.md).
- Supported the team by clarifying course requirements and sharing instructor responses about unclear assignments.

## Personal Reflection

This project changed how I think about both software security and research with imperfect data. At the beginning, it was tempting to treat a detected command, URL, or credential reference as evidence that an artifact was dangerous. Working through the threat model and extraction pipeline showed me that static analysis is more useful when it is precise about what it can observe and equally precise about what it cannot prove. A textual match can identify a review signal, but it does not establish execution, intent, or impact.

One of the most challenging parts of the project was turning loosely structured natural-language skill files into evidence that could be compared consistently. SKILL.md files vary widely in organization and writing style, and historical metadata is not always enough to establish which artifact came first. Building the extraction and comparison workflow forced me to think carefully about identifiers, missing records, source traceability, environment configuration, and reproducibility. I learned that a reliable result is not just a number produced by a notebook; it also requires a clear sample definition, documented exclusions, preserved inputs, and a way to trace the number back to the original artifacts.

The project also taught me how important communication and coordination are in technical work. My pipeline depended on scanner, sample-selection, and comparison components being completed by other team members. This required discussing blockers, clarifying acceptance criteria, documenting setup problems, and making sure the team used consistent samples and configuration. Facilitating the Sprint 2 backlog helped me understand how dependencies and unclear requirements can affect an entire research workflow.

The integrated pipeline showed me the importance of connecting components without losing meaning between them. Loading, extraction, comparison, scanning, and result generation each work differently, and a complete workflow can still produce misleading evidence if the populations, denominators, or direction assumptions are not carried forward. Documenting the outputs and reviewing them manually helped me understand why research software needs both automated checks and human interpretation.

Manual validation was especially valuable because it exposed the gap between a scanner's output and a defensible conclusion. Some findings were supported, some were uncertain, and some required examining surrounding context before deciding whether the detector had identified a real change. Reviewing ambiguous relationships reinforced that uncertainty should be preserved rather than hidden. It is better to report that chronology or coverage is insufficient than to make a confident claim that the evidence does not support.

My biggest takeaway is that meaningful security research does not require pretending that the available evidence is perfect. It requires building a process that is safe, reproducible, transparent about limitations, and useful for directing further review. I gained practical experience with notebooks, data pipelines, static analysis, validation datasets, environment configuration, documentation, and team coordination. More importantly, I learned that careful uncertainty handling is not a weakness in an analysis. It is part of what makes the analysis trustworthy.