# Method

## Research approach and security scope

Our question asks whether related skills introduce security-sensitive behavior absent from an earlier observed form. GitSkills contains skill-file snapshots and some repository and commit metadata, but **not a complete version history or a verified record of which skill was copied from which**. Some commit dates are missing; a first commit at the current file path may also be later than the skill's true origin. We therefore infer plausible relationships and ordering before comparing behavior. We do not claim to reconstruct a verified family tree.

Our threat model focuses on observable instructions or code involving command execution, network access, file-system operations, credentials, external code or dependency acquisition, and system modification. These operations can be legitimate. They matter because an agent acting on untrusted instructions may have tools that affect a user's machine, data, or external services. A detected change is a **reason to review**, not evidence that an instruction ran, a vulnerability was exploited, or its author intended harm. The full threat model describes the trust boundary and coverage limits.

## Step 1: Identify related skills

We first compare artifacts within an exact-name candidate family (RDR-003). Identical `SKILL.md` content is recognized by its file hash; known bundled-file content is represented separately by a fingerprint of sibling file hashes. This matters because two copies of `SKILL.md` can contain the same instructions yet ship with different scripts. Unavailable sibling state is treated as unknown, not as an empty bundle.

For distinct main-file contents, we compare the body text after masking the opening YAML frontmatter. We normalize and tokenize the text, then form **five-token shingles**: sequences of five consecutive tokens. Comparing sets of these short sequences tolerates some formatting changes while retaining important command and identifier structure (RDR-004).

We require three signals of relatedness: at least **five shared shingles**, maximum **containment of 0.80**, and **Jaccard similarity of 0.30**. Containment asks how much of the smaller shingle set appears in the larger one; Jaccard measures the shared shingles relative to all distinct shingles across both texts. For example, if two files have 100 and 150 shingles, with 85 shared, containment is `85 / 100 = 0.85` and Jaccard is `85 / 165 = 0.515` (approximately 0.52). The first captures retained content in an expanded skill; the second guards against treating a small shared fragment as broadly similar. Using both is useful because the *added* material in a modified skill may contain the behavior we seek.

The analyzer groups related artifacts into **similarity clusters**. An exact shared name is therefore only a starting point: a large family can contain several clusters of differently written skills. The thresholds are documented operational choices, not probabilities of copying.

## Step 2: Infer which artifact could come first

We assign an earlier (**base**) and later (**derived candidate**) only after establishing relatedness. The available evidence is tested in the following order (RDR-007):

| Priority | Direction evidence | What it establishes—and what it does not |
| --- | --- | --- |
| 1 | **Declared source** | Supported provenance metadata identifies a source; declarations can still be wrong or incomplete. |
| 2 | **Direct chronology** | `first_commit_at` records when a state was observed at its current file path, not its true original creation date. |
| 3 | **Equivalent-peer chronology** | A different occurrence of the *same known main-file and sibling state* supplies an earlier observed date when direct history is missing or later. The date belongs to the state, not automatically to the undated occurrence. |
| 4 | **Repository-creation boundary** | If one state was observed before another repository existed, that other repository occurrence could not have been earlier. Repository age alone never dates a skill. |
| 5 | **Directional containment** | When stronger evidence is missing, substantially greater containment in one direction (difference of at least **0.10**) can suggest a plausible base-to-expanded order. This is the weakest direction signal. |

: Evidence used to infer earlier-to-later ordering, in priority order {.wide}

For example, if a skill state has no recorded commit date but an equivalent copy was observed in January, that peer establishes that the state existed by January. If another related state is observed in March, January may support an earlier/later comparison. However, we cannot transfer that peer's date when its bundled-file state is different or unknown. Likewise, a repository created in March does **not** prove that its skill is newer than a skill in an older repository; a boundary is useful only when an independently dated state predates the repository.

When none of these methods supports direction, the relationship remains unresolved. Equivalent states remain peers rather than being forced into an earlier/later order. Each directed comparison retains its direction basis so that findings based on containment alone can be interpreted more cautiously than those supported by observed chronology.

