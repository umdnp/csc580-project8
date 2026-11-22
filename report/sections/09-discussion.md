# Discussion {#sec-discussion}

## What the findings mean for skill reuse

**A skill's name tells developers what it claims to do, not everything it may ask an agent to execute.** Our findings show why that distinction matters: the scanner identified candidate security-sensitive changes in **63 of 300** selected families, most often involving local script execution and external code acquisition. These changes can affect which scripts an agent runs, where it obtains code, and which external services it contacts. When adopting or updating a skill, those are the details worth checking, even if its advertised purpose has not changed.

As expected, the study found both changes meeting our security-indicator criteria and other flagged differences. The pipeline flagged **1,119 comparisons**, but only **340** supported at least one defined RI. The remaining **779** flagged comparisons include other differences and uncertain evidence; they cannot automatically be classified as harmless. This distinction reinforces why finding changed text is not the same as establishing a security-sensitive change.

A change in behavior does not necessarily make a skill less secure. A new helper script may support a legitimate feature, and the agent's permissions affect what it can actually do. Risk can also shift: replacing an online dependency with a bundled copy reduces reliance on that source but leaves questions about the copy's integrity. Our scanner cannot decide which arrangement is safer. For an adopter, the useful question is *what changed, and is that change appropriate for this environment?*

## Why the unit of analysis matters

A single family can produce many related comparisons, sometimes repeating the same underlying evidence. We therefore report how many **families** contained an indicator as our primary result. The dominant-family sensitivity check in [Section VI](#sec-results) supports that choice.

## Practical value and remaining uncertainty

For each comparison, the pipeline preserves the changed operation, its source location, the basis for direction, and any evidence gaps. This gives a developer or security reviewer a starting point for checking a modification. The `python-executor` example in [Section V](#sec-method) shows how a specific new instruction can be examined in context.

Individual findings may reflect intended features, routine maintenance, different environments, or unrelated artifacts sharing a name. Comparison direction and supporting-file evidence are also sometimes uncertain. As [Section VII](#sec-evaluation) explains, adjudication found both missed and unsupported detections, and strict eligibility excluded some known errors from the accuracy metrics. The findings give reviewers **specific changes worth checking**.
