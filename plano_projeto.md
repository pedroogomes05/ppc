# Guião para começar o projeto PPC

**Projeto:** Modelos de Concorrência num Microserviço Java
**Apresentação de progresso:** 11 de novembro de 2026
**Objetivo imediato:** chegar à apresentação com um protótipo executável, um pequeno piloto medido e uma página que explique o progresso.

## O que vais construir

Um serviço HTTP que recebe um pedido, chama um serviço externo simulado e devolve a resposta. Vais executar esse mesmo percurso de três maneiras:

1. Platform thread + chamada HTTP bloqueante;
2. Virtual thread + chamada HTTP bloqueante;
3. `HttpClient.sendAsync()` + `CompletableFuture`.

No início, não tentes estudar todas as variáveis da proposta. Primeiro faz as três variantes funcionarem de forma equivalente e mede apenas o efeito de aumentar a concorrência, mantendo o resto fixo.

## Começa por aqui - hoje

### Passo 1: prepara a pasta do projeto

Abre uma pasta de trabalho para o código, separada dos PDFs. Dentro dela, cria esta estrutura simples:

```text
ppc-project/
  README.md
  pom.xml
  src/main/java/...
  results/raw/
  results/figures/
  scripts/
  notes/experiment-log.md
```

Se já tens um repositório ou código iniciado, usa-o e adapta a estrutura; não cries outro projeto sem necessidade. Guarda os PDFs originais onde estão.

### Passo 2: confirma as ferramentas e o computador

Antes de programar, anota num ficheiro `notes/experiment-log.md`:

- Sistema operativo e modelo do computador;
- Processador e número de núcleos, RAM;
- Versão do Java (`java -version`);
- Versão do Maven (`mvn -version`), se usares Maven;
- Se tens acesso a uma segunda máquina para gerar carga.

Usa Java 21, conforme a proposta. Se não estiver instalado ou o projeto atual não compilar com essa versão, resolve isso antes de implementar as variantes.

### Passo 3: escreve a primeira versão da pergunta

Cola no `README.md` uma pergunta de trabalho simples:

> Como muda o throughput e a latência de um microserviço Java quando aumento o número de pedidos concorrentes, comparando platform threads, virtual threads e I/O assíncrono?

Regista também o que vais manter igual no primeiro piloto: uma chamada HTTP por pedido, mesma resposta, mesma latência fixa no serviço simulado e sem trabalho de CPU extra.

* [ ] Ordem de implementação

Segue esta ordem para não tentares depurar tudo ao mesmo tempo.

### 1. Faz o serviço simulado

Cria um endpoint HTTP pequeno que aguarda um tempo configurável e devolve sempre a mesma resposta. Nesta fase basta conseguires escolher, por configuração, por exemplo, um atraso fixo de 50 ms.

* [ ] **Concluído quando:** consegues chamar o endpoint manualmente e verificar que devolve resposta depois do atraso esperado.

### 2. Faz uma única versão do microserviço

Cria um endpoint agregador que chama o serviço simulado uma vez e devolve o resultado. Começa com uma chamada bloqueante normal em platform thread.

**Concluído quando:** uma chamada ao agregador chega ao stub e devolve a resposta certa. Regista também o tempo total do pedido.

### 3. Torna o modelo de concorrência configurável

Adiciona a segunda implementação, usando virtual threads para tratar os pedidos e mantendo a chamada HTTP bloqueante. Não mudes ao mesmo tempo o atraso, o número de chamadas nem o payload.

**Concluído quando:** consegues iniciar a aplicação em modo platform ou virtual thread e ambos devolvem o mesmo resultado.

### 4. Adiciona a versão assíncrona

Implementa a chamada com `HttpClient.sendAsync()` e `CompletableFuture`. Mantém a mesma lógica de endpoint e o mesmo serviço simulado.

**Concluído quando:** as três versões conseguem processar o mesmo pedido funcional. Guarda como selecionar cada modo (argumento, configuração ou variável) no README.

### 5. Só depois liga o gerador de carga

Escolhe uma ferramenta que permita definir concorrência e exportar latências. Usa a mesma ferramenta e os mesmos parâmetros nos três modos. Se ainda não souberes qual usar, primeiro termina o protótipo e valida com um script simples; não percas o dia a comparar ferramentas.

**Concluído quando:** uma execução deixa um CSV com, pelo menos, modo, concorrência, número de pedidos, latência e erros.

## Plano concreto até 11 de novembro

### 7 de novembro - preparar e arrancar

- Criar/confirmar o projeto Java e o registo de ambiente;
- Escrever a pergunta provisória e fixar o primeiro cenário (uma chamada, atraso fixo, sem CPU extra);
- Implementar o serviço simulado e verificar uma chamada manual;
- Anotar qualquer bloqueio técnico imediatamente.

