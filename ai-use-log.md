# AI Use Log

This log summarizes where the team used AI assistance during the CSC 580 Group 8 project and how we checked the resulting work. It complements the disclosure in [Appendix F](report/appendices/F-disclosures.md), rather than replacing the underlying code, tests, saved research artifacts, or individual contribution statements.

| Project phase | AI-assisted activity | Human checks and retained evidence |
| --- | --- | --- |
| Inception and elicitation | Helped formulate interview questions, explore dataset documentation, and organize requirements and research ideas, including NotebookLM-assisted elicitation. | Team reviewed the sources and recorded its own interpretations, decisions, and follow-up checks under `docs/requirements/` and `docs/decisions/`. |
| Scanner and pipeline development | Helped brainstorm approaches, draft or revise code and tests, explain errors, and refine commands, evidence comparison, and risk-indicator behavior. | Team inspected and revised implementation, ran automated tests and controlled examples, and recorded engineering decisions in the repository. |
| Data exploration and Sprint 3 analysis | Helped formulate SQL and Python analyses, inspect summaries, and check the presentation of trial results and figures. | Saved family lists, manifests, settings, trial outputs, and generated figures remain the source of numerical results; AI suggestions did not replace the frozen data. |
| Manual validation and adjudication | Assisted with explaining annotation fields, suggesting review questions, and examining potential scanner errors. | Reviewers inspected actual skill and sibling-file evidence, preserved the independent annotations, and approved final adjudicated judgments. AI-generated notes were not treated as independent human review. |
| Report and presentation | Assisted with wording, organization, layout, consistency checks, and speaker-note revisions. | Team checked claims against saved results and the research report, rebuilt the PDF, and reviewed the presentation and presenter notes. |
| Reproducibility documentation | Helped identify stale instructions and explain how the saved trial analyses differ from later adjudication-only processing. | The team completed clean-environment reproduction of all three Sprint 3 trials. Saved manifests, family lists, and research summaries provide comparison points; adjudication-only updates and scanner changes are tracked separately. |

## Responsibility and disclosure

The team remains responsible for research choices, security interpretations, code integration, tests, manual judgments, citations, and the final report. AI-assisted text, analyses, or implementation suggestions were reviewed before inclusion. No instructions or scripts from the untrusted GitSkills dataset were executed for this study.

This is a **project-level summary of documented AI use**, not a complete per-prompt transcript or a substitute for the individual reflections. See [Appendix F](report/appendices/F-disclosures.md), the [research decision records](docs/decisions/), and the [individual contribution and reflection files](docs/reflections/) for additional context.
