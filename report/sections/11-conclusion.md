# Conclusion

We studied whether reused or modified agent skills introduce security-sensitive behavior absent from a related earlier observed artifact. Our pipeline uses content similarity, explicit direction evidence, static evidence comparison, and eleven defined risk indicators to identify changes that warrant human review.

Across **three non-overlapping Sprint 3 trials**, the automated analysis found supported indicators in **63 of 300 sampled families (21.0%)** and **340 of 2,157 primary directed comparisons (15.8%)**. Script-execution and external-code acquisition changes appeared across the most families. Pair-level percentages varied substantially because a few large or highly connected families contributed many repeated comparisons; the family-level result provides a more balanced view of the selected sample.

These are **candidate findings**, not confirmed vulnerabilities, evidence of malicious authorship, or population-wide prevalence estimates. The dataset does not provide verified copying histories, some evidence is incomplete, and manual evaluation of the similarity decisions and indicator judgments is underway. The final interpretation may change when those reviews are adjudicated.

The main contribution is a reproducible method that preserves what changed, the evidence for comparison direction, and the limits of what the scanner can establish. This makes detected differences useful for further review without presenting every changed command as a newly introduced security threat.
