SMAIRT: A Structured Framework for AI-Assisted Scientific Discovery in Computational Research

Authors

[Author names to be added]

Abstract

The integration of large language models into scientific research workflows presents both unprecedented opportunities and significant challenges. While AI assistants can rapidly synthesize existing knowledge and generate functional code, they fundamentally cannot produce genuinely novel scientific insights, a capability that remains uniquely human. We present SMAIRT (Scientific Method with AI Research Template), an open-source framework that structures AI-assisted computational research around the classical scientific method. SMAIRT provides researchers with a standardized project template, documentation conventions, and workflow guidelines that maximize the benefits of AI collaboration while maintaining clear attribution of intellectual contributions. The framework implements a three-phase data progression from synthetic through benchmark to real data, creates a comprehensive breadcrumb trail for reproducibility and session continuity, and explicitly tracks where human researchers provide critical insights versus where AI generates suggestions. We describe the framework's design principles, implementation details, and intended use cases. SMAIRT transforms AI from an opaque assistant into a transparent research partner, enabling scientists to rapidly reach the frontier of existing knowledge where genuine innovation becomes possible.

Introduction

The Promise and Peril of AI in Scientific Research

The emergence of large language models has fundamentally altered the landscape of computational research. Tools such as ChatGPT, Claude, and GitHub Copilot can generate functional code, synthesize literature, suggest experimental designs, and iterate through analytical approaches at speeds impossible for human researchers working alone. For computational biologists, data scientists, and researchers across quantitative disciplines, these capabilities promise dramatic acceleration of the research cycle.

However, this promise comes with significant challenges. Large language models exhibit a fundamental characteristic that limits their scientific utility: they excel at regression toward the mean of their training data. This means AI assistants are remarkably effective at reproducing established approaches, suggesting methods that have worked in similar contexts, and synthesizing what is already known. They are far less capable, perhaps fundamentally incapable, of generating truly novel scientific insights, identifying genuine gaps in knowledge, or making the innovative conceptual leaps that drive scientific progress.

This limitation creates a paradox for researchers. AI can help navigate the vast landscape of existing knowledge with unprecedented speed, but it cannot tell you where the unexplored territories lie. It can suggest approaches that have been tried before, but it cannot recognize when a problem requires a fundamentally new approach. The researcher who relies too heavily on AI suggestions risks being led in circles through well-trodden ground, never reaching the frontier where genuine discovery becomes possible.

The Hard Problem of Science

One of the most challenging aspects of scientific research is identifying questions that are simultaneously novel, important, and tractable. Many apparent research questions fall into one of several traps. Some questions have already been answered, perhaps in a different domain or using different terminology. Others are not actually novel but rather hidden variants of something already well-understood. Still others cannot be answered with available data and methods, or even if answerable, would not meaningfully advance understanding.

Traditionally, researchers develop the judgment to navigate these traps through years of immersion in their field, reading literature, attending conferences, discussing with colleagues, and accumulating tacit knowledge about what constitutes a genuine gap versus a dead end. AI assistants can dramatically accelerate the first part of this process, moving from relative ignorance to familiarity with what is known. They can help researchers quickly survey approaches, understand methodological options, and identify relevant prior work. But they cannot substitute for the human judgment required to recognize genuine novelty or importance.

The Need for Structured AI-Human Collaboration

Given these complementary strengths and limitations, effective AI-assisted research requires a structured approach that leverages AI strengths in rapid iteration, code generation, and synthesis of known approaches while preserving human agency in critical decision-making, novelty recognition, and interpretation. Such an approach must also maintain reproducibility through clear documentation of what was tried and why, track intellectual contributions through explicit attribution of human versus AI-generated insights, and enable continuity through the ability to resume work across sessions and share context with collaborators.

We developed SMAIRT (Scientific Method with AI Research Template) to address these requirements. SMAIRT is an open-source framework implemented as a cookiecutter template that generates a standardized project structure for AI-assisted computational research. The framework is grounded in the classical scientific method and provides explicit mechanisms for documentation, attribution, and reproducibility.

Related Work

SMAIRT builds upon and extends several traditions in scientific computing, research methodology, and the emerging field of AI-assisted research. Understanding these related frameworks helps situate SMAIRT's contributions and clarifies how it addresses gaps in existing approaches.

Project Organization Frameworks for Computational Research

