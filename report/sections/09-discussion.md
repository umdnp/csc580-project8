# Discussion

## What the automated results suggest

The three Sprint 3 trials identify candidate introductions of security-sensitive behavior in **63 of 300 sampled families**. This provides an initial answer to the research question: the defined changes are observable in related agent-skill artifacts. It does not yet establish that the scanner is correct in every case, that the selected direction is the true history of copying, or that any skill is malicious. Independent human validation remains necessary.

The difference between family-level and pair-level rates is important. The family-level results are **25%, 18%, and 20%** across trials, whereas comparison-level results are **17.0%, 5.7%, and 22.2%**. A small number of families, especially `cso` and `mcp-builder`, generate many related comparisons. Counting every comparison equally can give those families much more influence than families with only one or two usable relationships. The sensitivity analysis in Section 7 shows that this is not a minor reporting choice. Family-level frequency, chosen in RDR-013, better describes how widely the automated findings appear across our **selected** families.

## Why the distinctions in the method matter

The scanner recognizes more changes than the indicator assessor supports: **1,119 comparisons were flagged**, but only **340** met the criteria for at least one supported RI. This is intentional. A changed package-manager command, for example, can be real evidence without establishing new external-code acquisition. Conversely, the `python-executor` case introduces an explicit remote download-and-execute operation even though network-dependent installation was already present in the base. Both examples illustrate why the result must describe *what changed*, rather than assuming every changed command increases risk.

The most widely observed indicators involve **local script execution (39 families)** and **external code or dependency acquisition (26 families)**. These patterns are relevant to supply-chain review because they can change which code an agent is directed to run or obtain. Other indicators are concentrated: destructive or privileged file operations appear in only ten families but in 159 comparisons, many involving the same few families. We should not treat those repeated observations as independent security incidents.

## Alternative explanations and limits

Many changes may reflect intended features, routine maintenance, or a different environment rather than unwanted exposure. Larger families offer more opportunities to observe changes; some contain many similarity clusters and may group unrelated skills sharing a name. Some content differences are directed through chronology, while others rely on weaker structural containment. Missing supporting-file text can also hide or limit interpretation of script behavior.

These limitations do not erase the observed changes. They define what we can responsibly say about them. The contribution is a reproducible process for locating and explaining potentially consequential changes, along with direction and coverage evidence that a reviewer can inspect. Manual review will determine how reliably those candidates satisfy the study's definitions and may change the final interpretation.
