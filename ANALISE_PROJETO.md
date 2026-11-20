# Análise do projeto PPC

**Projeto:** Modelos de Concorrência num Microserviço Java  
**Unidade curricular:** Programação Paralela e Concorrente  
**Autor:** Pedro Gomes  
**Data da análise:** 19 de novembro de 2026

## 1. Âmbito da análise

Este documento regista a análise dos documentos Markdown, do código-fonte, das configurações, dos scripts e dos dados de benchmark presentes no repositório. Foram consultados o enunciado (`statement.md`), a proposta (`ppc_proposal_67991.md`), os resultados preliminares (`preliminary_results.md`), as notas (`pp1.md`), os READMEs, o log de experiências, o código Java, os ficheiros Maven, o script k6, a automação PowerShell, o analisador Python, os nove resumos JSON e o CSV agregado.

**Os ficheiros PDF não foram abertos nem lidos.** Ficheiros gerados de build, como `target/`, e imagens já existentes foram identificados na árvore, mas não são fontes primárias para descrever a implementação. Não foi executado código nem alterado o comportamento do projeto durante esta análise.

## 2. Objetivo académico e estado do projeto

O enunciado pede um estudo empírico sobre execução paralela ou concorrente, com medições originais, desenho experimental justificável e resultados reproduzíveis. O artigo final deve incluir motivação e perguntas de investigação, pelo menos seis fontes relacionadas, metodologia e configuração experimental, resultados com análise estatística e tamanho do efeito, discussão, ameaças à validade e conclusão. O limite indicado é de cinco páginas, mais até duas páginas de referências. O repositório e o código devem permitir reproduzir o trabalho.

A proposta estuda três formas de tratar chamadas HTTP num serviço Spring Boot: chamadas bloqueantes em platform threads, chamadas bloqueantes em virtual threads e I/O não bloqueante com `HttpClient.sendAsync()` e `CompletableFuture`. A **RQ1** pergunta como throughput e latência mudam com a concorrência; a **RQ2** pergunta como latência externa, número de chamadas e carga de CPU alteram a comparação. As hipóteses são que virtual threads e async beneficiam sob carga I/O-bound elevada e que essa vantagem diminui à medida que aumenta o trabalho de CPU.

O estado atual já permite executar as três variantes e contém um piloto de 3 modos × 3 níveis de utilizadores virtuais (VUs). Esse piloto cobre apenas a RQ1, com uma chamada HTTP, atraso fixo de 1 000 ms e uma execução por condição. A RQ2, as repetições, a medição de memória e a análise inferencial ainda não estão implementadas nos resultados existentes.

## 3. Arquitetura e implementação

O repositório contém dois serviços independentes, ambos com Spring Boot 3.3.5 e alvo Java 21:

1. **Stub**, no módulo `stub/`, escuta na porta 8080. `GET /stub` espera o valor de `stub.delay-ms` (configurado como 1 000 ms) ou um `delayMs` fornecido no pedido. Depois devolve JSON com o serviço, atraso, timestamp, thread e mensagem. O servidor ativa `spring.threads.virtual.enabled=true`, para reduzir a possibilidade de o servidor simulado ser limitado pelo pool normal do Tomcat.
2. **Agregador**, no módulo `aggregate/`, escuta na porta 8081 e usa um `HttpClient` partilhado para chamar `http://localhost:8080/stub`. Um executor partilhado cria uma virtual thread por tarefa. Os endpoints são `/aggregate/platform`, `/aggregate/virtual` e `/aggregate/async`.

### 3.1 Percurso de cada variante

