# CSC 580 Group 8 – Meeting Minutes

**Date:** September 28, 2026 
**Duration:** Approximately 1.25 hours
**Attendees:** Jim Prantzalos, Vaisnavii Mohanraj, Kyle Cantrell  
**Absent:** Christian (Nepal Time Mismatch) 
**Purpose:** Select the team's research question and establish the approach for creating and managing the project backlog for Sprint 1.

## Main Topics of Discussion

The team met to review progress on Sprint 1 stories and discuss data analysis tools. Kyle had completed building a sample and documented the process, while Vaisnavii was working on creating a pipeline to load and extract fields needed for analysis. Jim demonstrated a new visualization tool he had developed that allows users to compare artifact relationships, chronology, and differences between base and derived files. The tool uses equivalent peer analysis to determine file relationships when commit dates are missing, and can generate JSON output for visualization purposes. The team discussed how to use the tool to identify false positives and negatives in their security scanning rules, with Jim emphasizing the importance of manual data inspection to refine their detection capabilities. Vaisnavii agreed to create a notebook version of the analysis using Kyle's sample data and the provided tools, while Jim committed to fixing the visualization tool's deployment to the main branch and providing documentation for its usage.

### Next steps
#### Jim
- Review the manual inspections and annotations in Vaisnavii's notebook once it's completed.
- Fix the issue with the visualization tool not being in the main branch and send out documentation on how to run it.
- Document the "candidate families do not establish copying" somewhere.
- Produce and share the lessons learned document for Sprint 1.
#### Kyle
- Send the list of candidate families to Vaisnavii via Discord direct message.
- Type up and send the pipeline instructions and Mergely usage to Vaisnavii via Discord.
#### Vaisnavii
- Finish setting up DuckDB tonight and follow the README sequentially in the data directory.
- Download the subset of candidate families from Kyle and finish building the pipeline.
- Run the pipeline on the subset of data and generate a comparison result.
- Create a Jupyter notebook to document the sample creation, run the comparison tool, manually inspect and annotate the results.
## Summary
### Sprint 1 Progress Review
The team discussed progress on Sprint 1 stories, with Kyle having completed most work on building a sample pipeline and awaiting a merge request. Vaisnavii needs to set up DuckDB and build a Jupyter notebook to analyze candidate families using the pipeline, with Jim requesting manual inspection of sample data to identify potential false positives and negatives. The team agreed that Vaisnavii should use a specific subset of candidate families for analysis, and Jim will document lessons learned and threats to validity once the data review is complete.
### Artifact Relationship Analysis Tool Demo
Jim demonstrated a visual tool for analyzing family relationships between artifacts in a repository. He explained how the tool uses JSON output from the Analyze Family tool to group similar files into clusters and identify relationships between base and derived artifacts. The tool determines relationships through chronology analysis, using commit dates when available, and leveraging equivalent peer nodes as proxies when date information is missing. Jim showed how the tool displays differences between artifacts and allows users to run security scans on the differences rather than on the artifacts themselves.
### Code Change Analysis Tool Demonstration
Jim demonstrated a tool he developed to compare and analyze code changes, specifically showing how it can identify differences between versions including system commands, URLs, and path changes. The tool provides visual inspection capabilities to help identify false positives and false negatives in code scanning rules. Vaisnavii expressed interest in creating a notebook version of the tool, though Kyle noted that the current tool should be sufficient for the analysis needs.
### Code Visualization Tool Demonstration
Jim demonstrated a visualization tool for analyzing code relationships and equivalent peers in a repository, explaining how it uses chronology and containment analysis to identify direct relationships between files. He showed how to run the Analyze Family tool to generate JSON data and use the visualization tool to examine file differences, including a live demonstration with CometChat-Core as an example. The team discussed implementation details, with Jim recommending Vaishnavii use WSL on Windows or set the GitSkillsDB environment variable to run the tool, and they confirmed the next meeting would be at 2 PM on Sunday.