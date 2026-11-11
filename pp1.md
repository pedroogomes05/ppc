import pypandoc

markdown = r"""# Software Empirical Experimentation

**Unidade curricular:** Programação Paralela e Concorrente

## 1. Why empirical experimentation matters

> “You wrote a parallel version. Is it actually faster?”

A first measurement might show:

- Sequential: 812 ms
- Parallel: 799 ms

A second run might show:

- Sequential: 799 ms
- Parallel: 820 ms

These measurements are not enough to conclude that the parallel version is faster. **One run tells you nothing.** There is a difference between “I measured it” and “I know it.”

You are not measuring a single number: you are measuring a **distribution**.

## 2. Sources of variance

Measurements can vary even when the code and binary are unchanged. Common sources include:

- **OS scheduler:** context switches, other processes and background daemons.
- **JIT warm-up:** in Java, code may move from interpreted execution to C1 and then C2 compiled code.
- **Garbage collection pauses.**
- **CPU frequency scaling:** thermal throttling and turbo boost.
- **Cache state:** cold versus warm cache, or data evicted by another process.
- **Power management and hyperthreading contention.**

A sequence of runs of the same sequential binary can produce noticeably different execution times.

### Corollary

If one run cannot tell you the true execution time, one comparison (one sequential run versus one parallel run) cannot tell you which implementation is faster.

## 3. Performance metrics

### 3.1 Speedup

\[
Speedup(N) = \frac{T_{sequential}}{T_{parallel}(N)}
\]

Linear speedup is the ideal case:

\[
Speedup(N) = N
\]

The real speedup curve usually falls below the ideal curve.

### 3.2 Efficiency

\[
Efficiency(N) = \frac{Speedup(N)}{N}
\]

- Efficiency equal to 1.0 means perfect scaling.
- Efficiency decreases as the number of processing units grows when overhead consumes the gains.
- Granularity is relevant to parallel efficiency.
- Parallel efficiency is different from energy efficiency.

## 4. Laws of scalability

### 4.1 Amdahl's Law

Every program contains:

- A part that can be parallelized, \(P\).
- A part that remains sequential, \(S = 1-P\).

For \(N\) cores, the expected speedup is:

\[
Speedup(N) = \frac{1}{S + \frac{P}{N}}
\]

Even 5% sequential code limits the maximum speedup to 20x, regardless of how many cores are available.

Amdahl's Law answers:

> If I have one particular problem, how much faster can I make it by adding more processors?

### 4.2 Gustafson's Law

A different question is:

> If I have more processors, why not solve a bigger problem in the same amount of time?

- **Amdahl:** solve the same problem 100 times faster.
- **Gustafson:** use 100 processors to solve a problem 100 times larger, keeping execution time the same.

The speedup expression shown is:

\[
Speedup = 1 + (N-1)P
\]

### 4.3 Example

Given \(S = 0.2\), \(P = 0.8\) and a maximum of \(N = 8\):

**Amdahl:**

\[
\frac{1}{S + \frac{P}{N}}
= \frac{1}{0.2 + \frac{0.8}{8}}
= 3.33
\]

**Gustafson, when scaling the problem:**

\[
1 + (N-1)P
= 1 + 7 \times 0.8
= 6.6
\]

## 5. Designing an experiment

### 5.1 Independent and dependent variables

**Independent variables** are controlled by the experimenter:

- Number of threads/cores.
- Problem size.
- Algorithm variant.

Change one variable at a time and keep everything else constant.

**Dependent variables** are measured:

- Execution time.
- Memory.
- Energy.

### 5.2 Controlling the environment

For fair comparisons:

- Close other applications.
- Disable background synchronization and indexing.
- Keep JVM flags fixed across all runs, including heap size and GC algorithm.
- Use the same machine, session and day, taking thermal drift into account.
- Pin CPU affinity and disable turbo boost for consistency, or explicitly report that this was not done.

### 5.3 Repetition

One execution is not enough. How many runs are needed: 10, 100, 1,000 or 10,000?

The **Central Limit Theorem** states that the distribution of a normalized version of the sample mean converges to a standard normal distribution.

Thirty runs are sometimes treated as a “magic number”, but they are not a universal rule. The Student's t-distribution becomes quite close to the Z-distribution around this point; skewed data requires more runs.

### 5.4 Warm-up

Discard the first \(K\) iterations before recording measurements.

This is especially important on the JVM because the JIT compiler may not have started optimizing the code yet.

### 5.5 Randomizing runs

Do not execute all sequential runs and then all parallel runs.

Instead, alternate or randomize the configurations, for example:

```text
seq_1, par_1, seq_2, par_2, ...
```

This helps separate system-wide effects, such as thermal throttling or background processes, from actual performance differences.

### 5.6 Fair comparison across configurations

Example: a machine has 8 cores and is tested with 1, 2, 4 and 8 threads.

Other experimental conditions must remain constant across the four configurations for the comparison to be fair.

## 6. Measuring execution time

### 6.1 `currentTimeMillis()` versus `nanoTime()`

- `currentTimeMillis()`: wall-clock time, low resolution and can jump (for example, due to NTP synchronization).
- `nanoTime()`: monotonic, high resolution and suitable for measuring durations, not absolute time.

Example measurements from the slides:

- `currentTimeMillis`: 6 ms
- `nanoTime`: 5,342,291 ns (5.342291 ms)

### 6.2 Measuring a computation

```java
long start = System.nanoTime();
int result = seq(coins, 0, 0);
System.out.println("Result: " + result);
long elapsed = System.nanoTime() - start;
```

### 6.3 Anti-pattern: including I/O in the timed region

I/O is slow and noisy. Do not accidentally include it in the measurement.

```java
long start = System.nanoTime();
int result = seq(coins, 0, 0);
long elapsed = System.nanoTime() - start;

// Outside the timed region
System.out.println("Result: " + result);
```

### 6.4 Anti-pattern: no warm-up

**Wrong — includes JIT compilation cost:**

```java
long start = System.nanoTime();
for (int i = 0; i < ITERATIONS; i++) {
    run();
}
long elapsed = (System.nanoTime() - start) / ITERATIONS;
```

**Better — warm up before measuring:**

```java
for (int i = 0; i < WARMUP; i++) {
    run();
}

long start = System.nanoTime();
for (int i = 0; i < ITERATIONS; i++) {
    run();
}
long elapsed = (System.nanoTime() - start) / ITERATIONS;
```

### 6.5 Dead code elimination

The JIT compiler may optimize away a computation whose result is never used.

To prevent this:

- Consume the result.
- Add it to an accumulator that is printed at the end.
- Use a blackhole.

Example of a potential problem:

```java
int sum = 0;
long start = System.nanoTime();

for (int i = 0; i < ITERATIONS; i++) {
    sum += i;
}

long elapsed = (System.nanoTime() - start) / ITERATIONS;
System.out.println(elapsed);
```

If the result is not meaningfully consumed, the JIT may remove the computation.

### 6.6 Java Microbenchmark Harness (JMH)

JMH handles several benchmarking concerns:

- Warm-up.
- Forking fresh JVMs for each benchmark.
- Dead-code elimination.
- Statistical output.

For whole applications, a `nanoTime()`-based harness is acceptable. JMH is better for measuring small code sections, where JIT and inlining artifacts can dominate.

JMH is a library and must be managed through a build tool such as Maven or Gradle.

Example output:

```text
# Warmup Iteration   1: 0.260 ns/op
# Warmup Iteration   2: 0.262 ns/op
# Warmup Iteration   3: 0.271 ns/op
# Warmup Iteration   4: 0.273 ns/op
# Warmup Iteration   5: 0.269 ns/op
Iteration   1: 0.274 ns/op
Iteration   2: 0.265 ns/op
Iteration   3: 0.269 ns/op
Iteration   4: 0.267 ns/op
Iteration   5: 0.267 ns/op
```

## 7. Reporting and visualizing results

### 7.1 The mean can be misleading

Benchmark distributions are usually **right-skewed**:

- There is a lower bound on how fast something can execute.
- There is no equivalent upper bound on how slow it can become.
- A garbage collection pause or context switch can produce a long execution time.

Always report the median (or a trimmed mean) alongside the mean. Ideally, also report the standard deviation.

### 7.2 Spread matters

Two configurations can have the same mean but very different standard deviations.

The spread is important when deciding which system is better to deploy.

### 7.3 Interquartile Range (IQR)

The slides introduce the Interquartile Range (IQR) as a measure used when describing the spread of a distribution.

### 7.4 Boxplots

A boxplot presents a distribution and helps visualize:

- Median.
- Spread.
- Quartiles.
- Outliers.

Boxplots are useful for comparing different distributions. For distributions with a very small standard deviation, they are usually a poor choice.

### 7.5 Violin plots

A violin plot combines a boxplot with a density estimate. It can show whether a distribution is bimodal, at the cost of additional complexity compared with a boxplot.

### 7.6 Scalability plots

A good visualization can present data more effectively than a table.

- A line graph may be used when the standard deviation is sufficiently small.
- Otherwise, use a visualization that shows the distribution.

## 8. Statistical comparison

### 8.1 The null hypothesis

The null hypothesis, \(H_0\), states that the two distributions come from the same underlying distribution.

This means there is no real difference and the observed gap is due to noise.

The goal is to reject \(H_0\) with confidence.

### 8.2 Why a t-test is not always appropriate

Student's t-test assumes data is roughly normally distributed.

This assumption is often false for wall-clock timings, which can be skewed and contain outliers.

The **Mann–Whitney U test** (also known as the Wilcoxon rank-sum test):

- Is non-parametric.
- Compares distributions using ranks.
- Does not assume normality.
- Is presented as a safer default for benchmark data.

**Rule of thumb:** if unsure, use Mann–Whitney U. To be more certain, test whether the distributions are normal.

### 8.3 Interpreting a p-value

If \(p < 0.05\), this means:

> If there were truly no difference, data this extreme would appear less than 5% of the time.

It does **not** mean there is a 95% chance that the parallel version is faster.

A tiny p-value with a tiny, practically meaningless speedup is still a practically meaningless speedup.

**Statistical significance is not the same as practical significance.**

### 8.4 Effect size

Report how much faster a configuration is, not only whether a difference is statistically significant.

Example:

```text
Median speedup: 1.8x
95% confidence interval: [1.6x, 2.0x]
```

A confidence interval for the speedup itself is more informative than reporting only a p-value.

### 8.5 Cohen's d

Effect size can be calculated using Cohen's d:

\[
d = \frac{mean_1 - mean_2}{pooled\ standard\ deviation}
\]

It indicates how many standard deviations apart two configurations are.

Rules of thumb:

- 0.2: small.
- 0.5: medium.
- 0.8: large