# Benchmarks da RQ1

Esta pasta contém a execução dos benchmarks k6 e a geração de gráficos para comparar platform threads, virtual threads e I/O assíncrono no agregador.

## Topologia do ensaio

```text
Mac:     agregador Spring Boot + stub HTTP
Windows: k6
```

O k6 envia pedidos ao agregador na porta 8081. O agregador chama o stub localmente na porta 8080. O atraso do stub permanece fixo em 1 000 ms na RQ1.

## Configuração atual

`run_all.ps1` executa:

- 3 modelos: `platform`, `virtual` e `async`;
- 5 níveis de carga: 10, 100, 500, 1 000 e 2 000 VUs;
- 10 repetições por combinação, numa ordem aleatória;
- 10 segundos de aquecimento separados de cada medição;
- 30 segundos de carga constante por medição.

São 150 medições. A duração estimada é de aproximadamente 108 minutos, incluindo os aquecimentos e pausas entre execuções. Os dados do aquecimento não são guardados como resultados da medição.

O agregador fixa `server.tomcat.threads.max=200` e mantém desativada a configuração global de virtual threads do Spring. A rota `/aggregate/virtual` usa o executor virtual explicitamente definido no código. Assim, o limite do Tomcat é documentado e igual durante a série principal.

## Pré-requisitos

- k6 instalado no Windows e disponível no caminho configurado em `run_all.ps1` ou no `PATH`;
- Python com `pandas` e `matplotlib` para gerar gráficos;
- agregador e stub arrancados no Mac;
- Windows e Mac ligados à rede local.

## Executar

1. No IntelliJ do Mac, arranca primeiro o stub e depois o agregador. Mantém ambas as aplicações a correr.
2. No Windows, confirma no topo de `run_all.ps1` que `$BASE_URL` aponta para o IP atual do Mac, sem barra no final. Exemplo:

   ```powershell
   $BASE_URL = 'http://192.168.1.48:8081'
   ```

3. No PowerShell, a partir desta pasta, executa:

   ```powershell
   .\run_all.ps1
   ```

O script faz primeiro um pedido de disponibilidade. Se falhar, confirma que os dois serviços estão ativos e que o IP está correto.

## Resultados

- Resultados do piloto anterior: `results/raw/`.
- Resultados repetidos da RQ1: `results/raw_rq1/`, um JSON por condição e repetição.
- Ordem aleatória da série: `results/raw_rq1/run_order_*.csv`.
- Resumo agregado: `results/raw_rq1/resultados_summary.csv`.
- Gráficos da série RQ1: `results/figures/rq1/`.

Cada JSON contém o identificador e a repetição, modo, VUs, throughput, p50/p95/p99, taxa de erros, duração medida, atraso do stub e limite configurado do Tomcat. O throughput é calculado sobre a janela constante de 30 segundos.

Depois de terminar a série, gera o resumo e os gráficos com:

```powershell
python plot_results.py
```

Os gráficos apresentam a mediana entre repetições e o intervalo interquartil. A inferência estatística, os intervalos de confiança e o tamanho do efeito ainda têm de ser calculados e justificados na análise final.

## Limitações a registar

- Agregador e stub partilham CPU, memória, sistema operativo e rede no Mac.
- O k6 corre numa máquina diferente, mas a capacidade do Windows deve ser acompanhada para confirmar que o gerador não limita a carga.
- Os dados em `results/raw/` pertencem ao piloto inicial, cuja topologia era diferente. Não os mistures com os novos dados em `results/raw_rq1/`.
- A variação do atraso externo e a carga de CPU aplicada por pedido pertencem à RQ2, não à série principal da RQ1.
