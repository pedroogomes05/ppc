# Benchmarks — Gerador de Carga e Análise de Resultados

Pasta com os scripts de benchmark e análise do projeto PPC.

## Estrutura

```
benchmarks/
  benchmark.js       # Script k6: testa um endpoint com N utilizadores concorrentes
  run_all.ps1        # Automação: corre k6 para todos os modos e concorrências
  plot_results.py    # Gera gráficos comparativos a partir dos resultados
  results/
    raw/             # JSONs gerados pelo k6 (ex: platform_vus100.json) e CSV resumo
    figures/         # Gráficos PNG gerados pelo Python
```

---

## Pré-requisitos

- k6 instalado e acessível no PATH → [download](https://github.com/grafana/k6/releases/latest)
- Python com pandas e matplotlib: `pip install pandas matplotlib`
- **Stub a correr** na porta `8080`
- **Agregador a correr** na porta `8081`

---

## Fundamentos Teóricos: Porque é que Platform Threads saturam a 200 e Virtual Threads chegam a 500+?

Esta é a base teórica e concetual indispensável para o relatório e para a apresentação do projeto:

### 1. O Limite Prático do Tomcat (200 Threads)
Quando executamos o Spring Boot com o servidor Apache Tomcat clássico:
* O Tomcat cria um pool de **Platform Threads** gerido pela propriedade:
  `server.tomcat.threads.max = 200` (valor predefinido).
* Enquanto uma Platform Thread está ocupada a processar um pedido ou à espera da resposta de I/O de uma API externa (como o Stub), ela fica **bloqueada** e indisponível.
* Se chegarem mais de 200 pedidos em simultâneo (ex.: 500 utilizadores concorrentes no k6), **apenas 200 pedidos entram em execução imediata**.
* Os restantes **300 pedidos ficam parados numa fila de espera do Tomcat (request queue)**, aguardando que alguma thread termine. Isto provoca a degradação imediata da latência de cauda (**p95 e p99**).

### 2. O Motivo Físico e do Sistema Operativo (Platform vs Virtual Threads)
Porque não aumentamos simplesmente o pool do Tomcat para 10.000 Platform Threads?

| Característica | Platform Threads (Clássicas) | Virtual Threads (Java 21 / Project Loom) |
| :--- | :--- | :--- |
| **Mapeamento** | **1:1 com Threads do Sistema Operativo** (Windows/Linux kernel threads) | **M:N** (milhares de Virtual Threads multiplexadas em poucas carrier threads do SO) |
| **Consumo de Memória (RAM)** | **~1 MB por thread** alocada fixamente para a pilha de chamadas (call stack) | **~1 KB a poucos kilobytes** alocados dinamicamente na Heap |
| **Custo de 10.000 Threads** | **~10 GB de memória RAM** apenas para manter as threads em espera | **~10 a 20 MB de memória RAM** (impacto quase nulo) |
| **Custo de Bloqueio em I/O** | A thread do SO fica parada, impedindo outro trabalho e gastando ciclos com *context switching* | A JVM **desmonta** a Virtual Thread da carrier thread física, libertando o CPU para outras tarefas |
| **Comportamento a 500 Concorrentes** | Esgota as 200 threads do pool; 300 clientes esperam na fila | Cria 500 Virtual Threads instantaneamente sem esgotar a máquina |

---

## O Fenómeno do Gargalo no Serviço a Jusante (Downstream Bottleneck)

### A Analogia do Restaurante
Para entender o que medimos:
* O **Agregador** são os **Empregados de Mesa** (que atendem os clientes).
* O **Stub** é a **Cozinha** (onde a comida demora a ser confecionada).
* Se queremos avaliar a eficiência de diferentes tipos de empregados (Platform vs Virtual vs Async), **a cozinha (Stub) não pode ser o estrangulamento**. Se a cozinha só tiver capacidade para 200 pratos ao mesmo tempo, de nada serve ter 500 empregados rápidos: a comida vai demorar sempre o mesmo tempo porque encrava na cozinha!

### O que aconteceu no primeiro teste piloto (1000 ms no Stub)?
1. O Stub estava a demorar **1 segundo (1000 ms)** com um pool padrão de **200 threads**.
2. Capacidade máxima de processamento do Stub:
   $$\text{Throughput Máximo do Stub} = \frac{200 \text{ threads}}{1 \text{ segundo}} = 200 \text{ req/s}$$
3. Quando o k6 disparou 500 pedidos:
   * O Agregador (em Virtual Threads ou Async) aceitou os 500 pedidos.
   * Mas o Stub só conseguiu processar 200 de cada vez, deixando os restantes 300 na sua fila de espera interna.
   * **Consequência:** Todos os modelos deram ~184 req/s e ~2.5s de latência porque ficaram reféns da capacidade do Stub, mascarando as vantagens do Agregador!

### A Solução: Desbloquear o Stub mantendo 1 segundo de latência
Para testar latências realistas de 1 segundo sem que o Stub estrangule a experiência, basta ativar Virtual Threads **no próprio Stub** (`spring.threads.virtual.enabled=true`).
Desta forma:
* O Stub passa a conseguir responder a 500, 1.000 ou mais pedidos de 1s em paralelo sem fila de espera.
* O verdadeiro teste de concorrência recai **exclusivamente sobre o Agregador**:
  * O `/aggregate/platform` vai saturar nas suas 200 threads e criar fila de espera (~200 req/s, latência alta).
  * O `/aggregate/virtual` e `/aggregate/async` vão processar todos os 500 pedidos em paralelo (~500 req/s, latência estável em 1s).

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

## Interpretação das Métricas

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
- Deve ser anotado no artigo: *"gerador e servidor correram na mesma máquina; os resultados refletem uma comparação relativa entre modelos de concorrência"*.