- **Platform:** o controller chama diretamente `doWork()`, que executa `HttpClient.send()`. O pedido bloqueia a thread que trata o pedido HTTP no servidor.
- **Virtual:** o controller submete `doWork()` ao `newVirtualThreadPerTaskExecutor()` e devolve um `CompletableFuture` ao Spring MVC. A chamada HTTP continua bloqueante para a virtual thread; o trabalho é deslocado para ela e a resposta HTTP é assíncrona para o Spring MVC.
- **Async:** o controller usa `HttpClient.sendAsync()` e transforma a resposta com `thenApply()`. A thread do pedido pode regressar antes da resposta do stub.

As três variantes fazem uma chamada GET ao mesmo stub, com o mesmo corpo de resposta e sem trabalho de CPU adicional. O tempo individual da chamada ao stub é medido com `System.nanoTime()`, mas o k6 mede a latência vista pelo cliente, que também inclui o processamento e o percurso HTTP.

### 3.2 Observações técnicas sobre a implementação

- A implementação virtual inclui duas características: uma virtual thread por tarefa e o retorno de um `CompletableFuture` ao Spring MVC. Portanto, a comparação mede esses percursos concretos em conjunto.
- O pool Tomcat do agregador não está explicitamente configurado no `application.properties`; o README e a interpretação do piloto assumem o valor predefinido de 200 threads. Para reproduzir e interpretar o teste, esse valor e a configuração efetiva do servidor devem ser registados e fixados.
- O stub regista duas mensagens INFO por pedido. A carga de logging pode consumir recursos e deve ser considerada ao interpretar testes de elevada taxa.
- O `HttpClient` tem timeout de ligação de 5 s; cada pedido ao stub tem timeout de 10 s. O cliente k6 usa timeout de 15 s. Estes limites não são iguais e fazem parte das condições experimentais.
- A variante async não verifica explicitamente o código HTTP do stub e propaga falhas do `CompletableFuture`. As variantes bloqueantes também incluem o status recebido, sem transformar status não-2xx em falha da chamada.
- O `threadRequest` e o `threadCompletion` são registados para a variante async. A identidade entre threads é uma observação de execução, não uma garantia necessária do modelo.

## 4. Benchmark e dados disponíveis

O script `benchmarks/benchmark.js` testa um endpoint por execução, com estágios de subida de 10 s, carga alvo por 30 s e descida por 5 s. Usa um timeout de pedido de 15 s, verifica status 200 e exporta throughput, p50, p95, p99, média, taxa de erro e total de pedidos. `run_all.ps1` percorre platform, virtual e async, nessa ordem, e testa 10, 100 e 500 VUs para cada modo; há uma pausa de três segundos entre execuções. O script faz ainda um pedido inicial a `/aggregate/platform` para verificar disponibilidade.

Os resultados JSON confirmam os números de `preliminary_results.md`:

