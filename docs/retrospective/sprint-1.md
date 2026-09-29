# Sprint 1 Retrospective

**Project:** CSC 580 Group Project – Mining AI-Native Software Engineering  
**Team:** Team 8  
**Sprint:** Sprint 1 – Research Framing and Data Foundation  
**Sprint Dates:** September 17 – October 7, 2026  
**Status:** Working draft for team review

> Detailed technical decisions are recorded separately in `docs/decisions/`. This retrospective focuses on what the team learned during Sprint 1, what changed as a result, and what we should carry forward.

## Sprint Goal

The goal of Sprint 1 was to confirm that our research question could be answered with the GitSkills dataset and to establish the data foundation needed for the rest of the project.

For our team, that meant understanding the dataset, defining the records we would study, creating a manageable sample, building an initial data-loading and exploration workflow, and organizing the work in GitHub.

## What We Accomplished

- Selected **Question 4: Skill Security and Supply-Chain Risk**.
- Explored the GitSkills dataset to determine whether the original question could be answered with the available data.
- Documented the main tables, fields, filters, and assumptions used by the project.
- Built an initial DuckDB/Python workflow for loading, filtering, and exploring the data.
- Generated exploratory tables and visualizations from code.
- Created a smaller working sample for development and review.
- Set up the GitHub Project board, Sprint 1 milestone, issues, branches, and pull-request workflow.
- Began recording important research and technical decisions in Research Decision Records (RDRs).

Some of the tools we built during Sprint 1 go beyond the minimum Sprint 1 requirements. We found that limited implementation was necessary to test our assumptions, inspect real examples, and determine whether our planned approach was workable.

## What We Learned

### 1. We can keep the original research question

Early in the sprint, we were concerned that GitSkills did not contain enough historical information to answer Question 4 as written. In particular, the dataset does not contain every version of every `SKILL.md` file.

Because of this, we considered simplifying the research question. After exploring the data, however, we found enough repeated and related artifacts, dates, repository information, and other clues to continue with the original question.

We therefore decided **not to change the research question**.

The important limitation is that we cannot always prove that one skill was copied directly from another or that the earliest skill we observe is the true original. Our analysis must clearly distinguish what the data shows from what we infer.

### 2. Finding possible related skills is easier than proving how they are related

Many skills share the same name or similar content. This gives us a practical way to find possible comparison candidates without comparing every record in the database with every other record.

However, a matching name or similar text is not enough by itself to prove that one skill came from another. We learned that we need several pieces of evidence before treating two skills as an earlier/later comparison.

This became one of the most important methodological lessons from Sprint 1: **finding possible matches and proving a meaningful relationship are two different problems.**

### 3. A useful working sample needs to be small enough to inspect

Our first sampling approach expanded to roughly 1,400 artifact-selection rows. That was too large for the kind of careful inspection we needed during Sprint 1.

We revised the sample to a smaller, purposeful set of **43 artifacts across 10 skill families**. This gave us enough variety to exercise the workflow while keeping the sample manageable for review.

The lesson was that a Sprint 1 sample does not need to represent the entire dataset. Its purpose is to help us verify that the data path, tools, and research approach work before applying them more broadly.

### 4. Simple text rules can produce misleading results

Exploratory work showed that text-based security scanning needs context.

For example:

- a command or tool name can appear in descriptive text without being an instruction to run it;
- metadata at the top of a skill file can contain tool names that should not automatically be treated as behavior;
- non-English text should not be excluded simply because some of our detection rules use English words;
- formatting differences can sometimes create artificial differences if the input is not normalized first.

These findings helped us identify where later validation will be important.

## What Changed During Sprint 1

The biggest change was **our understanding of how to answer the question**, not the question itself.

At the start of the sprint, incomplete history looked like it might make Question 4 impractical. By the end of the sprint, we had a workable approach for identifying possible related skills and using the available evidence carefully rather than requiring complete version history.

We also made several practical changes:

- Reduced the working sample after the original sample became too large for useful manual review.
- Changed from relying on a single clue, such as name or date, to combining multiple kinds of evidence when comparing skills.
- Added decision records so important choices, assumptions, and limitations would be preserved.
- Updated backlog items as exploratory work revealed new data and methodology needs.
- Started some implementation work earlier than the sprint schedule strictly required because working tools were necessary to test feasibility and make sound research decisions.

## What We Should Carry Forward

- Keep a clear distinction between **observed evidence** and **our interpretation of that evidence**.
- Prefer leaving a relationship uncertain rather than forcing an earlier/later conclusion that the data does not support.
- Use small, purposeful samples when developing or validating the method before running broader analysis.
- Treat scanner matches as signals that require validation, not automatic proof of risky behavior.
- Continue recording important research decisions when new evidence changes our assumptions or approach.
- Keep the backlog flexible enough to reflect what we learn from the data, rather than assuming every technical question can be planned in advance.

## Team Input Before Finalizing

Each team member should review this draft and add anything important that is missing.

- [ ] Add an important lesson from Sprint 1.
- [ ] Add any major challenge or blocker that affected the team's work.
- [ ] Confirm that the changes described above match what actually happened.
- [ ] Add any decision from Sprint 1 that should influence later work.
- [ ] Remove or revise anything that does not reflect the team's current understanding.

## Summary

Sprint 1 gave the team a much clearer understanding of both the GitSkills dataset and the limits of the evidence it provides. We confirmed that the original research question can remain in place, but we also learned that related skills cannot be identified or ordered using a single field or simple assumption.

The team responded by building enough tooling to test the approach, reducing the working sample to something manageable, documenting important decisions, and becoming more careful about the difference between what the dataset directly shows and what we infer from it.

Those lessons give us a stronger foundation for the implementation, validation, and broader analysis that follow.