The challenge of organizing computational research projects has been addressed by several influential frameworks. Noble's guidelines for organizing computational biology projects, published in PLoS Computational Biology, established foundational principles for directory structure, documentation, and reproducibility that remain widely cited. Noble emphasized the importance of separating raw data from processed data, maintaining clear documentation, and using version control, principles that SMAIRT incorporates and extends for the AI-assisted context.

Cookiecutter Data Science, developed by DrivenData, provides a standardized project template for data science work that has been widely adopted in industry and academia. This template emphasizes reproducibility through clear separation of data processing stages, from raw data through intermediate processing to final outputs. SMAIRT adopts the cookiecutter templating approach from this project but reorganizes the structure around the scientific method rather than the data processing pipeline, and adds explicit support for AI collaboration and intellectual contribution tracking.

The TIER Protocol, developed for teaching reproducible research in economics and social sciences, provides detailed guidelines for organizing data and analysis files to support transparency and replication. While focused on statistical analysis rather than computational research broadly, TIER's emphasis on documentation standards and clear provenance tracking influenced SMAIRT's approach to the breadcrumb trail.

Wilson and colleagues' "Good Enough Practices in Scientific Computing" and "Best Practices for Scientific Computing" provide comprehensive guidelines for computational research that have shaped practices across disciplines. These papers emphasize version control, testing, documentation, and collaboration practices that SMAIRT incorporates, while adding the AI-specific considerations that these earlier works could not have anticipated.

Reproducibility and Documentation Frameworks

The reproducibility crisis in science has spawned numerous frameworks aimed at improving documentation and enabling replication. Jupyter notebooks and similar literate programming environments attempt to interleave code, documentation, and results in a single document. While powerful for certain use cases, these environments can become unwieldy for larger projects and do not inherently support the iterative hypothesis-testing workflow that SMAIRT emphasizes.

Workflow management systems such as Snakemake, Nextflow, and Common Workflow Language provide formal specifications for computational pipelines that support reproducibility through explicit dependency tracking and containerization. These systems excel at ensuring that analyses can be re-executed but focus on the execution layer rather than the scientific reasoning layer that SMAIRT addresses. SMAIRT could be used in conjunction with such workflow systems, with SMAIRT organizing the scientific process and workflow managers handling execution reproducibility.

Electronic laboratory notebooks, both commercial and open-source, provide structured environments for documenting experimental work. While these systems support documentation and collaboration, they are typically designed for wet-lab research and do not provide the specific support for AI collaboration, code generation workflows, or the iterative computational hypothesis testing that SMAIRT emphasizes.

AI-Assisted Research Frameworks

The rapid emergence of large language models has spawned various approaches to integrating AI into research workflows, though few have been formalized into structured frameworks. Prompt engineering guidelines and best practices have emerged from the AI community, focusing on how to effectively communicate with language models to obtain desired outputs. These guidelines inform SMAIRT's approach to AI context files and session prompts but do not address the broader questions of research organization and intellectual contribution tracking.

The concept of AI pair programming, popularized by tools like GitHub Copilot, positions AI as a coding assistant that works alongside human developers. This paradigm influences SMAIRT's approach to code generation but SMAIRT extends beyond coding assistance to encompass the full scientific workflow from hypothesis formulation through interpretation.

Retrieval-augmented generation systems and AI agents represent more sophisticated approaches to AI-assisted work, where AI systems can access external knowledge bases or take autonomous actions. While these technologies may eventually integrate with frameworks like SMAIRT, the current implementation assumes a conversational AI assistant model where the human researcher maintains control of the workflow and the AI provides suggestions and generates code on request.

The emerging field of AI-assisted scientific discovery has produced systems like AlphaFold for protein structure prediction and various AI systems for materials discovery and drug design. These systems represent a different paradigm from SMAIRT, where AI performs specific well-defined tasks rather than serving as a general research assistant. SMAIRT is designed for the more common case where researchers use general-purpose language models as flexible assistants across diverse research tasks.

Distinguishing Features of SMAIRT

Several features distinguish SMAIRT from these related frameworks. First, SMAIRT explicitly addresses the human-AI collaboration dynamic, providing mechanisms for priming AI assistants, maintaining context across sessions, and tracking intellectual contributions. No existing framework provides this combination of features.

Second, SMAIRT organizes work around the scientific method rather than around data processing stages or project management concerns. This organization enforces disciplined hypothesis-driven research and creates natural documentation of the scientific reasoning process.

