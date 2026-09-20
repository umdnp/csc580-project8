# Motivation

GitSkills artifacts can contain instructions that direct AI agents to execute commands, access or modify files, communicate with external services, invoke scripts, or handle credentials. These behaviors are often legitimate and necessary, but they are security-relevant because carrying them out could affect a system, its data, or external resources.

Skills may also be modified over time or reused across repositories. During that process, security-relevant instructions may be added, removed, or altered. A modified skill could introduce command execution, file-system access, network access, script use, credential handling, or another consequential behavior that was not present in an earlier version or related source artifact.

Studying these changes can provide evidence about how security-relevant behavior evolves within GitSkills and whether reuse or modification introduces new risk signals. A reproducible analysis can also help developers and reviewers identify changes that may warrant closer security review.

This topic also has personal relevance to the team because two members are pursuing cybersecurity concentrations. It provides an opportunity to apply security-focused coursework to an emerging software-engineering problem while developing practical experience in threat identification, static analysis, and responsible interpretation of security evidence.


# Expected Contribution

This project is expected to produce:

1. A documented taxonomy of security-relevant instruction patterns, including command execution, file-system operations, external network access, script use, and credential-related instructions.
2. A reproducible, rule-based static-analysis pipeline for detecting those patterns in GitSkills artifacts without executing untrusted instructions or scripts.
3. A reproducible method for identifying and comparing related skill artifacts across versions or reuse relationships.
4. An analysis showing whether security-relevant instruction patterns are introduced, removed, retained, or modified between earlier or source artifacts and later or related artifacts.
5. Empirical measurements describing the prevalence of each defined pattern and the frequency with which new patterns appear during observed skill evolution or reuse.
6. A validation and reporting approach that documents detection limitations, relationship uncertainty, ambiguous cases, and false positives while distinguishing observable risk signals from confirmed vulnerabilities or malicious behavior.

Together, these contributions will provide a repeatable method for examining both the presence and evolution of security-relevant instructions in GitSkills artifacts.