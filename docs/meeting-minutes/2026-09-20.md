# CSC 580 Group 8 – Meeting Minutes

**Date:** September 20, 2026  
**Time:** 11:00 AM EDT  
**Duration:** Approximately 55 minutes  
**Attendees:** Jim Prantzalos, Vaisnavii Mohanraj, Kyle Cantrell, Christian Heiney  
**Purpose:** Review project progress, clarify upcoming coursework, introduce project documentation and development conventions, and review the initial approach for identifying risky changes in GitSkills artifacts.

## Main Topics of Discussion

- Welcomed Christian to his first full team meeting and reviewed the current state of the project.
  - The team has selected **Research Question 4**.
  - Sprint 1 work is being managed through GitHub Projects.
  - Project code, documentation, notebooks, figures, and other artifacts are being maintained in the GitHub repository.
  - Christian will be added as a repository contributor so he can participate directly in project development.

- Reviewed the separate group assignment due Wednesday.
  - The portions of the assignment that were struck out by the instructor do not need to be completed.
  - The primary requirement is to interact with the shared NotebookLM notebook and document selected questions, responses, team interpretations, and follow-up observations.
  - The NotebookLM notebook was successfully shared using an **anyone with the link** setting.
  - Shared notebook users can access the common source material, although individual NotebookLM conversation histories remain private to each user.
  - Each team member should ask approximately **2–5 relevant questions** using NotebookLM.
  - Team members will send their selected interactions to Jim.
  - Jim will consolidate the team responses into the group submission.

- Reviewed new workflow diagrams added to the repository.
  - Diagrams have been created for the overall project workflow and for the individual sprints.
  - Diagrams are stored in both Draw.io and SVG formats.
  - SVG versions can be viewed directly through GitHub.
  - Draw.io versions can be opened and modified using Draw.io.
  - The diagrams are intended to clarify how the project work and deliverables are divided across the three sprints.

- Reviewed the use of **Research Decision Records (RDRs)**.
  - Major project decisions should be documented using a standardized RDR format.
  - The first RDR documents the team's discussion and decision to retain Research Question 4 rather than revise it.
  - Potential future RDR topics include:
    - The similarity method used to identify related skills.
    - Selection and definition of scanner rules.
    - Other decisions that materially affect the project's methodology or direction.
  - A template and instructions for creating RDRs are available in the repository.
  - Generative AI may be used to help create an RDR from team discussions, provided the resulting document is reviewed for accuracy.

- Reviewed exploratory data analysis work.
  - Jupyter notebooks have been added to the repository for initial exploration of the GitSkills dataset.
  - Notebook output can be viewed in GitHub when the notebook has been executed and saved with its results.
  - Team members may modify or extend the existing notebooks.
  - A `GITSKILLS_DB` environment variable can be used to specify the local database path.
  - This prevents machine-specific database paths from being hard-coded into shared notebooks and code.

- Reviewed the Python project structure and development conventions.
  - Core Python source code is maintained under the project's source directory.
  - Command-line tools should remain relatively lightweight.
  - Reusable application logic should reside in modules/classes rather than being embedded directly in CLI tools.
  - This allows the same scanner, comparison, and analysis functionality to be reused from command-line utilities and Jupyter notebooks.
  - The project uses `pyproject.toml` rather than a traditional `requirements.txt` file for project configuration and dependencies.
  - Script aliases can be defined in `pyproject.toml` to make utilities such as `scan_diff` easier to execute.
  - `uv` was recommended as an option for managing Python environments and dependencies.

- Reviewed the initial `scan_diff` utility, scanner architecture, and rule framework.
  - The scanner compares a **base artifact** against a **derived artifact** to identify security-sensitive behavior that appears in the derived artifact but not in the base.
  - Scanner results can identify:
    - Rules matched in the base artifact.
    - Rules matched in the derived artifact.
    - Differences in the number of matches.
    - Whether potentially risky behavior appears to have been introduced or removed.
  - Synthetic base/derived artifact examples have been created as initial test cases.
  - A generic base rule abstraction has been created.
  - A regular-expression-based rule implementation currently supports the initial detection rules.
  - Initial rule categories include:
    - Command execution.
    - File-system access.
    - Network access.
    - Credential-related behavior.
  - Individual rules are assigned identifiers such as command or network rule IDs.
  - The current rules are an initial **straw-man implementation** intended to support discussion and refinement rather than a final rule set.
  - Additional rule implementations can be created later if certain behaviors cannot be reliably detected using regular expressions.
  - Regular expressions may identify text that describes a risky command without actually instructing an agent to execute it.
  - Comments, examples, documentation, and other contextual uses may therefore produce false positives.
  - The team will need to evaluate whether regular expressions are sufficient for each rule category and document known false-positive behavior and other limitations.

- Clarified the intended purpose of the scanner.
  - The project is **not** attempting to build an antivirus or comprehensive malware-detection product for `SKILL.md` files.
  - The scanner is intended to support analysis of the GitSkills dataset and help quantify how frequently potentially risky behavior appears or is introduced.
  - Scanner findings should be treated as indicators of potentially risky behavior rather than definitive proof that an artifact is malicious.
  - The effectiveness and limitations of the detection rules will be part of the analysis.

