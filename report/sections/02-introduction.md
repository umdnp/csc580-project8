# Introduction {#sec-introduction}

Imagine you want your AI coding agent to make a draft sound more natural. You search for a writing "humanizer" skill, find one that promises to do just that, and add it to your project. What you don't realize is that someone has copied a legitimate skill and slipped in an instruction to download and run a script. If your agent follows that instruction, the script could steal API keys, access private files, or install malware—even while the skill appears to do the writing task you wanted.

*Skills* are reusable instructions that help AI agents perform specialized tasks. Under the Agent Skills specification, a skill contains a `SKILL.md` file and may include supporting scripts and other resources [@agentskills]. Its instructions can tell an agent which commands to run, which files to access, or which external services to contact. A skill's name and description do not tell the whole story.

**How can developers spot security-sensitive changes before trusting a skill?** Instructions can be copied, modified, and shared from many sources while keeping a familiar name and purpose. That creates a **software supply-chain** concern: a useful-looking skill may ask an agent to do something its adopter never intended.

Finding these changes is harder than comparing numbered software releases. Similar skills may be distributed independently, and sharing a name does not necessarily mean that two skills are related. **GitSkills** collects agent-skill files from public GitHub repositories, allowing us to examine similarities and differences [@gitskills]. Its records do not provide complete copying histories, and some supporting files and dates are unavailable.

Our study compares skills with similar content, infers which artifact may have come earlier, and examines differences in their instructions and supporting files. We use **static analysis** to inspect the stored content without executing it. The goal is to help developers and security reviewers identify changes worth investigating before adopting or updating a skill.
