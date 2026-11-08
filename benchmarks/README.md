# Benchmarks — Gerador de Carga e Análise de Resultados

Pasta com os scripts de benchmark e análise do projeto PPC.

## Estrutura

```
benchmarks/
  benchmark.js       # Script k6: testa um endpoint com N utilizadores concorrentes
  run_all.ps1        # Automação: corre k6 para todos os modos e concorrências
  plot_results.py    # Gera gráficos comparativos a partir dos resultados
  results/
    raw/             # JSONs gerados pelo k6 (ex: platform_vus100.json)
    figures/         # Gráficos PNG gerados pelo Python
```

---

## Pré-requisitos

- k6 instalado e acessível no PATH → [download](https://github.com/grafana/k6/releases/latest)
- Python com pandas e matplotlib: `pip install pandas matplotlib`
- **Stub a correr** na porta `8080`
- **Agregador a correr** na porta `8081`

---

## Como Correr (Passo a Passo)

### 1. Arranca os servidores (em terminais separados)

```powershell
# Terminal 1 — Stub
cd C:\FCUL\PC\ppc\stub
mvn spring-boot:run

# Terminal 2 — Agregador
cd C:\FCUL\PC\ppc\aggregate
mvn spring-boot:run
```

### 2. Corre o benchmark completo

```powershell
# Terminal 3 — na pasta benchmarks
cd C:\FCUL\PC\ppc\benchmarks
.\run_all.ps1
```

O script corre automaticamente os 9 testes:
- 3 modos × 3 níveis de concorrência = 9 testes
- Duração estimada: ~8 minutos no total
- Resultados guardados em `results/raw/*.json`

### 3. Gera os gráficos

```powershell
python plot_results.py
```

Gera 4 gráficos em `results/figures/`:
- `throughput_vs_concurrency.png` — Throughput (req/s) por nível de VUs
- `latency_p95_vs_concurrency.png` — Latência p95 por nível de VUs
- `latency_p99_vs_concurrency.png` — Latência p99 por nível de VUs
- `latency_bars_vus500.png` — Comparação p50/p95/p99 ao nível máximo de concorrência

E uma tabela em `results/raw/resultados_summary.csv`.

---

## O que é cada nível de concorrência?

| VUs | Significado |
|-----|-------------|
| 10  | Carga baixa — poucos utilizadores em simultâneo |
| 100 | Carga média — começa a pressionar o pool de platform threads |
| 500 | Carga alta — platform threads esgotam-se, virtual e async sobressaem |

---

## Interpretação dos Resultados

| Métrica | O que significa |
|---|---|
| **Throughput (req/s)** | Quantos pedidos o servidor conseguiu responder por segundo |
| **p50 (ms)** | Latência típica — metade dos pedidos foi mais rápida que isto |
| **p95 (ms)** | 95% dos pedidos foi mais rápido — experiência da maioria dos utilizadores |
| **p99 (ms)** | Cauda longa — 1% dos pedidos mais lentos (mostra degradação sob carga) |
| **Error rate (%)** | % de pedidos que falharam com timeout ou erro do servidor |

---

## Notas de Validade

- O gerador de carga corre na **mesma máquina** que o servidor — há competição de recursos.
- Os resultados são **comparativos entre modelos**, não valores absolutos de produção.
- O warm-up (10s) garante que a JVM (JIT compiler) estabilize antes de medir.
- Deve ser anotado no artigo: *"gerador e servidor correram na mesma máquina; os resultados refletem uma comparação relativa entre modelos de concorrência".*
