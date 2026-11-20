Programa¸c˜ao Paralela e Concorrente Projeto Mestrado - Individual Semestre 2026/2027 



# **Empirical Study of a Parallel/Concurrent System** 

## **1 Motivation** 

Every claim about parallel/concurrent performance (“this scales up”, “this scheduler is faster”, “this primitive has less overhead”) is an empirical claim, and empirical claims need evidence. This project’s main goal is to produce that evidence. Pick a question (or open problem) about parallel/concurrent execution, measure it, and report what you found using sound experimental design and statistical methodology (e.g., speedup laws, correct timing, descriptive and inferential statistics for benchmark data). 

The goal is not novelty<sup>1</sup> . A student who rigorously answers a modest question should score higher than one who **sloppily “answers”** an ambitious one. 

## **2 Choosing a Topic** 

You have free choice of topic, but it must satisfy all three of the following: 

- **It is about parallel or concurrent execution** 

   - A language’s concurrency primitive, a scheduling policy, a parallelization strategy, a hardware feature, an architectural tradeoff, etc. 

- **It requires original measurement** 

   - You _must_ run the experiments and report real data: 

      - ∗ Original data from original work; 

      - ∗ Reproducing a subset of a published paper’s benchmark on different<sup>2</sup> hardware; 

      - ∗ Increasing the scope<sup>2</sup> of a published paper’s study. 

- **It is scoped to be answerable in a semester** 

   - A specific question / problem 

      - ∗ “does work-stealing outperform a fixed partition for skewed workloads on _N_ cores?”; 

      - ∗ “is it possible to improve the performance of this real application using a different parallelism abstraction (e.g., going from channels to actors)?”; 

      - ∗ “how much impact does a programming language have on the performance of a specific parallel application?”; 

   - **not a survey** (“parallel programming performance”). 

- **The results should matter** 

   - It needs to be important/relevant on some context 

      - ∗ Niche situations are forbidden (“compare the memory usage of Java’s Vector and ArrayList to add elements on a list”) 

> 1although novelty is surely challenging and exciting 

> 2it needs to be significantly different from the original source material 

PPC Project. Page 2 of 5. 

### **More examples** 

**_To spark ideas._** _DO NOT USE VERBATIM._ 

- Compare two concurrency primitives for the same problem (e.g., channels vs. shared-memory + locks) across different contention levels. 

- Reproduce one figure from a paper on current hardware and discuss what changed. 

- Benchmark a database or language runtime concurrency control (e.g., Python’s GIL removal in 3.13, Java virtual threads, normal threads, and OS processes under I/O-bound scenarios). 

- Energy/performance tradeoff of a GPU kernel across block/grid configurations. 

## **3 Checkpoints** 

The two first checkpoints exist specifically so nobody discovers in the last week that their topic cannot actually be measured, or that their experimental design is wrong. The proposal checkpoint is intentionally just pass/fail; its job is to catch problems early, not to grade writing quality yet<sup>3</sup> . 

|**Checkpoint**|**Due**|**Graded?**|**Deliverable**|
|---|---|---|---|
|Topic proposal|14 Oct 2026|Pass/fail<br>(one resubmission)|Single page + defense|
|Progress check-in|11 Nov 2026|Feedback only|Single page + defense|
|Final paper|02 Dec 2026|**0–20**|Complete paper|
|Presentation|03–04 Dec 2026<br>10–11 Dec 2026|**0–1** (multiplier)|Short talk + questions|



The topic proposal and the progress check-in are defended during **your** TP on the same week. Come prepared to talk through your proposal or progress. Final presentations will be held in the TP on two weeks. 

## **4 Required Paper Structure** 

The paper follows a short, double-column conference format (LaTeX template available on Moodle): at most 5 pages, plus up to 2 pages of references. The paper should have at least the following sections: 

- **Introduction** : explain the context of the problem. Includes: 

   - **Motivation** : why this question / problem matters, one paragraph. 

   - **Research Questions** : what you are trying to answer with this study. 

- **Related work** : at least 6 sources (papers, docs, prior benchmarks): what is already known, and what this study adds. 

> 3nevertheless, it should be well-written 

PPC Project. Page 3 of 5. 

- **Methodology** : what was built or modified, what was varied (independent variables), what was held constant. 

   - **Experimental setup** : hardware, OS, runtime/compiler versions, number of repetitions, warm-up strategy. Everything needed to reproduce the study. 

- **Results** : plots (boxplots/scalability curves), the statistical test used and why, effect size, and p-value. It might include tables in some specific cases. 

- **Analysis / Discussion** : what the reader can learn from the data you just presented. 

