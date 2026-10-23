# Sprint 2 Results

Generated on **2026-10-23 17:26:38 UTC** by the end-to-end Sprint 2
pipeline.

## Summary

The pipeline completed successfully:

- **43** sampled artifacts were scanned.
- The sample contains **10** exact-name groups and **43** distinct file
  contents.
- **43/43** security profiles completed without skips or errors.
- **33/33** candidate comparisons completed without skips or errors.
- **14** comparisons were flagged because the derived artifact changed its
  security profile relative to the base artifact.
- The ordered sample membership hash is
  `edacbd69b656321189677e807c33cdbe88cbe4b63ec0e9c615370ddd6c7b11fa`.

## Security profile results

The 43 scanned artifacts exposed the following capability counts:

| Capability | Artifacts |
| --- | ---: |
| Command execution | 28 |
| Network access | 19 |
| External code execution | 15 |
| System modification | 11 |
| Filesystem access | 10 |
| Credential access | 8 |

The most frequently matched security rules were:

| Rule | Matches |
| --- | ---: |
| `CMD-001` | 28 |
| `CMD-002` | 21 |
| `NET-001` | 19 |
| `EXT-002` | 15 |
| `SYS-002` | 11 |
| `FS-001` | 9 |
| `CRED-001` | 8 |

## Comparison results

Comparisons were made between adjacent artifacts within each exact-name group.
This ordering-based pairing is useful for detecting changes in the sampled
sequence, but it does **not** prove repository ancestry or historical lineage.

Across the 33 comparisons:

- 19 comparisons were unflagged.
- 14 comparisons were flagged.
- 110 evidence items were added and 98 were removed across all comparisons.
- The largest net rule-match increases were `CMD-002` (+6), `EXT-002` (+5),
  `CMD-001` (+3), `NET-001` (+2), and `SYS-002` (+1).

Flagged comparisons are recorded in
[`security_changes.json`](./security_changes.json), including the base and
derived artifact metadata, rule deltas, and evidence added or removed.

## Output files

- [`execution_summary.json`](./execution_summary.json): pipeline status,
  counts, hash, and generation timestamp.
- [`sample_membership.json`](./sample_membership.json): the 43 artifacts used
  in this run.
- [`security_profiles.json`](./security_profiles.json): extracted capabilities,
  rule counts, matches, and evidence for each artifact.
- [`security_changes.json`](./security_changes.json): security-profile
  comparisons and flagged changes.
- [`artifact_processing_log.csv`](./artifact_processing_log.csv): per-artifact
  processing status.
- [`comparison_processing_log.csv`](./comparison_processing_log.csv):
  per-comparison processing status.

The sample was reused from Sprint 1 and analyzed against the
`agent_skills_release.db` database.
