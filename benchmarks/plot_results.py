"""Summarize repeated k6 runs and generate RQ1 plots.

Reads one JSON summary per measured run from results/raw_rq1/ and produces
median-with-IQR plots plus a grouped CSV summary.
"""

import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd


BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, 'results', 'raw_rq1')
FIGURES_DIR = os.path.join(BASE_DIR, 'results', 'figures', 'rq1')
os.makedirs(FIGURES_DIR, exist_ok=True)

MODE_STYLE = {
    'platform': {'color': '#E74C3C', 'marker': 'o', 'label': 'Platform Threads'},
    'virtual': {'color': '#2ECC71', 'marker': 's', 'label': 'Virtual Threads'},
    'async': {'color': '#3498DB', 'marker': '^', 'label': 'Async (CompletableFuture)'},
}
METRICS = ('throughput', 'p50_ms', 'p95_ms', 'p99_ms', 'error_rate')


def load_results(raw_dir: str) -> pd.DataFrame:
    """Load per-run JSON summaries, ignoring unrelated JSON files."""
    rows = []
    for filename in sorted(os.listdir(raw_dir)):
        if not filename.endswith('.json') or '_vus' not in filename:
            continue
        path = os.path.join(raw_dir, filename)
        with open(path, 'r', encoding='utf-8') as result_file:
            rows.append(json.load(result_file))

    if not rows:
        raise FileNotFoundError(
            f"No per-run JSON results found in '{raw_dir}'. "
            "Run benchmarks/run_all.ps1 first."
        )

    frame = pd.DataFrame(rows)
    required = {'run_id', 'mode', 'vus', *METRICS}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Result JSON is missing required fields: {', '.join(sorted(missing))}")
    return frame.sort_values(['mode', 'vus', 'run_id']).reset_index(drop=True)


def summarize_runs(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate repeated runs as medians and interquartile ranges."""
    rows = []
    for (mode, vus), group in frame.groupby(['mode', 'vus'], sort=True):
        row = {'mode': mode, 'vus': int(vus), 'runs': int(len(group))}
        for metric in METRICS:
            values = pd.to_numeric(group[metric], errors='coerce').dropna()
            if values.empty:
                row[f'{metric}_median'] = float('nan')
                row[f'{metric}_q1'] = float('nan')
                row[f'{metric}_q3'] = float('nan')
                continue
            row[f'{metric}_median'] = float(values.median())
            row[f'{metric}_q1'] = float(values.quantile(0.25))
            row[f'{metric}_q3'] = float(values.quantile(0.75))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(['mode', 'vus']).reset_index(drop=True)


def configure_axes(ax, title: str, ylabel: str, frame: pd.DataFrame) -> None:
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Concorrência (VUs)', fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks(sorted(frame['vus'].unique()))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda value, _: f'{int(value)}'))
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def plot_metric(frame: pd.DataFrame, metric: str, title: str, ylabel: str, filename: str) -> None:
    """Plot the median of each condition with an IQR error bar across runs."""
    fig, ax = plt.subplots(figsize=(9, 5))

    for mode, style in MODE_STYLE.items():
        subset = frame[frame['mode'] == mode].sort_values('vus')
        subset = subset[subset[f'{metric}_median'].notna()]
        if subset.empty:
            continue

        medians = subset[f'{metric}_median']
        lower = (medians - subset[f'{metric}_q1']).clip(lower=0).to_numpy()
        upper = (subset[f'{metric}_q3'] - medians).clip(lower=0).to_numpy()
        ax.errorbar(
            subset['vus'], medians,
            yerr=[lower, upper],
            color=style['color'],
            marker=style['marker'],
            label=style['label'],
            linewidth=2,
            markersize=7,
            capsize=4,
        )

    configure_axes(ax, title, ylabel, frame)
    fig.tight_layout()
    output_path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(output_path, dpi=150)
    print(f'[OK] Figure saved: {output_path}')
    plt.close(fig)


def plot_latency_comparison(summary: pd.DataFrame) -> None:
    """Plot median p50/p95/p99 with IQR at the highest measured VU level."""
    max_vus = int(summary['vus'].max())
    subset = summary[summary['vus'] == max_vus].set_index('mode')
    modes = [mode for mode in MODE_STYLE if mode in subset.index]
    labels = [MODE_STYLE[mode]['label'] for mode in modes]
    positions = list(range(len(modes)))
    width = 0.25
    metric_specs = [
        ('p50_ms', 'p50', '#95A5A6', -width),
        ('p95_ms', 'p95', '#F39C12', 0),
        ('p99_ms', 'p99', '#E74C3C', width),
    ]

    fig, ax = plt.subplots(figsize=(9, 5))
    for metric, label, color, offset in metric_specs:
        medians = [subset.loc[mode, f'{metric}_median'] for mode in modes]
        lower = [
            max(0, subset.loc[mode, f'{metric}_median'] - subset.loc[mode, f'{metric}_q1'])
            for mode in modes
        ]
        upper = [
            max(0, subset.loc[mode, f'{metric}_q3'] - subset.loc[mode, f'{metric}_median'])
            for mode in modes
        ]
        ax.bar(
            [position + offset for position in positions], medians, width,
            label=label, color=color, yerr=[lower, upper], capsize=3,
        )

    ax.set_title(f'Latência a {max_vus} VUs (mediana e IQR)', fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Modelo de concorrência', fontsize=11)
    ax.set_ylabel('Latência (ms)', fontsize=11)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=9)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    output_path = os.path.join(FIGURES_DIR, f'latency_bars_vus{max_vus}.png')
    fig.savefig(output_path, dpi=150)
    print(f'[OK] Figure saved: {output_path}')
    plt.close(fig)


def main() -> None:
    raw = load_results(RAW_DIR)
    summary = summarize_runs(raw)

    print(f'Loaded {len(raw)} measured runs:')
    print(raw.groupby(['mode', 'vus']).size().rename('runs').to_string())

    csv_path = os.path.join(RAW_DIR, 'resultados_summary.csv')
    summary.to_csv(csv_path, index=False)
    print(f'[OK] Grouped summary saved: {csv_path}')

    plot_metric(
        summary, 'throughput', 'Throughput vs Concorrência',
        'Throughput (req/s)', 'throughput_vs_concurrency.png',
    )
    plot_metric(
        summary, 'p95_ms', 'Latência p95 vs Concorrência',
        'Latência p95 (ms)', 'latency_p95_vs_concurrency.png',
    )
    plot_metric(
        summary, 'p99_ms', 'Latência p99 vs Concorrência',
        'Latência p99 (ms)', 'latency_p99_vs_concurrency.png',
    )
    plot_latency_comparison(summary)


if __name__ == '__main__':
    main()
