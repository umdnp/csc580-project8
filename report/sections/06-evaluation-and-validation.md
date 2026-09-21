\clearpage

# Evaluation and Validation

## Evaluation Objectives

[TODO: Explain which parts of the extraction, relationship identification, scanning, and comparison methods require validation.]

## Automated Tests

[TODO: Describe unit, integration, and regression tests for important pipeline behavior.]

## Constructed Test Fixtures

[TODO: Explain how intentionally created base and derived skills test known rule introductions, removals, and retained behavior.]

## Manual Validation Sample

[TODO: Define the sample size, selection method, strata, random seed, and replacement procedure.]

## Annotation Protocol

[TODO: Explain what reviewers examine and how cases are labeled.]

## Validation Measures

[TODO: Define the validation metrics used, such as true-positive counts, false-positive counts, false-negative counts, precision, recall, or agreement.]

## Error Analysis

[TODO: Describe how incorrect, ambiguous, or disputed results are examined and categorized.]

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