- **Threats to validity** : what could still be wrong or non-generalizing (single machine? noisy environment? small _N_ ? generality of results?). 

- **Conclusion** : answer your research questions, explicitly. 

   - **Future Work** : how do you see this study moving forward? What are the next steps? 

## **5 How to Submit** 

Share the git repository containing the paper (source + PDF) and the source code of the project via Moodle. The delivery commit must carry the tag `submitted` and must be made before the deadline. A missing tag is penalized, as is a tagged commit made after the deadline. The project should be runnable. The code is _not_ graded for code quality, but your results must be reproducible from what you submit. 

## **6 Grading Criteria** 

**Failing to define and propose a reasonable topic will result in failing the project.** The project represents 50% of the final grade of the course and has a minimum passing grade of 9.5. The paper is marked out of 20 points: 

|**Criterion**|**Points**|**Explanation**|
|---|---|---|
|Motivation|1.5|Clear, specific, falsifiable question|
|Related work|1.5|Shows awareness of existing knowledge|
|Methodology|3|Sound design: right variables isolated, right thing measured|
|Experimental rigor|4|Enough repetitions, warm-up handled, environment controlled<br>and reported|
|Results|4.5|Correct test for the data shape, effect size reported, plots that<br>actually support the claim|
|Analysis|3|Deep discussion on the impact of the results|
|Threats to validity|1|Honest, specific to the study|
|Writing/reproducibility|1.5|Clear enough to follow; code/data actually let you reproduce it|



The presentation (and the answers to the questions) will be graded from 0 to 1 and will act as a multiplicative factor on the paper grade. The final grade for the practical component will be: 

Practicalgrade = Papergrade _×_ Presentationgrade 

PPC Project. Page 4 of 5. 

### **6.1 Academic Integrity** 

The same terms as the rest of the course apply (see the syllabus). You may use AI tools (ChatGPT, Claude, and similar) provided their use is disclosed. You must be able to explain _any_ part of your code, analysis, or writing when asked; anything you cannot explain will be treated as plagiarism. 

## **7 FAQ** 

### **Topic** 

- _“Can I use programming language / software construct X for the project?”_ 

   - You are free to choose any topic, programming language, software construct, parallelism abstraction, etc., as long as it meets the requirements in Section 2. 

- _“What tips can you give me for choosing a topic?”_ 

   - Look for something you are genuinely interested in (data structures, deadlocks, games, optimization, green software, mobile development, etc.). It is the easiest way to stay motivated. If you have questions, feel free to ask me. 

- _“Can I reuse a project/topic from another course?”_ 

   - Yes. If you have a project that meets the criteria, you can reuse it and dig deeper. It needs to including new measurements and it should be stated it in your proposal the original source of the project. 

- _“Can I change my topic after the proposal is approved?”_ 

   - In most cases, you should not: you will have less time to work on it, and that might hurt your grade. If you really want to change, discuss it with me first. 

- _“What hardware do I need? What if I don’t have a multi-core machine or a GPU?”_ 

   - If you want to study something that requires equipment you do not have access to, talk to me and we will discuss your options. 

- _“Some topics are only covered in class after the proposal deadline. Can I still choose them?”_ 

   - Yes, but you will have to get ahead of the lectures on your own. If you are unsure whether that is feasible, talk to me and we will discuss your options. 

### **Paper** 

- _“Does the paper have to be in LaTeX?”_ 

   - Yes, using the template on Moodle. 

- _“How many repetitions are enough?”_ 

   - It depends on the context, environment, number of variables, etc. Either way, you should justify the number in the paper. 

PPC Project. Page 5 of 5. 

- _“What if my results are negative / my hypothesis turned out wrong?”_ 

   - That is fine. The goal of the project is not novelty. A well-executed, well-motivated study with negative results can be just as valuable. 

### **Other** 

- _“Can the project be done in pairs / groups?”_ 

   - No, the project is individual. 

- _“The progress check-in is ‘feedback only’. Do I have to show up?”_ 

   - Yes. All students are expected to come and show their progress. It is also when you receive important feedback on the direction of your work and on how to prepare your presentation. Do not skip it. 

- _“How long is the presentation? Which day am I supposed to present?”_ 

   - The duration should be about 5–8 minutes, with 3min more for questions (it depends on the number of projects submitted). The day of the each individual presentation will be published on Moodle at a later date. 

- _“Will I fail the course if I do not present my project?”_ 

   - Yes. 

- _“Do I need to be present for the other presentations?”_ 

   - Yes. You are expected to come and see your colleagues present (and you may ask questions!). 

