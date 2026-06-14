# SMAIRT Paper Abstract — PLoS Computational Biology

## SMAIRT: A Structured Framework for AI-Assisted Scientific Discovery in Computational Research

**Target journal**: PLoS Computational Biology  
**Article type**: Software / Education  
**Status**: Draft

---

### Abstract

The integration of large language models (LLMs) into scientific research workflows presents both unprecedented opportunities for acceleration and significant challenges for reproducibility, attribution, and methodological rigor. We present SMAIRT (Scientific Method with AI Research Template), an open-source framework that structures AI-assisted computational research around the classical scientific method. Implemented as a cookiecutter template, SMAIRT generates standardized project structures with automated audit trails (linking hypotheses to scripts to logs to analyses), cross-session error prevention through accumulated known patterns, Model Context Protocol (MCP) skills for persistent AI context, configurable data progressions, and integrated HPC support. The framework's IDE-native workflow enables AI assistants to read files directly, execute code, and write documentation without manual context transfer—dramatically reducing the overhead of comprehensive documentation while maintaining it automatically.

We demonstrate SMAIRT through three use cases: (1) a machine learning classifier developed through synthetic-to-real data progression, illustrating the framework's core iteration cycle and knowledge accumulation; (2) an Artemis II trajectory prediction project exercising collaborative workflows, HPC integration, and paper-driven mode; and (3) a metagenomic functional annotation problem where the 3-phase data progression was essential for disentangling methodological artifacts from biological signal, and where a documented dead-end led to the study's central finding. Across all cases, SMAIRT's KNOWN_PATTERNS.md mechanism prevented error recurrence across sessions, the audit trail provided complete reproducibility of both results and reasoning, and intellectual contribution tracking clearly delineated human versus AI contributions for publication attribution.

SMAIRT is freely available under the MIT License at https://github.com/biodataganache/smairt-cookiecutter.

**Word count**: 262 (PLoS Comp Bio limit: 300)

---

### Keywords

AI-assisted research, reproducibility, scientific method, research template, large language models, computational biology, project organization, intellectual contribution tracking

---

### Author Summary (required by PLoS Comp Bio)

AI tools like ChatGPT and Claude can write code and suggest experiments far faster than humans working alone, but they cannot generate genuinely novel scientific ideas—they excel at reproducing what's already known. This creates a challenge: how do we benefit from AI's speed without losing track of our own intellectual contributions, and how do we maintain reproducibility when AI interactions are ephemeral?

SMAIRT solves this by providing a project template that automatically documents everything: which hypotheses led to which experiments, what the code produced, how results were interpreted, and crucially, where the human researcher provided the key insights that AI could not. The framework also remembers what went wrong in previous sessions, preventing the frustrating cycle of rediscovering the same errors.

We show SMAIRT working across three very different problems—a machine learning classifier, aerospace trajectory prediction, and a tricky metagenomics question—demonstrating that the same structured approach accelerates research regardless of domain. The framework is free, open-source, and works with any AI tool.
