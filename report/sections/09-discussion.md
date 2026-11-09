# Discussion

## What the findings mean for skill reuse

Our results suggest a practical reason to review a reused skill beyond its name and stated purpose: **related artifacts can contain different instructions about what an agent should run, obtain, or access**. The scanner identified candidate security-sensitive changes in 63 of 300 selected families. The most widespread indicators concerned local script execution and external code acquisition. Both can change the code an agent is directed to use, sometimes through resources controlled outside the project that adopted the skill.

A detected change is not necessarily an unsafe change. A new helper script may support a legitimate feature, and whether an instruction runs depends partly on the agent's tools and permissions. The useful question for an adopter is more specific: *What changed, and is that change appropriate for this environment?* Our method helps locate that question by comparing operational evidence instead of counting every new command or URL reference as a risk indicator.

## Why the unit of analysis matters

A single family can produce many related comparisons, sometimes repeating the same underlying evidence. We therefore report how many **families** contained an indicator as our primary result. The dominant-family sensitivity check in Section 7 supports that choice within our sample. It does not make the findings representative of every skill in GitSkills.

## Practical value and remaining uncertainty

For each comparison, the pipeline preserves the changed operation, evidence for its source and direction, and any coverage gaps. This makes the output useful for a developer or security reviewer deciding which modifications need closer inspection. The `python-executor` example in Section 6 shows the level of detail a review can examine without claiming that an instruction was executed or that its author was malicious.

There are also reasonable alternative explanations for individual findings, including intended features, routine maintenance, different deployment environments, and unrelated artifacts sharing a name. Some comparison directions rely on indirect evidence, and some supporting-file content is missing. Manual validation will test the selected relationships and indicator judgments. Until that work is complete, the findings establish **candidate changes worth checking**, not the rate of confirmed security incidents.
