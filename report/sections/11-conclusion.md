# Conclusion

We investigated whether modified or reused agent skills contain security-sensitive operations absent from a related earlier observed artifact. The study combines content similarity, evidence for plausible earlier/later ordering, comparison of instructions and available supporting files, and eleven defined risk indicators.

Across three non-overlapping Sprint 3 trials, the automated analysis identified supported indicators in **63 of 300 sampled families (21.0%)**. The most widely observed changes concerned local script execution and external code or dependency acquisition. These are useful review points because a change to a skill can change what an AI agent is instructed to run or obtain, even when the skill's name and general purpose remain the same.

The findings are **not** confirmed vulnerabilities or evidence of malicious intent. GitSkills does not establish verified copying histories, some evidence is incomplete, and independent manual validation of relationships and indicator judgments is still in progress. The sample results also cannot be generalized to every GitSkills family.

Our contribution is a reproducible way to identify and explain candidate changes while preserving uncertainty about their source and meaning. The final assessment of detection accuracy and individual cases will depend on the team's completed manual reviews.
