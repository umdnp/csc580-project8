# Sprint 3 manual review CSV

[manual-review-final.csv](manual-review-final.csv) combines 90 directed-pair reviews and 45 relationship-pair reviews across three trials. The first ten columns summarize indicator outcomes for directed pairs. The original review fields follow them.

## Indicator counts

Each count is the number of distinct risk indicator IDs in a directed pair. A **firm flag** comes from `indicator_ids`. A **tentative flag** comes from `uncertain_indicator_ids`. When an ID appears in both lists, it counts as firm.

| Column | Meaning |
| --- | --- |
| `indicator_hits` | Firm flags the reviewer confirmed. |
| `indicator_false_alarms` | Firm flags the review ruled out as newly introduced indicators. |
| `indicator_misses` | Reviewer-confirmed indicators the scanner did not flag, either firmly or tentatively. |
| `tentative_hits` | Tentative flags the reviewer confirmed. |
| `tentative_false_alarms` | Tentative flags the review ruled out as newly introduced indicators. |
| `unresolved_firm_flags` | Firm flags whose review outcome is unresolved. |
| `unresolved_tentative_flags` | Tentative flags whose review outcome is unresolved. |
| `unresolved_unflagged_indicators` | Possible indicators the reviewer identified as unresolved that the scanner did not flag. |

An indicator counts as confirmed if it appears in `manual_supported_indicator_ids` or has an `introduced` entry in `manual_change_judgments`. The change judgments `none_detected`, `retained`, and `removed` count as evidence that the indicator was not newly introduced. An indicator listed in `manual_uncertain_indicator_ids`, or marked `uncertain`, `mixed`, `direction_unknown`, or `not_applicable` without confirmation, is unresolved.

For an `all_assessed` review, a flag with no manual confirmation or uncertainty counts as absent. For a `not_assessable` review, explicit findings still count, and a flag without a settled judgment counts as unresolved. A zero is an empty count for that outcome. All ten derived columns are blank on relationship-only rows.

## Clean pair outcome

`clean_pair_outcome` applies when `indicator_review_scope` is `all_assessed` and the reviewer confirmed no newly introduced indicators and left none unresolved. Its value then depends on what the scanner flagged.

| Value | When it appears |
| --- | --- |
| `correctly_clean` | The scanner produced no firm or tentative indicator flags. |
| `tentative_flag` | The scanner produced at least one tentative flag and no firm flags. |
| `firm_false_alarm` | The scanner produced at least one firm flag. This label takes precedence if the pair also has tentative flags. |
| Blank | The row is a relationship review, the indicator review was incomplete, or at least one indicator was confirmed or unresolved. |

The current CSV has 22 `correctly_clean` pairs, 2 `tentative_flag` pairs, and 0 `firm_false_alarm` pairs. The correctly clean rate is 22 out of 24 among pairs eligible for this label.

## Review evidence

`review_evidence` describes the basis available for interpreting a directed review. The first applicable label in this table is used.

| Value | When it appears |
| --- | --- |
| `structured_indicator_review` | The reviewer marked the scope `all_assessed` or supplied a structured indicator judgment that confirms, rules out, or leaves an indicator unresolved. A structured judgment can still be inconclusive. |
| `note_supports_existing_flags` | With no structured indicator verdict, a reviewer note describes observed behavior consistent with a scanner flag. In this CSV, one Trial 2 note received this label. It contributes no indicator hits. |
| `notes_only` | At least one of `notes`, `missed_observations`, or `false_positive_notes` contains text, and neither of the preceding labels applies. These notes can document context, missing evidence, or work still to be checked. |
| Blank | The row is a relationship review or has neither structured indicator evidence nor reviewer notes. |

When summarizing the CSV, use settled outcomes for hit, miss, and false-alarm rates. Report unresolved counts alongside those rates. The directed pairs were selected across review strata, so rates describe the reviewed cases.