Third, the breadcrumb trail concept provides a novel approach to documentation that serves multiple purposes simultaneously: reproducibility, session continuity, collaboration support, and AI context restoration. While individual elements of this approach exist in other frameworks, their integration into a coherent system designed for AI-assisted research is unique to SMAIRT.

Fourth, the three-phase data progression provides structured guidance for moving from rapid prototyping through validation to real-world application. While experienced researchers often follow similar progressions informally, SMAIRT makes this progression explicit and provides organizational support for each phase.

Finally, SMAIRT's explicit intellectual contribution tracking addresses a concern that is unique to AI-assisted research: the need to clearly document where human insight drove the research versus where AI suggestions were followed. This feature has no direct analog in pre-AI research frameworks and represents a novel contribution to research methodology.

Design and Implementation

Core Philosophy

SMAIRT is built on several foundational principles that guide its design and use. The first principle positions AI as a vehicle to the frontier of knowledge, not beyond it. The framework explicitly positions AI as a tool for rapidly reaching the boundary of existing knowledge. Once at that frontier, human insight becomes essential for identifying genuine gaps and opportunities. This framing helps researchers maintain appropriate expectations and avoid over-reliance on AI suggestions.

The second principle uses the scientific method as the organizing structure for all work. All activities are organized around the classical scientific method cycle: Background, Hypothesis, Methods, Results, Interpretation, and Future Directions. This structure is not merely organizational; it enforces disciplined thinking about what is being tested and why, ensuring that each iteration of research has a clear purpose and measurable outcome.

The third principle establishes what we call the breadcrumb trail. Every prompt, response, code output, and interpretation is documented in a way that allows the complete thought process to be reconstructed. This serves multiple purposes including reproducibility, session continuity, collaboration, and critically, the ability to feed the entire project history back to an AI to restore context in new sessions.

The fourth principle requires explicit intellectual contribution tracking. The framework includes dedicated mechanisms for researchers to document where they provided critical insights versus where AI generated suggestions. This is essential for appropriate attribution in publications and for researchers' own understanding of their contributions to the work.

Project Structure

When a researcher creates a new SMAIRT project, the template generates a comprehensive directory structure designed to support the framework's principles. The docs directory contains philosophy documentation, a step-by-step methodology guide, and best practice guidelines for both solo researchers and collaborative teams. The prompts directory houses context files to prime AI assistants, code formatting conventions for AI-generated output, ready-to-use session initialization prompts, a running log of all prompts and responses, and tracking of human intellectual contributions.

The background directory stores the research question and literature context, while the hypotheses directory maintains tracking of all hypotheses tested throughout the project. The experiments directory is organized into three subdirectories corresponding to the three phases of data progression: synthetic data experiments, benchmark data experiments, and real data experiments. The results directory contains output logs from all experiments and generated visualizations, while the analysis directory holds interpretation of results and documentation of next steps and open questions.

The data directory mirrors the experiments structure with subdirectories for synthetic, downloaded, and real datasets. The scripts directory contains utility scripts including one to compile project state for AI sessions and another to generate new numbered experiment scripts. Finally, the paper_draft directory supports parallel development of methods documentation and results narrative as the research progresses.

This structure enforces separation of concerns while maintaining clear relationships between components. The prompts directory captures the human-AI interaction history, the experiments directory organizes code by data phase, and the results and analysis directories separate raw outputs from interpretation.

The Three-Phase Data Progression

A distinctive feature of SMAIRT is its explicit three-phase approach to data that guides researchers through increasingly realistic testing of their approaches. The first phase uses synthetic data, where initial experiments employ programmatically generated data with known properties. This enables rapid iteration without external dependencies, allows precise control over data characteristics, and permits assessment of whether an approach could work in principle before investing in real data acquisition. Synthetic data experiments are stored in the first experiments subdirectory.

The second phase employs downloaded benchmark data. Once approaches show promise on synthetic data, they are validated on publicly available benchmark datasets. This provides diversity including easy datasets, hard datasets, clean data, and messy data. It enables comparison with published results and tests robustness across different data characteristics. Benchmark experiments are stored in the second experiments subdirectory.

The third phase applies validated approaches to real data. By this point, the researcher has confidence that the methods work in principle and across diverse conditions, allowing focus on the scientific questions rather than methodological debugging. Real data experiments are stored in the third experiments subdirectory.

This progression is not mandatory, as some research questions may not be amenable to synthetic data or may require starting directly with real data. However, when applicable, the three-phase approach dramatically reduces wasted effort and increases confidence in results by ensuring that methodological issues are resolved before precious real data is analyzed.

