# Introduction {#sec-introduction}

A developer building a web application searches for a skill to help an AI coding agent generate front-end components and layouts. Its name and description look promising, so the developer adds it to the project. Unknown to the developer, someone has republished a modified copy of a legitimate skill and inserted an instruction to download and run an external script. If the agent follows that instruction, the script could steal API keys, read private project files, or install malware—even while the agent builds the requested interface.

*Skills* are reusable instructions that help AI agents perform specialized tasks. Under the Agent Skills specification, a skill contains a `SKILL.md` file and may include supporting scripts and other resources [@agentskills]. Its instructions can tell an agent which commands to run, which files to access, or which external services to contact. A skill's name and description do not tell the whole story.

**How can developers spot security-sensitive changes before trusting a skill?** Instructions can be copied, modified, and shared from many sources while keeping a familiar name and purpose. That creates a **software supply-chain** concern: a useful-looking skill may ask an agent to do something its adopter never intended.

Finding these changes is harder than comparing numbered software releases. Similar skills may be distributed independently, and sharing a name does not necessarily mean that two skills are related. **GitSkills** collects agent-skill files from public GitHub repositories, allowing us to examine similarities and differences [@gitskills]. Its records do not provide complete copying histories, and some supporting files and dates are unavailable.

Our study compares skills with similar content, infers which artifact may have come earlier, and examines differences in their instructions and supporting files. We use **static analysis** to inspect the stored content without executing it. The goal is to help developers and security reviewers identify changes worth investigating before adopting or updating a skill.
