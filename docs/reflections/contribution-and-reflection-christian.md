# Individual Contribution and Reflection - Christian Heiney (`@cheiney`)

**CSC 580 - Group 8 - November 2026**

My contributions focused on validation, reproducibility, and communicating the limitations of our results. I helped develop the manual-review process, contributed review annotations, evaluated scanner findings, and documented how another researcher could reproduce our analysis. I also supported report revisions and investigated practical problems encountered when running the project on Windows.

## Validation planning and methodology

- Contributed the validation sample and manual-review protocol deliverables for Story 6.2, helping establish a structured process for checking the project's automated results. [#98](https://github.com/umdnp/csc580-project8/issues/98), [#156](https://github.com/umdnp/csc580-project8/pull/156)
- Contributed to evaluating validation results and limitations, including updates to threats-to-validity documentation and supporting validation materials. [#100](https://github.com/umdnp/csc580-project8/issues/100), [#194](https://github.com/umdnp/csc580-project8/pull/194)
- Helped clarify the difference between preliminary annotations and completed human validation so that the report did not present unfinished review work as established ground truth. [#195](https://github.com/umdnp/csc580-project8/pull/195)

## Directed-pair and relationship review

- Submitted Results2 review materials covering the 30 directed-pair and 15 relationship-pair samples, then followed up with corrections to annotation text and file naming. [#244](https://github.com/umdnp/csc580-project8/pull/244), [#245](https://github.com/umdnp/csc580-project8/pull/245), [#250](https://github.com/umdnp/csc580-project8/pull/250)
- Used SkillTrace, source comparisons, and scan evidence to investigate relatedness, direction, scanner-rule matches, indicator changes, and sibling-file coverage. I used AI assistance to help organize and evaluate the review material, while retaining uncertainty where the available evidence did not support a definite conclusion.
- Compared Results2 annotations with Results1 and Results3 to identify missing fields and check consistent use of the review schema. Follow-up annotation work added evidence-specific context and more explicit judgments. [#261](https://github.com/umdnp/csc580-project8/pull/261)
- Investigated potential missed detections rather than reviewing only the indicators already reported by the scanner. One documented example was an added logging-wrapper execution workflow supporting RI-010 that was absent from the reported indicator list. I also helped distinguish such qualitative findings from cases eligible for formal precision and recall calculations.

## Reproducibility and execution support

- Documented an isolated end-to-end reproduction check, including dependency setup, fixed-cohort inputs, historical versus current-code comparisons, and figure and report regeneration. [#213](https://github.com/umdnp/csc580-project8/issues/213), [#231](https://github.com/umdnp/csc580-project8/pull/231)
- Recorded important boundaries of that check, including the use of a prepared database snapshot rather than claiming that the entire large-dataset download and import had been repeated.
- Investigated Windows and OneDrive execution problems and proposed portability and pipeline fixes. This work was submitted separately from the merged reproducibility documentation. [#230](https://github.com/umdnp/csc580-project8/pull/230)
- Added a repository ignore rule for generated SkillTrace reports to keep local inspection outputs out of version control. [#232](https://github.com/umdnp/csc580-project8/pull/232)

## Research communication and collaboration

- Supported research-report updates by documenting validation progress, unresolved review work, and limitations that affected interpretation of the results. [#194](https://github.com/umdnp/csc580-project8/pull/194), [#195](https://github.com/umdnp/csc580-project8/pull/195)
- Refined submitted review artifacts through follow-up pull requests, correcting references and keeping annotations aligned with the team's shared format.
- Connected the review process to the reporting requirements by checking which judgments were complete, which remained uncertain, and which pairs had sufficient direction and coverage evidence to contribute to metrics.

## Personal Reflection

One of the most important lessons I took from this project was that producing an automated result and establishing that the result is meaningful are different tasks. A scanner can identify a URL, shell command, or script invocation, but understanding what that observation represents requires reading its context. A documentation link is not necessarily a network operation, an example mentioning credentials is not necessarily credential exposure, and a legitimate script can still introduce a security-sensitive capability. Working through these distinctions made me more careful about separating observable behavior from conclusions about intent.

The manual-review work also showed me how much uncertainty can exist in an apparently straightforward comparison. Two artifacts can be closely related without enough evidence to establish which came first. A file appearing in one recorded snapshot does not necessarily mean it was newly created, particularly when the other snapshot is incomplete. I learned that recording uncertainty is not a failure to finish the analysis; it is an important part of making the analysis trustworthy.

Another valuable lesson came from looking beyond the scanner's existing findings. Reviewing only flagged indicators would make it easy to overlook missed behavior. Examining the underlying changes helped identify a local-execution observation that the reported indicators had missed, while other possible misses remained unresolved. This reinforced the importance of treating automated output as evidence to investigate rather than as an answer to accept.

The reproducibility work broadened my understanding of what it means for research to be repeatable. Successfully running a notebook is not enough. Another person needs to know which code revision, dependencies, dataset, configuration, and inputs produced the results. Changes in scanner behavior can also change the findings even when the cohort remains the same. Documenting those differences and the limits of the reproduction check was just as important as documenting successful execution.

Working through annotation corrections and follow-up pull requests also reinforced the value of clear communication. Review status, coverage, and adjudication fields may look administrative, but they determine what claims the team can responsibly make. AI assistance was useful for organizing evidence and checking consistency, but it did not remove the need for source-based reasoning or justify treating unresolved judgments as verified conclusions.

Overall, my contribution was to help connect the project's automated analysis with a more explicit and reproducible evaluation process. The project strengthened my ability to question results, document limitations, and communicate the difference between what the evidence demonstrates and what remains uncertain. Those habits are lessons I can apply to future software engineering and research work.

Coming from a background in Finance, learning cybersecurity-related workflows was a new frontier for me. This project challenged me to become more comfortable with unfamiliar tools, terminology, and methods for evaluating security-sensitive behavior. It also helped me connect the importance of evidence, risk assessment, and clear documentation with a new technical context.

I also had a period at the beginning of the semester when I was less available, which meant I took a more passive role in the project's initial planning. During that stage, I relied on the Scrum Master and Product Owner to help define my responsibilities and took on the tasks they assigned to me. Reflecting on that experience, I recognize the importance of communicating availability early and staying engaged with planning, even when my capacity is limited. The assigned work gave me a concrete way to contribute while building familiarity with the project's cybersecurity workflows.

### Experiencing Agile from a Different Role

In a business setting, I am more accustomed to playing a role similar to a Product Owner, helping define priorities, clarify business needs, and communicate desired outcomes. Participating in this project as a contributing team member rather than in that familiar role gave me a different perspective on the Agile framework. Instead of primarily shaping what needed to be delivered, I focused on understanding the team's priorities and translating assigned responsibilities into concrete deliverables.

This shift provided new experience with the technical work and uncertainty behind an agreed-upon requirement. It reinforced the value of clear acceptance criteria, opportunities to ask questions, and communication between those setting priorities and those carrying out the work. I can bring that perspective back to a Product Owner role with a greater appreciation for implementation challenges and the support team members need to deliver meaningful results.
