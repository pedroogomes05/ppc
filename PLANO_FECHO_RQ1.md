# Plano para responder à RQ1

## RQ1

**Como variam o throughput e a latência dos três modelos de concorrência quando aumenta o número de pedidos concorrentes?**

A hipótese H1 prevê que, sob concorrência elevada e carga dominada por I/O, virtual threads e I/O assíncrono tenham maior throughput e menor latência de cauda do que platform threads.

## Estado atual

- Os três endpoints estão implementados no agregador: `/aggregate/platform`, `/aggregate/virtual` e `/aggregate/async`.
- O benchmark foi atualizado para fazer um aquecimento separado de 10 segundos e medir uma janela constante de 30 segundos.
- O runner está configurado para testar 10, 100, 500, 1 000 e 2 000 VUs, com 10 repetições por condição e ordem aleatória.
- Cada medição é guardada num JSON distinto em `benchmarks/results/raw_rq1/`; a ordem da série fica num CSV separado. Os resultados do piloto antigo em `results/raw/` são preservados.
- O resumo e os gráficos agrupam as repetições pela mediana e intervalo interquartil.
- O agregador fixa `server.tomcat.threads.max=200` e mantém desativado o uso global de virtual threads do Spring. A variante virtual continua a usar o executor virtual explícito.
- O piloto inicial usou 10, 100 e 500 VUs, com uma execução por condição. Esses resultados são exploratórios e foram obtidos com gerador, agregador e stub na mesma máquina.
- A configuração prática atual é **agregador + stub no Mac; k6 no Windows**. Os resultados desta configuração devem ser guardados separadamente dos resultados do piloto inicial.

## Decisões do protocolo da RQ1

1. **Atraso do stub:** manter fixo em 1 000 ms em todas as condições da RQ1. Variar a latência do serviço externo pertence à RQ2.
2. **Pool do Tomcat:** fixar e registar `server.tomcat.threads.max=200` no ensaio principal. Se houver tempo, fazer uma ronda secundária com 500 threads, aplicando o mesmo valor aos três modos e analisando-a separadamente.
3. **Concorrência:** incluir os níveis previstos na proposta: 10, 100, 1 000 e 2 000 VUs. Manter 500 VUs como ponto intermédio é útil para ligar o piloto à nova série, mas aumenta o número de condições.
4. **Topologia:** manter agregador e stub no Mac, com k6 no Windows, durante toda a nova série. Registar que os dois serviços partilham CPU, memória e sistema operativo no Mac.
5. **Repetições e ordem:** o runner atual está configurado para 10 repetições por combinação, em ordem aleatória. Justificar no artigo a escolha do número de repetições e descrever como a ordem foi gerada.

## Trabalho que falta

### 1. Preparar e executar a série

- Copiar para o Windows os ficheiros atualizados `benchmarks/benchmark.js` e `benchmarks/run_all.ps1`, e confirmar no runner que `$BASE_URL` aponta para o IP do Mac, sem barra no final.
- Confirmar que o stub e o agregador estão ativos no Mac e executar a série completa no Windows. A configuração contém 150 medições e demora aproximadamente 108 minutos.
- Guardar os resultados dessa série em `benchmarks/results/raw_rq1/`. Não misturar estes dados com o piloto antigo em `benchmarks/results/raw/`.

### 2. Recolher as medições

Para cada execução, recolher:

- **Throughput** em pedidos por segundo.
- **Latência p50, p95 e p99**, calculada na janela de carga constante.
- **Taxa de erros/timeouts** e número total de pedidos.
- **Utilização de CPU e memória**, se possível, como informação de apoio para verificar se o Mac ou o Windows se tornam um gargalo. A carga de CPU aplicada a cada pedido não precisa de ser variada na RQ1.

### 3. Analisar os resultados

- Mostrar a variação entre repetições, além de um valor central (por exemplo, mediana e intervalo interquartil).
- Comparar os três modelos para cada nível de VUs, em particular nos níveis elevados.
- Reportar o tamanho do efeito e um intervalo de confiança, além do teste estatístico e do respetivo valor-p. Escolher e justificar o teste tendo em conta se as medições são emparelhadas e a forma dos dados.
- Responder explicitamente à H1: indicar em que níveis de concorrência os resultados a apoiam, não a apoiam ou são inconclusivos.

## O que não é necessário variar para responder à RQ1

- **Latência variável ou de cauda longa do stub:** manter o atraso fixo em 1 000 ms. A variação da latência externa pertence à RQ2.
- **Trabalho de CPU por pedido:** não variar nesta fase. Isso pertence à RQ2.
- **Limite do Tomcat a 500:** não está incluído na série principal. Pode ser uma análise secundária se houver tempo para estudar quanto os resultados dependem do pool de 200 threads.

## Critério de conclusão da RQ1

A RQ1 estará respondida quando houver medições repetidas e comparáveis dos três modelos nos níveis de concorrência escolhidos, com throughput, p50/p95/p99 e falhas medidos na janela estável; análise da dispersão, efeito e incerteza; e uma conclusão explícita sobre a H1, acompanhada das ameaças à validade da topologia usada.

## Nota sobre as limitações da configuração

O k6 corre numa máquina separada, mas o agregador e o stub partilham o Mac. A carga do stub pode influenciar os recursos disponíveis ao agregador; a chamada ao stub também usa `localhost`, e não a rede entre máquinas. Esta configuração permite prosseguir com duas máquinas, mas a limitação deve constar na metodologia e nas ameaças à validade. Os resultados do piloto inicial, com outra topologia, devem continuar identificados como um conjunto separado.