- Discussed validation using real GitSkills artifacts.
  - The synthetic test cases are useful for initial development but do not represent real-world repository data.
  - Real examples should also be extracted from the GitSkills dataset.
  - Base and derived artifacts can then be run through the scanner to determine:
    - Whether expected risky behaviors are detected.
    - Whether behaviors are missed.
    - Whether false positives occur.
    - Whether existing rules need to be modified.
    - Whether additional rules are required.
  - Extracted real-world examples can be stored using a similar base/derived test directory structure.

- Clarified the scope of the threat-model story.
  - The Sprint 1 threat-model work is primarily a **definition and documentation task**, not an implementation task.
  - The threat model should document the initial security-sensitive categories and candidate detection rules that will guide scanner development.

- Reviewed the research-question documentation.
  - The team will continue with the original wording of **Research Question 4** rather than revising the question.
  - The research-question documentation should also explain the team's motivation for selecting the question.
  - Kyle has already created a pull request containing motivation and expectations documentation.
  - The motivation may be included with the research-question documentation or maintained within the related documentation area.

- Reviewed local use of the GitSkills dataset with DuckDB.
  - Repository documentation includes instructions for configuring and using the local DuckDB copy of the dataset.
  - DuckDB provides substantially faster access to the dataset than the previous approach.
  - The source dataset is approximately 40 GB, and the initial import can take a significant amount of time.

- Discussed the initial approach for identifying potentially reused or derived skills.
  - Skills can initially be grouped using their **name and description**.
  - Matching repositories can then be compared using commit information to help establish a base artifact for comparison.
  - The earliest observed artifact may be used as the base for analysis, but this should not be treated as proof that it is the historical original.
  - Exact description matching is currently being used as an initial approach.
  - Similarity techniques such as Jaccard similarity may be explored later if exact matching proves too restrictive.
  - Exact file duplicates can be excluded from change analysis because no content changed between copies.
  - Very small artifacts may also be excluded from analysis where there is insufficient substantive content to evaluate.
  - The identified base/derived pairs will eventually provide the input to the scanner and subsequent analysis.

- Clarified Sprint 1 timing for Christian.
  - The separate group NotebookLM assignment is due Wednesday.
  - **Sprint 1 itself is due October 7, 2026.**
  - Christian will review the project documentation, previous meeting material, and his assigned Sprint 1 work as his schedule permits.
  - Team members will use Discord for questions and additional discussion between meetings.

## Decisions and Outcomes

- **Research Question 4 will remain unchanged.**
- The motivation for selecting Research Question 4 will be documented as part of the project documentation.
- Major methodological or project-direction decisions will be documented using **Research Decision Records (RDRs)**.
- Shared Python tools will use a modular architecture in which reusable logic is separated from command-line interfaces.
- `pyproject.toml` will be used for Python project configuration and script entry points.
- Local database locations will be handled through the `GITSKILLS_DB` environment variable rather than hard-coded paths.
- The existing regex-based rule framework will be treated as an initial implementation and refined as the team evaluates real examples and false positives.
- The Sprint 1 threat-model work will document the security-sensitive categories and candidate detection rules that will guide scanner development.
- The scanner will identify **potentially risky behavior**, not classify artifacts as definitively malicious or safe.
- Synthetic test cases will be supplemented with real-world samples extracted from the GitSkills dataset.
- Exact file duplicates will be excluded from introduced-behavior scans because their content is unchanged.
- Name and description matching will serve as an initial method for finding potentially related skills, with more sophisticated similarity methods considered if necessary.
- Discord will continue to be used for questions, follow-up discussions, and coordination between meetings.

## Action Items

### Jim

- [ ] Add Christian as a contributor to the GitHub repository.
- [ ] Consolidate the team's NotebookLM interactions into the group assignment submission.
- [x] Add the September 20 meeting minutes to the project repository.

### Vaisnavii

- [ ] Complete approximately 2–5 relevant NotebookLM questions/interactions and send the selected material to Jim.
- [ ] Develop the Sprint 1 threat-model documentation, including the initial security-sensitive categories and candidate rule areas.
- [ ] Review the current scanner rules and consider additional behaviors that should be represented in the threat model.

### Kyle

- [ ] Complete approximately 2–5 relevant NotebookLM questions/interactions and send the selected material to Jim.
- [ ] Complete/revise the research-question motivation and expectations documentation associated with the current pull request.
- [ ] Post remaining project questions to Discord for team discussion.

### Christian

- [ ] Complete approximately 2–5 relevant NotebookLM questions/interactions and send the selected material to Jim.
- [ ] Review the previous meeting minutes and current project documentation to become familiar with the work completed to date.
- [ ] Review the GitHub Project and assigned Sprint 1 story/work.

### All Team Members

- [ ] Review the workflow diagrams and current repository structure.
- [ ] Review the initial scanner rules and identify potential missing cases or false positives.
- [ ] Document significant methodological decisions using the RDR format when they arise.
- [ ] Use real GitSkills artifacts to help validate and refine the detection approach.
- [ ] Continue project questions and technical discussions through Discord between meetings.