| VUs | Modo | Throughput (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Erros |
|---:|---|---:|---:|---:|---:|---:|
| 10 | Platform | 8,29 | 1 008,81 | 1 020,94 | 1 031,02 | 0% |
| 10 | Virtual | 8,33 | 1 007,67 | 1 018,53 | 1 030,72 | 0% |
| 10 | Async | 8,36 | 1 007,30 | 1 017,68 | 1 019,09 | 0% |
| 100 | Platform | 82,30 | 1 008,36 | 1 019,25 | 1 039,85 | 0% |
| 100 | Virtual | 82,16 | 1 008,27 | 1 020,13 | 1 032,76 | 0% |
| 100 | Async | 81,99 | 1 008,80 | 1 026,81 | 1 096,31 | 0% |
| 500 | Platform | 183,71 | 2 477,89 | 2 793,12 | 2 837,45 | 0% |
| 500 | Virtual | 403,53 | 1 018,53 | 1 091,43 | 1 133,70 | 0% |
| 500 | Async | 404,58 | 1 015,83 | 1 060,21 | 1 138,17 | 0% |

A 500 VUs, virtual e async obtêm aproximadamente 2,20× o throughput de platform. O p99 de platform é aproximadamente 2,50× o de virtual e 2,49× o de async. A 10 e 100 VUs, throughput e latências são próximos. Os nove ficheiros indicam zero falhas HTTP segundo a métrica `http_req_failed` do k6.

Estes números são **descritivos de uma execução por condição**. Não estimam variabilidade entre execuções, não suportam um teste estatístico e não demonstram equivalência entre virtual e async. A diferença de throughput entre esses dois modos a 500 VUs é pequena nesta execução, mas é necessário repetir para avaliar a sua estabilidade.

## 5. Leitura metodológica e limitações

1. **As fases do teste são agregadas.** O `handleSummary` extrai métricas globais do teste, que inclui subida, medição e descida. Assim, os p50/p95/p99 e throughput guardados não são calculados exclusivamente sobre a janela constante de 30 s. Para uma análise final, convém recolher a janela de medição explicitamente ou identificar claramente que as métricas abrangem as três fases.
2. **Concorrência não é taxa de chegada fixa.** O k6 usa VUs iterativos, que enviam um pedido e esperam pela resposta antes de iniciar a iteração seguinte. A taxa obtida depende da latência e do número de VUs; VUs é o nível de concorrência configurado, não o número de pedidos simultaneamente ativos garantido em todo o instante.
3. **Gerador e serviços partilham máquina.** O documento preliminar regista Windows 10 Home, Intel Core i5-10400F (6 núcleos/12 threads), 16 GB RAM, Temurin 21.0.13 e Maven 3.10.0, com k6, agregador e stub na mesma máquina. A partilha de CPU, memória e I/O pode afetar os resultados.
4. **Possível gargalo do servidor.** O stub usa virtual threads, o que é uma medida útil para reduzir uma fila de threads bloqueadas, mas não prova por si só que o stub ou a máquina não limitam o throughput. A taxa perto de 404 req/s, com latência do stub próxima de 1 s, depende de capacidade concorrente e de recursos suficientes em todo o sistema.
5. **Ordem fixa e aquecimento limitado.** As condições são executadas sempre na mesma ordem e há um pedido de verificação em platform antes da série. Cada teste tem um estágio de subida, mas não há evidência de várias repetições ou de ordem aleatorizada. Efeitos de JIT, temperatura, carga do sistema e ordem podem influenciar comparações.
6. **Variáveis propostas ainda por cobrir.** Não há medições de 1 000/2 000 VUs, atrasos variáveis ou de cauda longa, 3/5 chamadas por pedido, trabalho de CPU, uso de memória, CPU do sistema, dispersão ou inferência estatística.
7. **Análise dos gráficos.** `plot_results.py` faz gráficos de linhas e barras a partir de um ponto por combinação e exporta CSV. São úteis para visualizar o piloto, mas sem repetições não mostram dispersão nem intervalos de confiança. A documentação dos gráficos deve refletir que cada ponto representa uma única execução.

## 6. Consistência dos documentos

- O `stub/README.md` ainda apresenta as três variantes como por implementar, descreve atraso padrão de 50 ms e uma estrutura antiga de projeto monolítico. O estado atual usa módulos separados, atraso configurado de 1 000 ms no ficheiro de propriedades e variantes já presentes no agregador.
- O `stub/notes/experiment-log.md` regista Java 25.0.5, enquanto os resultados preliminares especificam Temurin 21.0.13. Esta diferença pode refletir momentos distintos, mas a versão efetivamente usada nos benchmarks finais precisa de ser confirmada e documentada.
- O `aggregate/README.md` é detalhado, mas contém explicações categóricas sobre limites, escalabilidade e comportamento de threads que não devem ser tomadas como resultados medidos deste projeto. São descrições de expectativa e pressupostos (por exemplo, o tamanho predefinido do pool), não garantias para todas as configurações.
- O `benchmarks/README.md` descreve a motivação dos testes, mas algumas estimativas de memória por thread e afirmações de capacidade são simplificações. O argumento de saturação do stub deve ser validado por dados ou instrumentação, não apenas pela analogia teórica.
- `pp1.md` contém notas didáticas de experimentação empírica: repetição, aquecimento, aleatorização, distribuição, visualização e inferência. Essas ideias apoiam a metodologia, mas não são evidência do projeto nem substituem a justificação do desenho final. O ficheiro contém ainda um bloco de Python/Markdown que parece material de geração/conversão e não documentação operacional do serviço.
- A proposta prevê seis ou mais fontes no artigo final; proposta e relatório preliminar enumeram cinco referências. É necessário acrescentar fontes relevantes e sintetizar o que o estudo acrescenta face a cada uma.

## 7. Organização do repositório observada

- `stub/`: serviço HTTP de atraso configurável, fontes Java, configuração e notas.
- `aggregate/`: serviço Spring Boot com os três endpoints concorrentes.
- `benchmarks/`: script k6, automação PowerShell, análise Python, JSON/CSV e figuras.
- `preliminary/`: fontes e artefactos auxiliares de LaTeX e bibliografia. Não foram usados para esta análise do conteúdo do relatório, conforme a orientação para usar os Markdown e não ler PDFs.
- Raiz: enunciado, proposta, relatório preliminar e notas didáticas.
- `target/` em ambos os módulos contém artefactos compilados do Maven.

Na verificação de estado do Git, o diretório também apresentava `ESTADO_PROJETO.md`, `plano_projeto.md`, `ppc_proposal_67991.pdf` e `statement.pdf` como removidos no working tree, e `.DS_Store`, `.idea/`, `ppc_proposal_67991.md` e `preliminary_results.md` como não rastreados. Esta observação é apenas um retrato do estado local durante a análise; não foram restaurados nem alterados esses ficheiros. Os PDFs não foram abertos.

## 8. Próximas etapas recomendadas

1. **Fechar e registar o protocolo da RQ1:** fixar versão Java, configuração e máximo do Tomcat, configuração do stub, hardware, processos concorrentes, duração e critério de aquecimento; guardar a configuração de cada execução.
2. **Recolher repetições comparáveis:** executar várias repetições por condição, alternar/aleatorizar a ordem e guardar dados por execução. Justificar o número de repetições e reportar mediana e dispersão, além de estimativas de efeito e incerteza.
3. **Separar medição de aquecimento:** calcular as métricas apenas para o intervalo de carga constante, ou explicitar e justificar outra janela. Guardar também falhas, timeouts e pedidos concluídos.
4. **Verificar o gargalo:** medir recursos do agregador, stub e gerador; testar se a capacidade do gerador permite manter a carga; quando possível, executar o gerador noutra máquina.
5. **Expandir o âmbito por etapas:** testar níveis superiores de concorrência para RQ1 e depois variar um fator de cada vez para RQ2 (atraso, chamadas por pedido e CPU), evitando uma matriz demasiado grande para o prazo.
6. **Medir memória e recursos:** escolher uma medida reproduzível (por exemplo, RSS/heap e CPU ao longo do teste), explicar o que representa e usar as mesmas condições para os três modos.
7. **Atualizar documentação e artefactos:** alinhar os READMEs com a implementação e ambiente reais, acrescentar as fontes relacionadas necessárias e garantir que instruções e scripts funcionam a partir de uma cópia limpa do repositório.

## 9. Conclusão da análise

O projeto tem uma pergunta concreta, uma arquitetura executável e um piloto que mostra uma diferença forte a 500 VUs no cenário I/O-bound de atraso fixo. O resultado preliminar é coerente com H1, mas ainda é indicativo: uma execução por condição, métricas que incluem todas as fases e execução na mesma máquina não permitem concluir significância estatística ou generalização. O principal trabalho restante é tornar o protocolo repetível e controlado, recolher distribuições comparáveis, medir recursos e alinhar a documentação com o estado real do código antes de responder formalmente às perguntas de investigação.
