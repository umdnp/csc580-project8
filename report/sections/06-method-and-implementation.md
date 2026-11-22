# Method {#sec-method}

## Research approach and security scope

To assess what changed, we must first decide which skills are related and which artifact could have come earlier. GitSkills provides snapshots and some repository and commit metadata, but **not a complete version history or verified copying relationships**. Some commit dates are missing; even a recorded first commit at the current path may be later than the skill's origin. We therefore infer plausible comparison directions rather than reconstructing a proven family tree.

Our threat model focuses on observable instructions or code involving command execution, network access, file-system operations, credentials, external code or dependency acquisition, and system modification. These operations matter because an agent following untrusted instructions may have tools that affect a user's machine, data, or external services. The full threat model describes the trust boundary and what our scanner covers.

## Analysis overview

[Figure 1](#fig-analysis-pipeline) shows the four stages in order. We establish relatedness and a plausible direction **before** examining changed operations; otherwise, a difference alone could be mistaken for an introduced behavior.

![Four stages of the static comparison process: group candidates, match and order, compare operations, and assess risk indicators.](report/figures/analysis-pipeline.svg){#fig-analysis-pipeline width="100%" .here}

## Step 1: Identify related skills

Two skills can share a name but contain completely different instructions. Before looking for newly introduced behavior, we therefore check whether they are similar enough to compare. We start with same-name candidates and use file hashes to identify identical `SKILL.md` content. A separate fingerprint records the known state of supporting files. This matters because identical instructions can ship with different scripts; when supporting-file content is unavailable, we do not assume the bundle is empty.

For distinct `SKILL.md` contents, we compare the body text after masking the opening YAML frontmatter. We normalize and tokenize the text, then form **five-token shingles**: sequences of five consecutive tokens. Comparing sets of these short sequences tolerates some formatting changes while retaining important command and identifier structure.

We consider two skill variants sufficiently similar when they share at least **five shingles**, have a maximum **containment score of at least 0.80**, and have a **Jaccard similarity of at least 0.30**. Containment asks how much of the smaller shingle set appears in the larger one; Jaccard measures the shared shingles relative to all distinct shingles across both texts. For example, if two files have 100 and 150 shingles, with 85 shared, containment is `85 / 100 = 0.85` and Jaccard is `85 / 165 = 0.515` (approximately 0.52). In simpler terms, the two skills must share most of the smaller text **and** a meaningful portion of their combined text. This helps us recognize an expanded skill without treating a small shared passage as evidence that otherwise different skills are related. The added material may contain the behavior we seek.

The analyzer groups related artifacts into **similarity clusters**. Variants can belong to the same cluster through intermediate matches, so membership does not mean that every pair meets the similarity thresholds directly. An exact shared name is therefore only a starting point: a large family can contain several clusters of differently written skills. The thresholds are documented operational choices, not probabilities of copying.

## Step 2: Infer which artifact could come first

After establishing that two artifacts are related, we determine which could have come first. We evaluate five types of direction evidence in priority order: declared source, direct chronology, equivalent-peer chronology, repository-creation boundaries, and directional containment. [Table 2](#tbl-direction-priority) explains each method and its limitations.

| Priority | Direction evidence | What it establishes—and what it does not |
| --- | --- | --- |
| 1 | **Declared source** | Supported provenance metadata identifies a source; declarations can still be wrong or incomplete. |
| 2 | **Direct chronology** | `first_commit_at` records when a state was observed at its current file path, not its true original creation date. |
| 3 | **Equivalent-peer chronology** | A different occurrence of the *same known `SKILL.md` content and sibling-file state* supplies an earlier observed date when direct history is missing or later. The date belongs to the state, not automatically to the undated occurrence. |
| 4 | **Repository-creation boundary** | If one state was observed before another repository existed, that other repository occurrence could not have been earlier. Repository age alone never dates a skill. |
| 5 | **Directional containment** | When stronger evidence is missing, substantially greater containment in one direction (difference of at least **0.10**) can suggest a plausible base-to-expanded order. This is the weakest direction signal. |

: Evidence used to infer earlier-to-later ordering, in priority order {#tbl-direction-priority} {.wide}

**Equivalent-peer chronology** helps when an artifact lacks a reliable date. If the same `SKILL.md` content and known sibling-file state were observed elsewhere at an earlier date, that observation can help order the content states. It does not tell us when the undated copy was created, and we cannot use this evidence when the sibling-file states differ or are unknown.

A **repository-creation boundary** can support ordering when one skill state was observed before another repository existed; an older repository alone proves nothing about the skill's age. When dating evidence is unavailable, **directional containment** considers whether one skill preserves most of another's text while adding material. That pattern helps infer the comparison order.

When the available evidence cannot support an ordering, we leave the relationship unresolved. Conflicting source declarations also remain unresolved, and equivalent states are retained as peers. For each directed comparison, we record the evidence used to determine its order. This allows us to distinguish comparisons supported by observed chronology from those relying on weaker evidence, such as directional containment.

The algorithm selects at most **one primary predecessor per derived candidate**, avoiding cycles. In practical terms, we compare each candidate with one selected, plausibly earlier artifact rather than every possible predecessor. Other related, directed comparisons are retained as *additional edges*. For the final three trials, we scanned **only primary edges** to reduce repeated comparisons within large families. In a controlled Sprint 2 test using the same scanner configuration, this reduced the number of comparisons from 3,997 to 468 while retaining 43 of 44 observed family–indicator combinations. These results supported our decision to use primary edges, although additional edges may still contain unique findings. We did not perform a separate all-edge comparison for Sprint 3.

## Step 3: Detect and compare observable evidence

The static scanner applies **15 detection rules across six categories** ([Table 10](#tbl-detection-rules)): command execution, network access, file-system access, credentials, external code/dependency acquisition, and system modification. These rules find recognizable operations, such as shell commands, URLs, and file access, **without executing them**. The `SKILL.md` frontmatter is excluded from behavioral scanning because metadata describing a tool does not itself instruct the agent to use it. Provenance metadata can still inform the ordering in Step 2.

We then **extract and compare evidence**, rather than interpreting a changed rule-match count as new risk. Evidence records retain the recognized operation, source location, context, and extraction completeness. We normalize the evidence for comparison while preserving meaningful command arguments, file paths, and URL details, along with the original text. The comparison distinguishes added, removed, and matching constructs. A different URL might matter even if the number of URL matches stays the same; repeated mentions can raise match counts without introducing an operation. Unclear associations remain uncertain.

Bundled **sibling files** are assessed when added or changed content is available, regardless of file extension. For instance, a skill's instructions might remain the same while the bundled `setup.sh` changes. We examine the changed script's stored content, but do not infer its behavior from a filename when that content is missing. Renaming a file without changing its known content does not count as changed script behavior.

The comparator classifies changes as `skill-only`, `siblings-only`, `skill+siblings`, or `unknown`. A **`siblings-only`** classification does not necessarily mean the `SKILL.md` files are identical: the similarity method can treat files with textual differences as equivalent. [Appendix B](#app-b) defines these classifications.

## Step 4: Assess changes against risk indicators

**Detection rules identify operations; risk indicators assess changes in those operations.** For example, a rule may recognize a command in an individual skill, but an indicator requires evidence that an operation was introduced or materially changed between two artifacts. This final stage applies **11 risk indicators (RIs)** ([Table 3](#tbl-risk-indicators)) covering exposure to external code, networks, local files, credentials, or privileged actions. Indicators do **not** assign severity scores. A rule match by itself is insufficient.

| ID | Security-sensitive change assessed |
| --- | --- |
| **RI-001** | Newly downloaded content is passed directly to an interpreter. |
| **RI-002** | The source URL of remotely executed code changes. |
| **RI-003** | A network operation uses a new hostname/domain or introduces explicit outbound transfer. |
| **RI-004** | HTTPS is downgraded to HTTP, or certificate verification is disabled. |
| **RI-005** | External code or dependency acquisition is introduced, or its source/registry changes. Package-name or version edits alone do not qualify. |
| **RI-006** | A destructive file operation is introduced or expands in scope or privilege. |
| **RI-007** | An operation newly accesses a recognized credential file or includes a credential reference directly in outbound transfer. |
| **RI-008** | An operation introduces or expands system, permission, service, or scheduled-task changes. |
| **RI-009** | A read/write operation newly targets a recognized sensitive file or directory. |
| **RI-010** | Local script execution is introduced or changes to a target with observably different content. |
| **RI-011** | A skill newly directs following external instructions, changes that source, or changes an ordinary reference into such a directive. |

: Eleven evidence-based risk indicators {#tbl-risk-indicators} {.wide}

We chose these indicators because they can be supported by **specific observable evidence** in the dataset rather than speculative runtime effects. They also reflect the plausible changes described in the threat model. An indicator may be supported, uncertain, or absent from the observed comparison. “Absent” means **not supported by available evidence**, not proven safe. One command may support several indicators without representing several separate incidents.

A simple example from scanner development is replacing `npm install` with `bun install` while preserving the same dependency-acquisition workflow. The scanner records the changed commands, but the substitution alone does not support **RI-005**: it does not show a new acquisition operation or a changed code source.

### Worked example: A changed installation instruction

The `python-executor` family provides a contrasting example from Trial 3: an installation change that meets our risk-indicator criteria. In the observed comparison **1773238 → 1729578**, the instructions change from:

**Base artifact:**

```bash
npx skills add inference-sh/skills@agent-tools
```

**Derived candidate:**

```bash
curl -fsSL https://cli.inference.sh | sh && infsh login
```

Both instructions involve acquiring software, but the derived candidate introduces a different installation method. It explicitly downloads a shell script from `cli.inference.sh` and passes it directly to `sh` for execution. The assessor reported **RI-001** because the new command passes downloaded code directly to a shell, and **RI-003** because it introduces a new hostname for an explicit network operation. Both indicators describe the same changed command, rather than separate security incidents.

Downloading and executing a script from an external website raises a supply-chain concern because the code can change independently of the skill's instructions.

## Outcomes and interpretation limits

The **primary measure** is the share of sampled families with at least one supported RI. Secondary measures cover comparison-level findings, individual indicators, family size, direction basis, and evidence coverage. A single change can support multiple indicators, so their counts are not additive.

A **flagged comparison** may contain rule changes, extracted-evidence changes, or uncertain observations even if no RI is supported. A **supported finding** meets an indicator's automated criteria. We report missing evidence and uncertainty separately. **Complete coverage** means no known gaps within the scanner's implemented extraction scope. [Appendix B](#app-b) contains the rule registry and analysis workflow; [Appendix E](#app-e) identifies the source artifacts and saved outputs used for these results.
