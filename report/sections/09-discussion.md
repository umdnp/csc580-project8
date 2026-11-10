# Discussion {#sec-discussion}

## What the findings mean for skill reuse

Our results suggest a practical reason to review a reused skill beyond its name and stated purpose: **related artifacts can contain different instructions about what an agent should run, obtain, or access**. The scanner identified candidate security-sensitive changes in 63 of 300 selected families. The most widespread indicators concerned local script execution and external code acquisition. Both can change the code an agent is directed to use, sometimes through resources controlled outside the project that adopted the skill.

A change in behavior does not necessarily make a skill less secure. A new helper script may support a legitimate feature, and the agent's permissions affect what it can actually do. Risk can also shift: replacing an online dependency with a bundled copy reduces reliance on that source but leaves questions about the copy's integrity. Our scanner cannot decide which arrangement is safer. For an adopter, the useful question is *what changed, and is that change appropriate for this environment?*

## Why the unit of analysis matters

A single family can produce many related comparisons, sometimes repeating the same underlying evidence. We therefore report how many **families** contained an indicator as our primary result. The dominant-family sensitivity check in [Section VI](#sec-results) supports that choice within our sample. It does not make the findings representative of every skill in GitSkills.

## Practical value and remaining uncertainty

For each comparison, the pipeline preserves the changed operation, its source location, the basis for direction, and any evidence gaps. This gives a developer or security reviewer a starting point for checking a modification. The `python-executor` example in [Section V](#sec-method) shows how a specific new instruction can be examined in context.

There are also reasonable alternative explanations for individual findings, including intended features, routine maintenance, different deployment environments, and unrelated artifacts sharing a name. Some comparison directions rely on indirect evidence, and some supporting-file content is missing. Manual validation will test the selected relationships and indicator judgments. Until that work is complete, the findings establish **candidate changes worth checking**, not the rate of confirmed security incidents.