**No fim do dia:** stub funcional e ambiente documentado.

### 8 de novembro - construir a baseline

- Implementar o endpoint agregador com platform threads e chamada bloqueante;
- Confirmar que o pedido termina e obtém a resposta correta;
- Medir o tempo de um pedido isolado só para validar o percurso, não para tirar conclusões de desempenho;
- Guardar comandos de arranque no README.

**No fim do dia:** caminho completo a funcionar numa variante.

### 9 de novembro - adicionar as alternativas

- Implementar o modo de virtual threads;
- Implementar o modo assíncrono;
- Verificar que cada modo faz exatamente o mesmo trabalho;
- Se uma variante estiver a bloquear o progresso, registar o problema e pedir feedback; não esconder uma variante incompleta.

**No fim do dia:** três modos funcionais, ou um protótipo claro com o estado real de cada modo.

### 10 de novembro - executar o piloto

- Executar aquecimento antes de guardar medidas;
- Usar poucos níveis de concorrência, por exemplo 10, 100 e 500, ajustando se a máquina não aguentar;
- Fazer algumas repetições curtas para confirmar que a recolha funciona;
- Guardar CSVs originais em `results/raw/` e anotar cada configuração;
- Criar um gráfico simples de concorrência versus throughput e/ou latência;
- Identificar o gráfico como **piloto exploratório**, não como conclusão final.

Se o gerador e o servidor estiverem na mesma máquina, escreve isso nas notas: a competição pelos recursos pode afetar o resultado. Se houver segunda máquina, usa-a para gerar carga e regista essa separação.

**No fim do dia:** pelo menos um conjunto de dados que consegues explicar e um gráfico preliminar.

### 11 de novembro - preparar a página e apresentar

Faz uma página com estes cinco blocos:

1. Pergunta e motivação;
2. Diagrama simples: gerador de carga → microserviço → stub HTTP;
3. O que já está implementado e o que ainda falta;
4. Configuração do piloto e gráfico preliminar;
5. Limitações encontradas e próximos passos.

Leva também uma demonstração curta do pedido a funcionar. Explica o que mediste, sem afirmar que o piloto prova qual modelo é melhor.

## Depois do dia 11

### Fase A - tornar a medição fiável

- Incorporar feedback do docente;
- Confirmar que o gerador não é o gargalo e, se possível, executá-lo noutra máquina;
- Automatizar as execuções e guardar configuração, logs e dados brutos;
- Definir duração, aquecimento e número de repetições com base no piloto;
- Variar a ordem dos modelos nas execuções para reduzir efeitos de ordem e carga de fundo.

### Fase B - responder à pergunta

- Completar primeiro a comparação por concorrência;
- Só depois testar latência variável/cauda longa, várias chamadas por pedido e trabalho de CPU;
- Acrescentar uma variável de cada vez para perceber o seu efeito;
- Reduzir a experiência se a quantidade de combinações não couber no calendário.

### Fase C - analisar e escrever

- Validar os dados e documentar qualquer execução descartada e a razão;
- Fazer gráficos de throughput e distribuições de latência (p50/p95/p99);
- Escolher e justificar o teste estatístico adequado ao desenho e aos dados; reportar tamanho do efeito e p-value;
- Escrever o artigo no template LaTeX do Moodle, com pelo menos 6 fontes;
- Incluir metodologia reproduzível, ameaças à validade e resposta explícita às perguntas;
- Reexecutar o processo seguindo apenas o README antes da entrega de 2 de dezembro.

## O que não fazer primeiro

- Não começar por escrever o artigo todo;
- Não implementar todos os valores de todas as variáveis antes de validar um pedido;
- Não comparar variantes que fazem trabalho diferente;
- Não recolher uma grande quantidade de números sem guardar configuração e dados brutos;
- Não tratar um piloto pequeno como resultado conclusivo.

## Checklist de saída para 11 de novembro

- [ ] Sei explicar a pergunta do projeto em duas frases.
- [ ] O serviço simulado responde.
- [ ] O microserviço chama o stub e devolve uma resposta.
- [ ] As três variantes estão executáveis ou o estado de cada uma está descrito com honestidade.
- [ ] Tenho dados piloto guardados e sei como foram recolhidos.
- [ ] Tenho pelo menos um gráfico preliminar.
- [ ] Consigo explicar o que ainda pode enviesar as medições.

## Documentos usados

Este guião segue o tema, as variantes e as variáveis da proposta, e os requisitos do enunciado para o checkpoint, artigo, avaliação e reprodutibilidade. O âmbito do piloto foi reduzido para caber nos dias disponíveis e produzir progresso demonstrável.
