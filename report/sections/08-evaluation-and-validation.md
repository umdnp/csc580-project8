# Evaluation and validation

## What is established by the saved run

The pipeline completed the automated workflow for the supplied cohort, loaded all 1,151 selected artifacts, preserved pair-level outcomes, and generated review samples. Completion establishes that those stages produced the saved outputs. It does not establish that relationships are historical facts, that every supported RI is correct, or that unflagged cases lack in-scope changes. The committed annotation files contain draft entries for 21 of the 30 directed cases and all 15 relationship cases. Their entries are marked `review_phase=independent` but `review_status=pending`; the notes identify AI-assisted proposals awaiting human acceptance. This records review work in progress, not completed independent or adjudicated labels.

Earlier development checks exercised constructed fixtures, file-input comparisons, extraction, and output round trips. These provide regression evidence for specified behavior, not independent estimates of detector precision or recall. Appendix C summarizes the current validation scope and status. No new scanner test result is claimed from rebuilding this report, and an older passing test count is not presented as validation of the current research run.

## Current review design

The saved directed sample contains 30 pairs: five each from supported-indicator, uncertain-indicator, coverage-limited, sibling-change, flagged-without-indicator, and unflagged-directed strata. A separate relationship sample contains 15 pairs: five ambiguous, five equivalent, and five with no related edge. Both use seed 580. Sampling includes negative and difficult cases because reviewing only reported positives cannot establish recall or reveal missed relationships.

For a directed pair, reviewers inspect both original bodies, relevant available siblings, the source correspondence, and direction evidence. They judge each of RI-001 through RI-011 independently of the scanner's predicted IDs. Relatedness, direction, rule matches, evidence changes, supported/uncertain indicators, and coverage receive separate fields. For a relationship pair, reviewers assess substantive relatedness and defensible ordering, including pairs that the automated method did not link.

Independent copies precede team adjudication. The accepted annotations must match the frozen sample's identities and generated values; importing judgments from an earlier family list or regenerated sample without reconciliation would invalidate the link between labels and results. AI-assisted proposals can help identify source locations and questions, but are not an additional independent human reviewer. Acceptance of an individual explanatory example also does not establish completion of the full current sample.

## Indicator accuracy and uncertainty

A false positive occurs when the scanner supports an RI that manual review finds unsupported under its defined change conditions. A false negative occurs when manual review supports one of those eleven RIs and the scanner does not report it as supported. Missing an additional command, API, or keyword is not automatically an RI false negative: the behavior may be retained, uncertain, outside the eleven definitions, or additional evidence for an RI already reported.

For example, missing a second network-client syntax does not create another missed RI-003 category if the pair already supports and reports RI-003. Conversely, correctly extracting a package-install rule does not excuse an RI-005 false positive when the operation is merely an equivalent substitution. Separating these judgments keeps evaluation aligned with the research instrument rather than expanding it into an unbounded security checklist.

The reporting protocol includes indicator metrics only for assessable comparisons: manual relatedness must be related, direction supported, scanner and reviewer coverage complete, and all eleven categories reviewed. Uncertain individual indicators are excluded from their corresponding judgments. Other reviewed pairs remain informative cases but do not become negative labels. Precision measures support among reported positives; recall requires independently identified positives, including omissions.

The current saved summary contains no completed manual-validation or relationship-validation metrics. The report therefore provides no precision, recall, or reviewer-agreement estimate. The stratified review sample is designed to test the tool and inspect errors; without appropriate weighting it is not a prevalence sample. Appendix E links to the detailed protocol and annotation instructions.
