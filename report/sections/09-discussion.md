# Discussion

## What the findings mean for skill reuse

A reused skill may look familiar while containing instructions or supporting files that have changed. That is the supply-chain concern behind our research question: **an adopter may encounter security-sensitive operations that were not present in a related earlier observed artifact**. Across the three trials, the scanner found candidate changes in **63 of 300 sampled families (21.0%)**. This shows that the defined indicators occur across the selected families, but it does not establish direct copying, malicious behavior, or actual execution. Independent manual validation is still underway.

The most widespread indicators involved **local script execution (39 families)** and **external code or dependency acquisition (26 families)**. At least one of these appeared in **52 of the 63 indicator-bearing families**. These changes matter because they can affect which scripts or outside code an agent is instructed to use. Their presence does not necessarily mean a skill is dangerous: the same instructions may be legitimate for its task, and an agent's permissions may limit what it can do. The relevant question for a reviewer is what operation changed, where it came from, and whether that change is appropriate in the intended environment.

Our evidence comparison helps narrow that review. The scanner flagged **1,119 comparisons**, but only **340** met the more specific criteria for a supported risk indicator. For example, switching package managers can change a command without introducing a new dependency-acquisition operation. The `python-executor` example in Section 6 shows the contrasting case: a later observed skill includes a direct remote-script execution command. Both examples illustrate why simply counting command or URL matches would overstate what the analysis can establish.

## Why we report findings by family

We chose the family as our primary reporting unit because several comparisons can share artifacts or repeat the same evidence. The sensitivity check in Section 7 shows the effect: excluding one influential family from each trial changed the pair-level detection rate from **15.8% to 8.4%**, while the family-level rate changed only from **21.0% to 20.2%**. Family-level reporting better describes how widely these automated findings occur *within our sample*. It does not make the sample representative of all GitSkills or resolve uncertainty about relationships.

## Practical value and remaining uncertainty

The pipeline is intended to support **review of changes**, not to assign a security score to a skill. It retains the detected operation, the supporting evidence, the basis for comparison direction, and any missing information so a reviewer can judge the finding in context. This could help developers and security reviewers prioritize changes to check when adopting or updating skills.

There are other reasonable explanations for many findings: ordinary feature additions, maintenance, different operating environments, or unrelated skills that share a name. In some comparisons, earlier/later ordering relies on weaker clues, and some supporting-file contents are unavailable. The manual reviews will test whether the selected relationships and indicator judgments hold up. Until then, the findings show **where the method identifies potential supply-chain concerns**, not how often those concerns become real security incidents.
