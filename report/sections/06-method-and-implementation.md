# Method

## Research approach and security scope

To assess what changed, we must first decide which skills are related and which artifact could have come earlier. GitSkills provides snapshots and some repository and commit metadata, but **not a complete version history or verified copying relationships**. Some commit dates are missing; even a recorded first commit at the current path may be later than the skill's origin. We therefore infer plausible comparison directions rather than reconstructing a proven family tree.

Our threat model focuses on observable instructions or code involving command execution, network access, file-system operations, credentials, external code or dependency acquisition, and system modification. These operations can be legitimate. They matter because an agent acting on untrusted instructions may have tools that affect a user's machine, data, or external services. A detected change is a **reason to review**, not evidence that an instruction ran, a vulnerability was exploited, or its author intended harm. The full threat model describes the trust boundary and coverage limits.

## Analysis overview

Figure 1 shows the four stages in order. We establish relatedness and a plausible direction **before** examining changed operations; otherwise, a difference alone could be mistaken for an introduced behavior.

![Four stages of the static comparison process: group candidates, match and order, compare operations, and assess risk indicators.](report/figures/analysis-pipeline.svg){#fig-analysis-pipeline width="100%" .here}

## Step 1: Identify related skills

We first compare artifacts within a candidate family whose artifacts have the same exact name. Identical `SKILL.md` content is recognized by its file hash; known bundled-file content is represented separately by a fingerprint of sibling file hashes. This matters because two copies of `SKILL.md` can contain the same instructions yet ship with different scripts. Unavailable sibling state is treated as unknown, not as an empty bundle.

For distinct main-file contents, we compare the body text after masking the opening YAML frontmatter. We normalize and tokenize the text, then form **five-token shingles**: sequences of five consecutive tokens. Comparing sets of these short sequences tolerates some formatting changes while retaining important command and identifier structure.

We consider two skill variants sufficiently similar when they share at least **five shingles**, have a maximum **containment score of at least 0.80**, and have a **Jaccard similarity of at least 0.30**. Containment asks how much of the smaller shingle set appears in the larger one; Jaccard measures the shared shingles relative to all distinct shingles across both texts. For example, if two files have 100 and 150 shingles, with 85 shared, containment is `85 / 100 = 0.85` and Jaccard is `85 / 165 = 0.515` (approximately 0.52). The first captures retained content in an expanded skill; the second guards against treating a small shared fragment as broadly similar. Using both is useful because the *added* material in a modified skill may contain the behavior we seek.

The analyzer groups related artifacts into **similarity clusters**. Variants can belong to the same cluster through intermediate matches, so membership does not mean that every pair meets the similarity thresholds directly. An exact shared name is therefore only a starting point: a large family can contain several clusters of differently written skills. The thresholds are documented operational choices, not probabilities of copying.

## Step 2: Infer which artifact could come first

After establishing that two artifacts are related, we determine which could have come first. We evaluate five types of direction evidence in priority order: declared source, direct chronology, equivalent-peer chronology, repository-creation boundaries, and directional containment. Table 2 explains each method and its limitations.

| Priority | Direction evidence | What it establishes—and what it does not |
| --- | --- | --- |
| 1 | **Declared source** | Supported provenance metadata identifies a source; declarations can still be wrong or incomplete. |
| 2 | **Direct chronology** | `first_commit_at` records when a state was observed at its current file path, not its true original creation date. |
| 3 | **Equivalent-peer chronology** | A different occurrence of the *same known main-file and sibling state* supplies an earlier observed date when direct history is missing or later. The date belongs to the state, not automatically to the undated occurrence. |
| 4 | **Repository-creation boundary** | If one state was observed before another repository existed, that other repository occurrence could not have been earlier. Repository age alone never dates a skill. |
| 5 | **Directional containment** | When stronger evidence is missing, substantially greater containment in one direction (difference of at least **0.10**) can suggest a plausible base-to-expanded order. This is the weakest direction signal. |

: Evidence used to infer earlier-to-later ordering, in priority order {.wide}

Equivalent-peer chronology helps when an artifact has no reliable commit date of its own. For example, suppose an equivalent copy of a skill was observed in January, and another related skill state was observed in March. The January observation may support an earlier-to-later comparison, even if the artifact being examined has no recorded date. However, the equivalent copy must have the same known skill content and sibling-file state. A different or unknown sibling state cannot supply that historical evidence.

Repository creation dates can also help establish order, but only in specific circumstances. If one skill state was observed before another repository existed, that observation can support an earlier-to-later comparison. Simply belonging to an older repository does not establish that a skill came first.

When the available evidence cannot support an ordering, we leave the relationship unresolved. Conflicting source declarations also remain unresolved, and equivalent states are retained as peers. For each directed comparison, we record the evidence used to determine its order. This allows us to distinguish comparisons supported by observed chronology from those relying on weaker evidence, such as directional containment.

The algorithm selects at most **one primary predecessor per derived candidate**, avoiding cycles. It also identifies other related, directed comparisons, called *additional edges*. For the final three trials, we scanned **only primary edges** to reduce repeated comparisons within large families. In a controlled Sprint 2 test using the same scanner configuration, this reduced the number of comparisons from 3,997 to 468 while retaining 43 of 44 observed family–indicator combinations. These results supported our decision to use primary edges, although additional edges may still contain unique findings. We did not perform a separate all-edge comparison for Sprint 3.

## Step 3: Detect and compare observable evidence

The static scanner applies **15 detection rules across six categories**: command execution, network access, file-system access, credentials, external code/dependency acquisition, and system modification. The rules identify recognizable constructs, such as a shell command, URL, file operation, or package-install instruction. They do not execute the content. The `SKILL.md` frontmatter is excluded from behavioral scanning because descriptive metadata and declared tools do not, by themselves, demonstrate an operation. Provenance metadata can still inform the ordering described in Step 2.

We then **extract and compare evidence**, rather than interpreting a changed rule-match count as new risk. Evidence records retain the recognized operation, source location, context, and extraction completeness. We normalize the evidence for comparison while preserving meaningful command arguments, file paths, and URL details, along with the original text. The comparison distinguishes added, removed, and matching constructs. A different URL might matter even if the number of URL matches stays the same; repeated mentions can raise match counts without introducing an operation. Unclear associations remain uncertain.

Bundled **sibling files** are assessed when added or changed content is available, regardless of file extension. For instance, a skill's instructions might remain the same while the bundled `setup.sh` changes. We examine the changed script's stored content, but do not infer its behavior from a filename when that content is missing. Renaming a file without changing its known content does not count as changed script behavior.

The comparator also distinguishes `skill-only`, `siblings-only`, `skill+siblings`, and `unknown` bundle changes. Here, **equivalent skill content** can mean equivalent under the token-shingle representation, not necessarily byte-for-byte identical; therefore, a `siblings-only` label does not by itself guarantee that no textual differences exist. Appendix B defines the classifications.

## Step 4: Assess changes against risk indicators

The last stage tests the changed evidence against **11 risk indicators (RIs)** defined for this study. Their purpose is to highlight observable ways in which an operation or source may change the agent's exposure to external code, networks, local files, credentials, or privileged actions. They do **not** assign a severity score. An indicator must be supported by the relevant *change* and its context; a rule match alone is insufficient.

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

: Eleven evidence-based risk indicators {.wide}

We chose these indicators because they can be supported by **specific observable evidence** in the dataset rather than speculative runtime effects. They also reflect the plausible changes described in the threat model. An indicator may be supported, uncertain, or absent from the observed comparison. “Absent” means **not supported by available evidence**, not proven safe. One command may support several indicators without representing several separate incidents.

A useful negative example from scanner development is a change from `npm install` to `bun install` that preserves the same dependency-acquisition workflow. Both commands remain in the extracted evidence, but the substitution alone does not support **RI-005**. This is intentional: recording a changed command does not mean reporting a newly introduced operation.

### Worked example: A changed installation instruction

The `python-executor` family provides a contrasting example from Trial 3: an installation change that meets our risk-indicator criteria. In the observed pair **1773238 → 1729578**, the guidance changes as follows:

**Base artifact:**

```bash
npx skills add inference-sh/skills@agent-tools
```

**Derived candidate:**

```bash
curl -fsSL https://cli.inference.sh | sh && infsh login
```

The base already describes software installation, so the finding is **not** that installation or network access became possible for the first time. The derived candidate introduces a *specific download-and-execute method*: it retrieves a remote shell script and passes it immediately to `sh`. It also introduces `cli.inference.sh` as a destination for an explicit network operation. The assessor consequently reported **RI-001** (direct download-and-execute) and **RI-003** (network expansion) from the same changed command—not two independent incidents.

This could be legitimate installation guidance, but executing remotely supplied code is relevant to supply-chain review because the contents of that code may change outside the skill. The stored instructions do not show whether an agent executed it, whether the agent's permissions would allow it, or whether the two artifacts share a verified copying history. The comparison has incomplete overall extraction coverage, although the installer evidence itself was extracted completely. **This case is an automated finding pending independent human validation.**

## Outcomes and interpretation limits

Our **primary measure** is the number of sampled families with at least one supported RI divided by all sampled families. Secondary measures count primary directed comparisons containing at least one RI, the distinct families containing each indicator, and the distribution by family size, direction basis, and evidence coverage. Indicator frequencies can overlap, so their totals are not additive.

A **flagged comparison** may contain rule changes, extracted-evidence changes, or uncertain observations even if no RI is supported. A **supported finding** meets a defined indicator's automated criteria; it is not a validated security incident. We separately report partial extraction, missing sibling content, and uncertainty. Complete coverage means no known gap *within the implemented extraction scope*, not comprehensive detection of all risks. Appendix B contains the rule registry and analysis workflow; Appendix E identifies the source artifacts and saved outputs used for these results.
