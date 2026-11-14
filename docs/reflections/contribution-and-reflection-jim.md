# Individual Contribution and Reflection — Jim Prantzalos (`@umdnp`)

**CSC 580 · Group 8 · November 2026**

Throughout the project, I contributed to research planning, dataset preparation, core analysis tools, experiments, and the final report and presentation. I also served as Product Owner, managed our GitHub project, and helped integrate and troubleshoot work across the codebase.

## Research, data, and design

- Led GitSkills dataset acquisition and documentation, including setup, licensing, and the data dictionary. [#29](https://github.com/umdnp/csc580-project8/issues/29)
- Built DuckDB creation scripts and analysis tables for artifact grouping, deduplication, and similarity queries.
- Co-defined the comparison approach and research sample, including eligibility filters, selection criteria, and data-quality limitations. [#30](https://github.com/umdnp/csc580-project8/issues/30)
- Authored numerous research decision records, plus architecture, design, and workflow documentation.
- Consolidated NotebookLM research into a sourced elicitation matrix with follow-up questions.
- Developed and refined threats-to-validity documentation covering provenance, measurement, scanner coverage, and interpretation limits. [#34](https://github.com/umdnp/csc580-project8/issues/34)

## Artifact comparison and security analysis

- Developed the initial static scanner and contributed to expanded detection rules and automated tests. [#32](https://github.com/umdnp/csc580-project8/issues/32), [#94](https://github.com/umdnp/csc580-project8/issues/94)
- Developed artifact-family comparison and provenance analysis, including relatedness, lineage, chronology, and direction. [#93](https://github.com/umdnp/csc580-project8/issues/93)
- Built evidence extraction, normalization, and comparison to identify introduced, removed, and retained behavior. [#95](https://github.com/umdnp/csc580-project8/issues/95)
- Introduced evidence-based risk indicators and assessment, improving how security-sensitive changes are evaluated and reported.
- Expanded detection of network operations, installations, staged execution, and Python source context; reduced false positives and added regression tests.
- Added and optimized sibling-artifact scanning, including changed-content and missing-file comparisons, and protected reports with secret redaction.

## Notebooks, pipeline, and SkillTrace

- Authored many of the project's research notebooks, covering dataset exploration, cohort analysis, and experiments.
- Built and refactored the consolidated end-to-end pipeline, integrating artifact comparison, scanning, validation outputs, and reporting.
- Developed batch scanning, cohort summarization, and reusable command-line options for analysis tools.
- Extended SkillTrace with artifact differencing, including side-by-side and intraline comparisons and usability improvements.
- Added security and evidence scanning to SkillTrace, including risk-indicator comparisons and sibling-artifact support.
- Improved `family_picker` with database-driven eligibility, deduplication, reusable sampling logic, and saved cohorts.
- Optimized DuckDB queries, sibling retrieval, scan caching, and runtime performance; investigated dependency regressions.

## Validation support and experiments

- Supported manual validation through protocol, annotation-template, and reviewer-guidance improvements.
- Evaluated validation findings and corrected defects, including missed indicators, false positives, and related regression tests. [#207](https://github.com/umdnp/csc580-project8/issues/207)
- Ran and analyzed the 30-family baseline, summarizing findings by family and risk indicator. [#208](https://github.com/umdnp/csc580-project8/issues/208)
- Benchmarked primary-edge versus all-edge scanning and ran three seeded 100-family trials, preserving selections, configurations, timing, and results. [#209](https://github.com/umdnp/csc580-project8/issues/209)

## GitHub repository and team coordination

- Set up and managed the GitHub repository and Project board, including repository structure, development setup, branch protection, and pull-request safeguards. [#35](https://github.com/umdnp/csc580-project8/issues/35), [#45](https://github.com/umdnp/csc580-project8/issues/45)
- Served as Product Owner, maintaining sprint backlogs, assignments, estimates, milestones, and priorities. [#104](https://github.com/umdnp/csc580-project8/issues/104)
- Built and maintained backlog import/export scripts and Sprint 2–3 planning workflows.
- Integrated teammates' contributions and investigated cross-component bugs, failing tests, and compatibility issues.
- Maintained README files, tooling guides, setup instructions, and reproducibility documentation.
- Recorded meeting minutes, sprint retrospectives, blockers, and AI-use documentation. [#36](https://github.com/umdnp/csc580-project8/issues/36), [#105](https://github.com/umdnp/csc580-project8/issues/105)

## Research report and presentation

- Co-authored and extensively revised the final research report, including methodology, results, interpretation, limitations, and conclusions. [#211](https://github.com/umdnp/csc580-project8/issues/211)
- Developed and refined report figures and tables, including the pipeline diagram and Sprint 3 visualizations.
- Improved report production across PDF, HTML, and DOCX, including layout, SVG figures, references, and pagination.
- Contributed substantially to the presentation slide deck, including its introduction, research narrative, and supporting examples. [#215](https://github.com/umdnp/csc580-project8/issues/215)

## Personal Reflection

One of the most valuable things I gained from this project was a much deeper appreciation for the complexity of cybersecurity, particularly the new challenges introduced by AI-native software. Before this project, I had never fully considered the security implications of AI agents following instructions written in natural language. Traditional static analysis benefits from the predictable syntax and structure of programming languages. AI skills, however, can describe potentially risky behavior through free-form text, where meaning depends heavily on context and interpretation. Identifying actionable instructions within that text is difficult enough in English, but considering the many languages in which these instructions can be written makes the problem considerably more challenging. This project opened my eyes to an entirely new dimension of software security that I had previously given little thought to.

Initially, I questioned whether our research question was even practical to address within a semester. The scope of "other risky behavior" was not clearly defined, and the GitSkills dataset lacked the complete historical versions we expected to need for identifying modified or reused skills. We seriously considered narrowing our research question to something more manageable. However, our early exploration revealed enough information to pursue an alternative approach, using similarities between artifacts and available commit metadata to infer relationships and possible changes over time. Even that approach introduced new challenges, particularly when historical information was missing or insufficient to establish a reliable direction of change. Each solution seemed to reveal another complication we hadn't anticipated.

Perhaps the most important lesson was realizing that a problem doesn't have to be solved perfectly for meaningful progress to be possible. At first, the ambiguity of natural language and the limitations of the dataset made reliable security analysis seem almost unattainable. Through our research, however, we demonstrated that carefully designed static analysis can still identify useful security-sensitive indicators and changes between related artifacts. The results require careful interpretation, and false positives, missed detections, and uncertain relationships remain unavoidable concerns. Nevertheless, imperfect analysis can still provide valuable evidence. I learned that understanding and communicating those limitations is just as important as developing the tools themselves.

Looking back, I'm glad we chose to retain the original research question rather than simplify it simply to make the project easier. We recognized early on that it would be challenging, but decided that confronting those challenges would provide a more valuable learning experience. That decision required considerable experimentation, problem-solving, collaboration, and a willingness to reconsider our assumptions as new evidence emerged. By working through the difficulties instead of avoiding them, I gained a far greater understanding of the problem than I would have otherwise.

Ultimately, this project changed how I think about software security and research in general. It reinforced the importance of persistence, critical thinking, and approaching uncertain problems with an open mind. More importantly, it gave me a new appreciation for the security challenges emerging as AI systems become increasingly capable of interpreting and acting on human language. These are difficult problems with no simple solutions, and I now have a much better understanding of both the risks they present and the opportunities for developing meaningful ways to address them.