The Breadcrumb Trail

Central to SMAIRT is the concept of the breadcrumb trail, a comprehensive record of everything that was tried, why it was tried, and what happened. This trail serves multiple critical purposes in the research workflow.

For session continuity, the breadcrumb trail addresses a fundamental limitation of LLM conversations: their limited context windows and lack of persistent memory. When starting a new session, researchers can use the compile_for_ai.py script to generate a summary of the project state, which can be provided to the AI to restore context. The breadcrumb trail makes this restoration possible and effective.

For reproducibility, the trail documents not just what code was run, but what prompts generated that code, what the researcher was thinking, and how results were interpreted. This level of documentation far exceeds typical research practices and enables genuine reproducibility of the research process, not just the final analysis.

For collaboration, when multiple researchers work on a project, the breadcrumb trail allows each to understand not just what was done, but the reasoning behind decisions. This is particularly valuable when researchers work asynchronously or when new team members join an ongoing project.

For intellectual contribution tracking, by documenting the full interaction history, researchers can later identify where they provided critical direction versus where AI suggestions were followed. This is essential for appropriate attribution and for researchers' own understanding of their contributions.

The breadcrumb trail is implemented through several mechanisms working together. Session logs in the prompts directory provide a complete record of prompts and response summaries. Output comments at the end of each script provide space where output is pasted directly into the code file. Interpretation logs in the analysis directory capture human interpretation of results. Hypothesis tracking in the hypotheses directory maintains a record of what was tested and the outcomes.

Code Conventions

SMAIRT specifies conventions for AI-generated code that support the breadcrumb trail and ensure consistency across the project. Scripts are numbered sequentially using a format like script_01_description.py, script_02_description.py, and so forth. This creates a clear timeline of what was tried and when, making it easy to trace the evolution of the research.

Every script outputs to both the console for immediate feedback and a log file in the results logs directory for permanent record. Log files are named to match their scripts, creating a clear correspondence between code and output.

Each script includes a standardized results comment block at the end. This block contains sections for pasting the console output, recording human interpretation of results including whether the hypothesis was supported and where the approach worked or broke down, and documenting what should be tried next. This convention ensures that when the repository is fed back to an AI, it can immediately see not just the code, but what happened when it ran and how the results were interpreted.

Intellectual Contribution Tracking

SMAIRT includes explicit mechanisms for tracking intellectual contributions through a dedicated file in the prompts directory. For each iteration, researchers document what AI suggested, what the researcher suggested, critical insights provided by the researcher, key decisions made by the researcher, and where the researcher pushed past dead ends that AI could not resolve.

This tracking serves several important purposes. For attribution, it ensures appropriate credit in publications by clearly documenting who contributed what. For self-awareness, it helps researchers understand their own contributions and maintain confidence in their intellectual role. For quality control, it encourages critical evaluation of AI suggestions rather than passive acceptance. For documentation, it creates a permanent record for future reference and potential disputes.

The framework distinguishes several types of human contributions that researchers should track. Conceptual contributions include novel questions, framings, or connections between ideas. Methodological contributions include approaches AI did not suggest and decisions at branch points in the research. Interpretive contributions include implications AI missed and unexpected pattern recognition. Critical judgment includes knowing when approaches are not working and recognizing limitations in AI suggestions.

AI Context Files

SMAIRT includes files specifically designed to prime AI assistants for effective collaboration within the framework. The AI_CONTEXT.md file explains to the AI its role in the SMAIRT workflow, what it excels at including rapid iteration, code generation, and synthesis of known approaches, what it is less suited for including genuine innovation and literature deep dives, and the expected workflow for the collaboration.

The CODE_CONVENTIONS.md file specifies how the AI should format code output, including naming conventions, logging requirements, and the results comment block structure. The SESSION_START.md file provides ready-to-paste prompts for initializing new AI sessions, continuing existing projects, interpreting results, and handling dead ends.

These files can be provided to any LLM-based assistant including ChatGPT, Claude, and others to establish consistent behavior aligned with SMAIRT conventions. This AI-agnostic approach ensures the framework remains useful as the landscape of AI tools continues to evolve.

Helper Scripts

The framework includes utility scripts to support the workflow and reduce friction in common tasks. The compile_for_ai.py script traverses the project and generates a single document summarizing the current state, including recent session logs, hypothesis status, and key results. This document can be pasted into a new AI session to restore context quickly and completely.

