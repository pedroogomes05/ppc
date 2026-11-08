"""
plot_results.py — Gera gráficos comparativos a partir dos resultados do k6

Lê todos os ficheiros JSON em results/raw/ e gera:
  1. Throughput vs Concorrência (req/s por nível de VUs)
  2. Latência p95 vs Concorrência
  3. Latência p99 vs Concorrência
  4. Tabela completa de resultados em resultados_summary.csv

Uso:
  python plot_results.py

Pré-requisito:
  pip install pandas matplotlib
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Configuração ──────────────────────────────────────────────────────────────

RAW_DIR     = os.path.join(os.path.dirname(__file__), 'results', 'raw')
FIGURES_DIR = os.path.join(os.path.dirname(__file__), 'results', 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

# Cores e estilos por modo — consistentes em todos os gráficos
MODE_STYLE = {
    'platform': {'color': '#E74C3C', 'marker': 'o', 'label': 'Platform Threads'},
    'virtual':  {'color': '#2ECC71', 'marker': 's', 'label': 'Virtual Threads'},
    'async':    {'color': '#3498DB', 'marker': '^', 'label': 'Async (CompletableFuture)'},
}

# ── Leitura dos dados ─────────────────────────────────────────────────────────

def load_results(raw_dir: str) -> pd.DataFrame:
    """Lê todos os ficheiros JSON do k6 e devolve um DataFrame unificado."""
    rows = []
    for fname in sorted(os.listdir(raw_dir)):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(raw_dir, fname)
        with open(path, 'r') as f:
            data = json.load(f)
        rows.append(data)

    if not rows:
        raise FileNotFoundError(
            f"Não foram encontrados ficheiros JSON em '{raw_dir}'.\n"
            "Corre primeiro o run_all.ps1 para gerar os resultados."
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(['mode', 'vus']).reset_index(drop=True)
    return df

# ── Funções de gráfico ────────────────────────────────────────────────────────

def configure_axes(ax, title: str, xlabel: str, ylabel: str, df: pd.DataFrame):
    """Aplica estilos comuns a todos os gráficos."""
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks(df['vus'].unique())
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x)}'))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def plot_metric(df: pd.DataFrame, metric: str, title: str, ylabel: str, filename: str):
    """Gera um gráfico de linha para uma métrica, agrupado por modo."""
    fig, ax = plt.subplots(figsize=(9, 5))

    for mode, style in MODE_STYLE.items():
        subset = df[df['mode'] == mode].sort_values('vus')
        if subset.empty:
            continue
        ax.plot(
            subset['vus'], subset[metric],
            color=style['color'],
            marker=style['marker'],
            label=style['label'],
            linewidth=2,
            markersize=7,
        )
        # Anotação de valor em cada ponto
        for _, row in subset.iterrows():
            ax.annotate(
                f"{row[metric]:.1f}",
                xy=(row['vus'], row[metric]),
                xytext=(4, 6),
                textcoords='offset points',
                fontsize=8,
                color=style['color'],
            )

    configure_axes(ax, title, 'Concorrência (VUs)', ylabel, df)
    fig.tight_layout()

    out_path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(out_path, dpi=150)
    print(f"[OK] Gráfico guardado: {out_path}")
    plt.close(fig)


def plot_latency_comparison(df: pd.DataFrame):
    """
    Gráfico de barras agrupadas: p50 / p95 / p99 para cada modo
    ao nível de concorrência mais alto (melhor para a apresentação).
    """
    max_vus = df['vus'].max()
    subset  = df[df['vus'] == max_vus].set_index('mode')

    modes      = list(MODE_STYLE.keys())
    labels     = [MODE_STYLE[m]['label'] for m in modes]
    p50_vals   = [subset.loc[m, 'p50_ms'] if m in subset.index else 0 for m in modes]
    p95_vals   = [subset.loc[m, 'p95_ms'] if m in subset.index else 0 for m in modes]
    p99_vals   = [subset.loc[m, 'p99_ms'] if m in subset.index else 0 for m in modes]

    x      = range(len(modes))
    width  = 0.25
    fig, ax = plt.subplots(figsize=(9, 5))

    bars_p50 = ax.bar([i - width for i in x], p50_vals, width, label='p50', color='#95A5A6')
    bars_p95 = ax.bar([i         for i in x], p95_vals, width, label='p95', color='#F39C12')
    bars_p99 = ax.bar([i + width for i in x], p99_vals, width, label='p99', color='#E74C3C')

    ax.set_title(f'Distribuição de Latência a {max_vus} VUs', fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Modelo de Concorrência', fontsize=11)
    ax.set_ylabel('Latência (ms)', fontsize=11)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    out_path = os.path.join(FIGURES_DIR, f'latency_bars_vus{max_vus}.png')
    fig.savefig(out_path, dpi=150)
    print(f"[OK] Gráfico guardado: {out_path}")
    plt.close(fig)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  PPC — Gerador de Gráficos")
    print("=" * 55)

    df = load_results(RAW_DIR)
    print(f"\n[INFO] {len(df)} resultados carregados:\n")
    print(df[['mode', 'vus', 'throughput', 'p50_ms', 'p95_ms', 'p99_ms', 'error_rate']].to_string(index=False))
    print()

    # Gráfico 1: Throughput vs Concorrência
    plot_metric(
        df, metric='throughput',
        title='Throughput vs Concorrência',
        ylabel='Throughput (req/s)',
        filename='throughput_vs_concurrency.png',
    )

    # Gráfico 2: Latência p95 vs Concorrência
    plot_metric(
        df, metric='p95_ms',
        title='Latência p95 vs Concorrência',
        ylabel='Latência p95 (ms)',
        filename='latency_p95_vs_concurrency.png',
    )

    # Gráfico 3: Latência p99 vs Concorrência
    plot_metric(
        df, metric='p99_ms',
        title='Latência p99 vs Concorrência',
        ylabel='Latência p99 (ms)',
        filename='latency_p99_vs_concurrency.png',
    )

    # Gráfico 4: Barras comparativas ao nível de concorrência mais alto
    plot_latency_comparison(df)

    # Exportar tabela completa para CSV
    csv_path = os.path.join(RAW_DIR, 'resultados_summary.csv')
    df.to_csv(csv_path, index=False)
    print(f"\n[OK] Tabela completa guardada: {csv_path}")

    print("\n" + "=" * 55)
    print(f"  Gráficos gerados em: results/figures/")
    print("=" * 55)


if __name__ == '__main__':
    main()