The algorithm selects at most **one primary predecessor per derived candidate**, avoiding cycles. It can also identify other related, directed comparisons, called *additional edges*. RDR-013 selected **primary edges only** for the final three trials to study more families without repeatedly counting all related combinations in a few large families. In a controlled Sprint 2 comparison using the same scanner configuration, primary selection reduced 3,997 all-edge comparisons to 468 while retaining 43 of 44 observed family–indicator combinations. This supported the narrower design but did not establish that additional edges never contain unique findings. No separate Sprint 3 all-edge robustness result is claimed here.

## Step 3: Detect and compare observable evidence

The static scanner applies **15 detection rules across six categories**: command execution, network access, file-system access, credentials, external code/dependency acquisition, and system modification. The rules identify recognizable constructs, such as a shell command, URL, file operation, or package-install instruction. They do not execute the content. The `SKILL.md` frontmatter is excluded from behavioral scanning because descriptive metadata and declared tools do not, by themselves, demonstrate an operation. Provenance metadata may still inform Step 2 (RDR-002).

We then **extract and compare evidence**, rather than interpreting a changed rule-match count as new risk. Evidence records retain the recognized operation, source location, context, and extraction completeness. The comparison distinguishes added, removed, and matching constructs. A different URL might matter even if the number of URL matches stays the same; repeated mentions can raise match counts without introducing an operation. Unclear associations are left uncertain (RDR-008 and RDR-012).

Bundled **sibling files** are assessed when added or changed content is available, regardless of file extension. For instance, a skill's instructions might remain the same while the bundled `setup.sh` changes. We examine the changed script's stored content, but do not infer its behavior from a filename when that content is missing. Known identical-content renames do not count as changed script behavior (RDR-009).

The comparator also distinguishes `skill-only`, `siblings-only`, `skill+siblings`, and `unknown` bundle changes. Here, **equivalent skill content** can mean equivalent under the token-shingle representation, not necessarily byte-for-byte identical; therefore, a `siblings-only` label does not by itself guarantee that no textual differences exist. Appendix B defines the classifications.

## Step 4: Assess changes against risk indicators

The last stage tests the changed evidence against **11 risk indicators (RIs)** selected in RDR-010. Their purpose is to highlight observable ways in which an operation or source may change the agent's exposure to external code, networks, local files, credentials, or privileged actions. They do **not** assign a severity score. An indicator must be supported by the relevant *change* and its context; a rule match alone is insufficient.

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

A useful negative example from scanner development is a skill that changes `npm install` to `bun install` while retaining the same dependency-acquisition workflow. We still record the changed commands, but the substitution alone does not support RI-005. This distinction avoids inflating counts whenever routine instructions change (RDR-012). In contrast, introducing `curl -fsSL https://cli.inference.sh | sh && infsh login` adds an explicit download-and-execute operation. The Trial 3 `python-executor` comparison **1773238 → 1729578** received RI-001 and RI-003 for this single changed construct; its classification remains an **automated observation pending human adjudication**. Two indicators here describe two aspects of one command, not two incidents.

## Outcomes and interpretation limits

Our **primary measure** is the number of sampled families with at least one supported RI divided by all sampled families. Secondary measures count primary directed comparisons containing at least one RI, the distinct families containing each indicator, and the distribution by family size, direction basis, and evidence coverage. Indicator frequencies can overlap, so their totals are not additive.

A **flagged comparison** may contain rule changes, extracted-evidence changes, or uncertain observations even if no RI is supported. A **supported finding** meets a defined indicator's automated criteria; it is not a validated security incident. We separately report partial extraction, missing sibling content, and uncertainty. Complete coverage means no known gap *within the implemented extraction scope*, not comprehensive detection of all risks. Appendix B contains the rule registry and analysis workflow; Appendix E identifies the source artifacts and saved outputs used for these results.