The new_script.py script generates a new numbered script with the standard template, including logging setup, the results comment block, and appropriate phase directory placement. This ensures consistency across all experiments and reduces the overhead of starting new iterations.

The SMAIRT Workflow

Starting a New Project

Beginning a new SMAIRT project involves several steps that establish the foundation for structured AI-assisted research. First, the researcher generates the project by running cookiecutter with the SMAIRT template, providing the project name, research question, and other metadata. This creates the complete directory structure with all necessary files and templates.

Next, the researcher primes the AI by starting an AI session and providing the contents of the AI context and code conventions files, or by using a ready-made prompt from the session start file. This establishes the AI's understanding of its role and the expected conventions.

The researcher then documents the research question by working with the AI to refine the question and document it in the background directory. This process often clarifies the scope and focus of the research. Finally, the researcher formulates an initial hypothesis and documents the first testable prediction in the hypotheses directory, setting the stage for the first experimental iteration.

The Iteration Cycle

Each iteration follows the scientific method in a structured cycle. The cycle begins with background, where the researcher reviews what is known, including results from previous iterations. This is followed by hypothesis, where the researcher states what is being tested in this iteration. The methods phase involves generating code to test the hypothesis, typically with AI assistance. The results phase involves running the code and capturing output. The interpretation phase analyzes results through the lens of the hypothesis. Finally, the future directions phase identifies next steps, which feed back into the background for the next iteration.

For each iteration, the researcher creates a new script using the helper script or by asking the AI to generate one following the conventions. After running the script, the researcher pastes output into the results comment block at the end of the script file. The researcher then updates the hypothesis log with the outcome, the iteration log with interpretation, the session log with the session record, the intellectual contribution file with their contributions, and the future directions file for the next iteration.

Handling Dead Ends

When an approach is not working, SMAIRT provides structured prompts for exploring alternatives. The framework includes specific prompts for dead end situations that help researchers articulate what has been tried, where things break down, and what alternatives might exist.

Critically, the framework reminds researchers that dead ends are where human insight becomes most important. AI may suggest variations on failed approaches, but recognizing when a fundamentally different direction is needed requires human judgment. The intellectual contribution tracking becomes especially important at these junctures, as the decision to pivot or persist often represents a key human contribution to the research.

Phase Transitions

When moving from synthetic to benchmark data, or from benchmark to real data, the researcher follows a structured transition process. First, the researcher summarizes findings from the completed phase in the background directory. Then the researcher documents which hypotheses were supported and which limitations were identified. The researcher tags the phase completion in git to mark the milestone. Finally, the researcher adapts approaches for the new data type and designs experiments to validate whether results transfer to the new context.

These transitions represent important checkpoints in the research process, ensuring that lessons from earlier phases inform later work and that the progression through data types is deliberate rather than haphazard.

Collaborative Use

For teams working together on SMAIRT projects, the framework provides guidelines for coordinating work effectively. Branch strategies involve user-specific branches with merging of completed iterations to the main branch. File ownership conventions specify shared logs with clear attribution of entries. Script numbering uses either user prefixes or designated ranges to avoid conflicts. Communication protocols include coordination logs and decision tracking to keep team members aligned.

The key principle for collaborative use is that the breadcrumb trail should be clear enough that anyone, including a new AI session, can reconstruct the full thought process and continue from where the team left off.

Example Use Cases

This section will be populated with real examples from projects that have used SMAIRT. The following placeholder descriptions indicate the types of examples that will be included.

Example 1

This example will describe a computational biology project that used SMAIRT, including the research question, how the three-phase data progression was applied, key iterations, and outcomes. This example will demonstrate the framework's utility for biological data analysis and show how the breadcrumb trail supported reproducibility.

Example 2

This example will describe a machine learning methods development project that used SMAIRT, showing how the framework supports algorithmic research and benchmarking. It will illustrate the value of the three-phase data progression for methods development and demonstrate intellectual contribution tracking in a context where AI generates substantial code.

Example 3

This example will describe a collaborative project involving multiple researchers, demonstrating the framework's support for team science and distributed work. It will show how the branching and attribution mechanisms support effective collaboration while maintaining clear documentation of individual contributions.

Discussion

Positioning AI Appropriately in Scientific Research

