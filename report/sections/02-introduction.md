# Introduction

Adopting a familiar agent skill can introduce unfamiliar instructions. A reused file may preserve its name and most of its text while adding a downloader, changing a remote code source, or expanding a file operation. Reviewing only the skill description, the presence of a capability, or the total number of scanner matches can miss the change that matters to the adopter.

The Agent Skills format combines a Markdown instruction file with optional scripts, references, and assets [@agentskills]. That structure makes the file body and its associated resources relevant to a review. A script can change without changing the instruction that invokes it. Conversely, a new example or additional documentation can increase matches without introducing a new operational requirement. The security question is therefore comparative and contextual: what changed between related artifacts, and does the change satisfy an explicit reason for review?

The study addresses that question through static analysis of the GitSkills dataset [@gitskills]. The pipeline separates three decisions: whether two artifacts are meaningfully related, whether an earlier/source-to-later ordering is defensible, and whether changed evidence supports one of eleven risk indicators. A URL reference, a rule-count increase, and a supported risk indicator are distinct observations. None alone establishes malicious intent or execution.

The report presents the comparison method, eleven indicators, exploratory results, and validation requirements. Appendices retain preparation queries, implementation details, validation materials, extended results, and supporting repository resources.
