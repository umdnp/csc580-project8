# Research Question

## Topic

**Question 4: Skill Security and Supply-Chain Risk**

## Research Question

**Do modified or reused skills introduce command execution, file-system access, network access, or other risky behavior that was absent from an earlier version or source artifact?**

## Motivation

Agent skills can contain instructions involving commands, files, networks, scripts, and credentials. When skills are reused or modified, new security-sensitive behavior may be introduced without being obvious to someone adopting the skill.

Understanding whether this occurs in GitSkills can provide evidence about potential security and software supply-chain risks associated with sharing and modifying agent skills.

## Expected Contribution

This study will provide evidence about whether related GitSkills artifacts introduce security-sensitive behavior that was absent from an earlier or source artifact, and what types of behavior are introduced when this occurs.

## Interpretation and Feasibility

We interpret the research question as asking whether a related skill artifact contains security-sensitive behavior that was not present in an earlier or source artifact. **Other risky behavior** includes security-sensitive actions beyond command execution, file-system access, and network access, such as credential-related or script-based behavior. The presence of this behavior does not necessarily mean that a skill is malicious.

Based on our Sprint 1 exploration, we believe the GitSkills release dataset contains enough artifact content, repository information, dates, and related skill records to investigate the research question as written. The available data does not always prove that one artifact was directly copied from another or that the earliest observed artifact is the true original, so conclusions about source and modification relationships need to be made carefully.

The team's decision to retain the original research question and the alternatives considered are documented in [RDR-001](docs/decisions/RDR-001-retain-question-4-versioning-strategy.md).

## Competing Explanation

Differences in security-sensitive behavior may reflect legitimate changes in a skill's intended functionality rather than evidence that reuse or modification itself increased security risk.

## Study Definition

| Item | Definition |
| --- | --- |
| **Unit of analysis** | A comparison between two related GitSkills artifacts where the available evidence supports an earlier/source and later/modified ordering. |
| **Population** | Qualifying `SKILL.md` artifacts in the selected GitSkills release dataset and the related artifact comparisons that can be identified among them using the project's study criteria. |
| **Sprint 1 sample** | A purposeful sample of 43 artifacts across 10 skill families, producing 17 directed comparisons in the saved Sprint 1 analysis reports. The sample is intended to support feasibility and tool validation, not population-wide risk estimates. |
| **Variables** | Artifact relationship and ordering; security-sensitive behavior observed in each artifact; and whether a behavior is newly present in the later artifact. |
| **Outcome measures** | Whether newly introduced security-sensitive behavior is detected in a comparison, and the type of behavior introduced. |

## Supporting Analysis

Exploratory and sample analysis are maintained under [`notebooks/`](notebooks/). Detailed research and methodology decisions are maintained under [`docs/decisions/`](docs/decisions/).