SMAIRT embodies a specific philosophy about the role of AI in scientific research: AI is a powerful tool for reaching the frontier of existing knowledge, but human insight remains essential for pushing beyond that frontier. This positioning has several important implications for how researchers should approach AI-assisted work.

First, it sets appropriate expectations. Researchers who expect AI to generate novel scientific insights will be disappointed and may become frustrated with the technology. Those who use AI to rapidly survey the landscape of known approaches will find it invaluable for accelerating their work. SMAIRT's documentation makes this distinction explicit, helping researchers calibrate their expectations appropriately.

Second, it preserves the essential human role in science. The framework's emphasis on intellectual contribution tracking ensures that researchers remain aware of where they are providing critical direction. This awareness is important both for appropriate attribution in publications and for maintaining the skills of scientific judgment that might otherwise atrophy through over-reliance on AI suggestions.

Third, it enables a productive division of labor between human and AI capabilities. AI handles the tasks it does well, including code generation, synthesis of known approaches, and rapid iteration through variations. This frees human researchers to focus on the tasks that require human judgment, including novelty recognition, interpretation of unexpected results, and strategic direction-setting for the research program.

Reproducibility and the Breadcrumb Trail

The breadcrumb trail concept addresses a significant challenge in computational research: the gap between what is documented and what actually happened during the research process. Traditional documentation captures final code and results but often omits the exploratory process, including the dead ends, the iterations, and the reasoning behind decisions. This omission makes it difficult for others to understand why certain approaches were taken and what alternatives were considered.

SMAIRT's breadcrumb trail captures this process in detail. While this requires more documentation effort than traditional approaches, the benefits are substantial. True reproducibility becomes possible, meaning not just reproducing results but understanding how they were reached. Learning from failures becomes easier because dead ends are documented, preventing repeated mistakes by the same researcher or others who follow. Onboarding new team members becomes more effective because they can understand not just what was done but why. AI continuity is enabled because context can be restored across sessions and even across different AI systems.

The documentation overhead is a legitimate concern, and researchers must weigh the benefits against the time investment. However, for projects of any significant duration or complexity, the investment typically pays dividends in reduced confusion, faster onboarding, and more effective collaboration.

Limitations and Future Directions

SMAIRT has several limitations that suggest directions for future development of the framework. The documentation overhead required by the framework may be burdensome for rapid exploratory work where the goal is quick iteration rather than careful documentation. Future versions might include more automated documentation capture to reduce this burden while maintaining the benefits of comprehensive records.

The current framework is AI-agnostic, working with any LLM-based assistant. While this flexibility is valuable, future versions might include optimizations for specific AI systems, such as custom GPTs or Claude projects with pre-loaded context, that could reduce the friction of session initialization and context restoration.

SMAIRT currently operates alongside computational environments such as Jupyter notebooks, integrated development environments, and high-performance computing systems rather than integrating directly with them. Deeper integration could reduce friction and improve documentation capture by automatically recording outputs and linking them to the code that generated them.

While SMAIRT has been developed based on practical experience with AI-assisted research, systematic evaluation of its impact on research productivity, reproducibility, and quality would strengthen the evidence base for its adoption. Future work should include controlled studies comparing research outcomes with and without the framework.

Implications for Scientific Practice

The emergence of AI assistants is changing how computational research is conducted, and this change will likely accelerate as AI capabilities continue to improve. Frameworks like SMAIRT represent one approach to managing this change, embracing AI's capabilities while preserving the essential human elements of scientific inquiry.

The specific mechanisms of SMAIRT may need to evolve as AI capabilities advance. Context windows will grow larger, reducing the need for explicit context restoration. AI systems may develop better memory and continuity across sessions. New interaction paradigms may emerge that change how researchers collaborate with AI assistants.

However, the core principles underlying SMAIRT are likely to remain relevant regardless of how AI technology evolves. Structured collaboration between human and AI capabilities will continue to be valuable. Explicit attribution of intellectual contributions will remain important for scientific integrity. Comprehensive documentation will continue to support reproducibility and collaboration. Appropriate positioning of AI as a tool rather than a replacement for human judgment will remain essential for maintaining the quality and integrity of scientific research.

Conclusion

SMAIRT provides a structured framework for AI-assisted computational research that maximizes the benefits of AI collaboration while maintaining clear documentation, attribution, and reproducibility. By organizing work around the scientific method, implementing a three-phase data progression, creating a comprehensive breadcrumb trail, and explicitly tracking intellectual contributions, SMAIRT enables researchers to leverage AI capabilities while preserving the essential human elements of scientific discovery.

