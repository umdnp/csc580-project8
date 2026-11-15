# Individual Contribution and Reflection — Kyle Cantrell

**CSC 580 · Group 8 · November 2026**

I served as Scrum Master and contributed to the study design, GitSkills sampling, static scanner, automated tests, and manual validation. I also helped document how to reproduce the analysis and revised the research report as the methods and results developed. [Team roles](https://github.com/umdnp/csc580-project8#team-and-roles)

Jim led much of the project’s development, and his technical expertise was central to what we delivered. I worked closely with him throughout the project, talking through designs, weighing implementation options, and helping work out how to turn research goals into concrete steps. That collaboration was a regular part of my contribution alongside the tools, tests, and validation work I owned.

## Research, data, and design

- Selected the team’s research question on security-sensitive changes in reused AI-agent skills and helped determine whether we could answer it with the artifact relationships and history available in GitSkills. I drafted the motivation, expectations, and study design, and documented a competing explanation for the findings. [Research question](../../RESEARCH_QUESTION.md), [PR #54](https://github.com/umdnp/csc580-project8/pull/54), [PR #55](https://github.com/umdnp/csc580-project8/pull/55), [PR #67](https://github.com/umdnp/csc580-project8/pull/67)
- Co-defined the comparison approach and research sample with Jim. My part was to work out how to select families with enough variation for comparison while keeping the sample manageable for manual review. I authored RDR-006 to document the selection rationale, wrote the SQL to select candidate families, and created the 43-artifact Sprint 1 sample and its reproducible notebook view. [Comparison and sampling story](https://github.com/umdnp/csc580-project8/issues/30), [PR #120](https://github.com/umdnp/csc580-project8/pull/120), [RDR-006](../decisions/RDR-006-sprint1-sample-design-and-selection.md)
- Created Family Picker to select my own samples and later added seeded sampling and configurable family-size groups and allocations. Jim and I jointly developed the stratified sampling method documented in RDR-014. He implemented the non-overlap requirement and selected the families for the three Sprint 3 trials. [PR #129](https://github.com/umdnp/csc580-project8/pull/129), [PR #218](https://github.com/umdnp/csc580-project8/pull/218), [RDR-014](../decisions/RDR-014-stratified-family-sampling-method.md)
- Authored RDR-011, which documents how I corrected description whitespace normalization so equivalent descriptions would group together. [RDR-011](../decisions/RDR-011-description-whitespace-normalization.md)

## Artifact comparison and security analysis

- Built the initial tool for visualizing artifact lineage. Jim developed the idea further into SkillTrace. I also wrote a utility that passed artifact-family analysis results into the pairwise scanner. [Lineage prototype](https://github.com/umdnp/csc580-project8/commit/c44e929), [Family-to-scanner utility](https://github.com/umdnp/csc580-project8/commit/1bb9e0b)
- Wrote and tested `FS-003`, the static scanner rule for file-reading commands and APIs. I also expanded other scanner rules and updated the threat model to map rules to the behaviors under study. [Rule changes](https://github.com/umdnp/csc580-project8/commit/42ac259), [FS-003 test](https://github.com/umdnp/csc580-project8/commit/0da5e9e), [Threat-model update](https://github.com/umdnp/csc580-project8/commit/175f51c)
- Added handling for missing or malformed artifact content so individual invalid records would not stop the analysis. [PR #157](https://github.com/umdnp/csc580-project8/pull/157)

## Automated testing and reproducibility

- Set up pytest and wrote most of the project’s automated tests, including coverage for Sprint 1 extraction, data preparation, artifact matching, and similarity comparisons. I tested threat-model coverage and verified that the analysis tools treat dataset content as data without executing it. [PR #66](https://github.com/umdnp/csc580-project8/pull/66), [PR #145](https://github.com/umdnp/csc580-project8/pull/145), [Data preparation tests](https://github.com/umdnp/csc580-project8/commit/82b8def), [PR #171](https://github.com/umdnp/csc580-project8/pull/171), [PR #158](https://github.com/umdnp/csc580-project8/pull/158)
- Added end-to-end coverage for the pipeline, notebook, and security comparisons, and fixed Sprint 3 test regressions involving the CLI, scan cache, and plotting in headless environments. [Pipeline tests](https://github.com/umdnp/csc580-project8/commit/9b5ca58), [PR #228](https://github.com/umdnp/csc580-project8/pull/228)
- Created the project’s Start Guide, which walks readers through the analysis tools using an example artifact pair. [PR #153](https://github.com/umdnp/csc580-project8/pull/153)
- Documented how to reproduce the Sprint 1 notebook output and created Mermaid diagrams of the pipeline for team review. [PR #140](https://github.com/umdnp/csc580-project8/pull/140), [PR #151](https://github.com/umdnp/csc580-project8/pull/151)

## Manual validation and experiments

- Reviewed and annotated examples from the Sprint 1 scanner output, then completed manual validation of the Sprint 2 sample, including directed comparisons and relationship pairs. [Sprint 1 review](https://github.com/umdnp/csc580-project8/commit/97d533b), [PR #192](https://github.com/umdnp/csc580-project8/pull/192)
- Completed manual validation of the Sprint 3 Trial 1 results. I documented whether the evidence supported the reported relationships, directions, and risk indicators. [PR #235](https://github.com/umdnp/csc580-project8/pull/235), [PR #254](https://github.com/umdnp/csc580-project8/pull/254)
- Ran an exploratory scan across qualifying GitSkills artifact families in restartable batches and shared the scan files and summary outputs with Jim. We discussed how to reuse the scans for cohort-level risk-indicator summaries, how to compare primary-edge and all-edge results, and how the broader findings might complement the Sprint 3 results.
- Reviewed a teammate’s Sprint 3 directed-pair annotations and flagged a sibling-only case in which the evidence for the risk indicators appeared in the sibling files. I shared the finding with Jim before the team summarized the validation results.

## Scrum and team coordination

- Served as Scrum Master, helped run team meetings, and guided the other developers through sprint work and review deadlines. I recorded the September 28 meeting notes and contributed to the Sprint 1 retrospective. [September 28 meeting notes](../meeting-minutes/2026-09-28-meeting-minutes.md), [PR #146](https://github.com/umdnp/csc580-project8/pull/146)
- Recommended sharing the Sprint 3 manual review across the team. I demonstrated how to locate assigned pairs in SkillTrace and use the annotation templates, and proposed a shared deadline so the findings could feed into the final report. [November 2 meeting notes](../meeting-minutes/2026-11-02-meeting-minutes.md), [November 8 meeting notes](../meeting-minutes/2026-11-08-meeting-minutes.md)

## Research report

- Co-authored the final research report with Jim and the team. I created the report structure and maintained it through Sprints 1 and 2. My writing covered the research framing, dataset preparation, methodology, validation, results, and threats to validity. I also added diagrams for data preparation, artifact relationships, and the family-scanning workflow. [PR #58](https://github.com/umdnp/csc580-project8/pull/58), [PR #154](https://github.com/umdnp/csc580-project8/pull/154), [Final report story](https://github.com/umdnp/csc580-project8/issues/211)
- Streamlined the main report and moved detailed methods, validation materials, extended results, and reproducibility information into appendices. [PR #193](https://github.com/umdnp/csc580-project8/pull/193)
- Reviewed the final report draft with Jim and flagged missing figure and table references, table numbering and formatting issues, and language that needed updating after manual validation.

## Personal Reflection

I had fun working through the engineering problems on this project from beginning to end. I'm a Project Manager for a software team. I don't get a lot of hands-on experience with the software design process, even though I am regularly a part of the process in my work. I have gained a greater appreciation for the tasks that I regularly ask my team to accomplish. I have realized the challenges that go into software design and creation, and had fun trying to solve the engineering problems along the way.

Our group's major hurdle was determining if the original research question was even answerable with the provided dataset. The biggest hurdle was determining an artifact lineage, which would be the basis for determining evolution over time. The original lineage assessment seemed like an easy answer of "this question is unanswerable", so we worked out how to revise the question into something achievable. However, with some tenacity and further analysis, Jim and I (mostly Jim) were able to develop a clever yet logical way to establish a lineage with the data we had available. I learned a lot about requirement design, analysis and research, and the benefit of building tools to help make informed decisions. I also got my first direct experience with databases in this phase.

Over the course of the project I got to experience first-hand the challenges that go into a software project. I learned things like the importance of documentation (which I kind of already knew), but I also learned that too much documentation with spread out information can be a hindrance. I learned a lot about the value of unit testing; especially when the tests were failing after a change. Either the test needs to change to match the new design, or the design needs to change to keep the test passing. Even though I didn't write a notebook, I was given exposure to them and came to appreciate their value. To say I learned a lot this semester would be an understatement. Gaining first-time hands-on experience with the many different facets of this project only helped to grow my development skillset. I feel like I have more tools to work with now.

I’ll bring my experience back to my work as a project manager. When I ask my team to implement a change, I have a better sense of the work behind it; from clarifying what the change should do to deciding what to test and where to document the decision. I also have better questions to ask when the team is working through a design, especially when the requirements or the evidence are ambiguous or leave room for assumptions.