The framework addresses a fundamental tension in AI-assisted research: the need to benefit from AI's capabilities while maintaining clarity about human contributions and ensuring reproducibility of the research process. By making the human-AI collaboration explicit and documented, SMAIRT transforms AI from an opaque assistant into a transparent research partner.

The framework is freely available as an open-source cookiecutter template. We invite the computational research community to adopt, adapt, and contribute to its continued development as we collectively navigate the integration of AI into scientific practice.

Availability

SMAIRT is available as an open-source cookiecutter template at [repository URL to be added]. The template is released under the MIT License, and projects generated from the template can use any license chosen by the researcher.

Acknowledgments

[To be added]

References

1. Chen M, et al. Evaluating Large Language Models Trained on Code. arXiv preprint arXiv:2107.03374. 2021.

2. Biswas S. Role of ChatGPT in Science and Research: A Systematic Review. Journal of Scientific Research. 2023.

3. Bender EM, Gebru T, McMillan-Major A, Shmitchell S. On the Dangers of Stochastic Parrots: Can Language Models Be Too Big? Proceedings of FAccT. 2021.

4. Kuhn TS. The Structure of Scientific Revolutions. University of Chicago Press. 1962.

5. Wilson G, et al. Good Enough Practices in Scientific Computing. PLoS Computational Biology. 2017;13(6):e1005510.

6. Sandve GK, et al. Ten Simple Rules for Reproducible Computational Research. PLoS Computational Biology. 2013;9(10):e1003285.

7. Noble WS. A Quick Guide to Organizing Computational Biology Projects. PLoS Computational Biology. 2009;5(7):e1000424.

8. Cookiecutter Data Science. DrivenData. Available from: https://drivendata.github.io/cookiecutter-data-science/

9. Ball R, Medeiros N. Teaching Integrity in Empirical Research: A Protocol for Documenting Data Management and Analysis. Journal of Economic Education. 2012;43(2):182-189.

10. Wilson G, et al. Best Practices for Scientific Computing. PLoS Biology. 2014;12(1):e1001745.

11. Kluyver T, et al. Jupyter Notebooks: A Publishing Format for Reproducible Computational Workflows. Positioning and Power in Academic Publishing: Players, Agents and Agendas. 2016:87-90.

12. Mölder F, et al. Sustainable Data Analysis with Snakemake. F1000Research. 2021;10:33.

13. Di Tommaso P, et al. Nextflow Enables Reproducible Computational Workflows. Nature Biotechnology. 2017;35(4):316-319.

14. Amstutz P, et al. Common Workflow Language, v1.0. Specification, Common Workflow Language working group. 2016.

15. Jumper J, et al. Highly Accurate Protein Structure Prediction with AlphaFold. Nature. 2021;596(7873):583-589.

16. Vaswani A, et al. Attention Is All You Need. Advances in Neural Information Processing Systems. 2017;30.

17. Brown TB, et al. Language Models Are Few-Shot Learners. Advances in Neural Information Processing Systems. 2020;33:1877-1901.

18. OpenAI. GPT-4 Technical Report. arXiv preprint arXiv:2303.08774. 2023.

19. Anthropic. Claude: A Next-Generation AI Assistant. 2023.

20. GitHub Copilot. GitHub. Available from: https://github.com/features/copilot

[Additional references to be added as appropriate]

Figures

Figure 1: SMAIRT Project Structure. Diagram showing the directory structure and relationships between components of a SMAIRT project.

Figure 2: The SMAIRT Workflow Cycle. Diagram showing the iterative cycle from Background through Hypothesis, Methods, Results, and Interpretation to Future Directions, which feeds back into Background.

Figure 3: Three-Phase Data Progression. Diagram showing progression from Synthetic data through Downloaded Benchmark data to Real Data, with key characteristics of each phase.

Figure 4: The Breadcrumb Trail. Diagram showing how documentation flows through the project and enables context restoration across sessions.

Supplementary Materials

S1: Complete Template File Listing. Full listing of all files generated by the SMAIRT template with descriptions of each file's purpose.

S2: Example Session Transcript. Annotated example of a complete SMAIRT session, from project creation through several iterations, demonstrating the workflow in practice.

S3: Comparison with Related Frameworks. Comparison of SMAIRT with other research organization frameworks such as Cookiecutter Data Science and Noble's guidelines for computational biology projects.
