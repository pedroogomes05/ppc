# Estado do Projeto PPC — Registo de Progresso e Próximos Passos

**Projeto:** Modelos de Concorrência num Microserviço Java  
**Data:** 8 de Novembro de 2026  
**Checkpoint / Apresentação:** 11 de Novembro de 2026  
**Entrega Final:** 2 de Dezembro de 2026  

---

## 1. O que foi feito nesta sessão

### 1.1 Configuração e Validação de Ambiente
- Verificada a instalação do Java: **Java 25 (LTS)** e **Maven 3.10.0**.
- Alinhado o target de compilação para **Java 21** no `pom.xml` para cumprir os requisitos da proposta.
- Resolvido o problema de validação de certificados SSL do Maven Central através de um truststore local dedicado configurado em cada módulo (`.mvn/jvm.config` e `.mvn/truststore.jks`), garantindo que o Maven compila e corre sem necessidade de flags manuais.
- Limpeza dos artefactos e scripts temporários usados na configuração de rede.

### 1.2 Módulo 1: O Serviço Simulado (`/stub`)
- Criado o projeto Spring Boot na pasta `c:\FCUL\PC\ppc\stub`.
- Implementado o endpoint `GET /stub`:
  - Simula um serviço externo lento aplicando latência artificial através de `Thread.sleep()`.
  - Atraso base configurável em `application.properties` (`stub.delay-ms=50`).
  - Suporta override de latência via parâmetro de query: `GET /stub?delayMs=200`.
  - Responde com JSON contendo: `service`, `delayMs`, `timestamp`, `thread` e `message`.
- Porta configurada: **8080**.
- Testado e validado em isolamento com tempos de resposta coerentes.

### 1.3 Módulo 2: O Agregador (`/aggregate`)
- Criado o projeto Spring Boot na pasta `c:\FCUL\PC\ppc\aggregate`.
- Porta configurada: **8081** (para permitir correr em simultâneo com o stub).
- Implementado um cliente HTTP partilhado e thread-safe (`java.net.http.HttpClient`).
- Implementados os **três modelos de concorrência** no mesmo serviço:

1. **Platform Threads (`GET /aggregate/platform`):**
   - Executa diretamente na thread do pool padrão do Tomcat.
   - Faz chamada bloqueante com `httpClient.send()`.
   - Demonstra a saturação de threads do SO sob concorrência.
2. **Virtual Threads (`GET /aggregate/virtual`):**
   - Cria uma Virtual Thread leve por tarefa (`Executors.newVirtualThreadPerTaskExecutor()`).
   - Faz a chamada bloqueante ao stub.
   - Enquanto espera por I/O, a carrier thread física (`ForkJoinPool-worker`) fica livre para executar outras tarefas.
3. **I/O Assíncrono com CompletableFuture (`GET /aggregate/async`):**
   - Dispara o pedido com `httpClient.sendAsync()`, que não bloqueia.
   - Devolve imediatamente um `CompletableFuture<Map<String, Object>>` ao Spring MVC.
   - A thread do Tomcat é libertada logo após o envio do pedido.
   - Quando o stub responde, o callback corre numa thread interna do `HttpClient` (`HttpClient-Worker`).
   - A resposta devolve `threadRequest` e `threadCompletion` separadamente como prova visual do funcionamento assíncrono.

### 1.4 Testes e Validação Prática de Concorrência
- Realizado teste com 30 pedidos paralelos em PowerShell:
  - **Platform:** alocou 30 threads distintas do Tomcat (`exec-1` até `exec-30`).
  - **Virtual:** gerou 30 Virtual Threads distintas multiplexadas em cima da **mesma carrier thread física** (`worker-3`).
- Ambos os projetos compilam a 100% via `mvn compile`.
- Documentação detalhada criada no `README.md` do agregador.

---

## 2. Estrutura Atual do Repositório

```text
c:\FCUL\PC\ppc\
├── plano_projeto.md          # Guião de orientação e cronograma
├── ppc_proposal_67991.pdf    # Proposta oficial assinada
├── statement.pdf             # Enunciado do trabalho
├── ESTADO_PROJETO.md         # Este documento resumo
├── stub\                     # Módulo do serviço externo simulado (Porta 8080)
│   ├── pom.xml
│   ├── .mvn/
│   │   ├── jvm.config
│   │   └── truststore.jks
│   ├── README.md
│   ├── notes/experiment-log.md
│   └── src/main/...
└── aggregate\                # Módulo agregador com os 3 modelos (Porta 8081)
    ├── pom.xml
    ├── .mvn/
    │   ├── jvm.config
    │   └── truststore.jks
    ├── README.md
    └── src/main/...
```

---

## 3. Próximos Passos Imediatos (Para o Checkpoint de 11 de Novembro)

O objetivo até dia 11 de Novembro é ter o **piloto executado e medido**, sem complicar com todas as variáveis da tese.

### Passo 1: Construir o Gerador de Carga
- Escolher a abordagem (script Python / k6 / wrk / PowerShell).
- O gerador deve permitir definir:
  - Concorrência de clientes (ex.: 10, 100, 500 pedidos concorrentes);
  - Duração do teste ou número fixo de pedidos;
  - Período de warm-up (aquecimento da JVM para estabilizar o JIT compiler).

### Passo 2: Executar o Teste Piloto Comparativo
- Correr os 3 endpoints nas mesmas condições:
  - `GET http://localhost:8081/aggregate/platform`
  - `GET http://localhost:8081/aggregate/virtual`
  - `GET http://localhost:8081/aggregate/async`
- Recolher e guardar em `results/raw/`:
  - **Throughput:** pedidos atendidos por segundo (req/s);
  - **Latência:** Percentis **p50**, **p95** e **p99**;
  - **Taxa de erro / timeouts.**

### Passo 3: Gerar Gráficos Preliminares
- Produzir 1 ou 2 gráficos simples (ex.: Concorrência vs Throughput, e Concorrência vs p99 de Latência).
- Guardar as figuras em `results/figures/`.

### Passo 4: Preparar Apresentação de 11 de Novembro
Elaborar 1 página / apresentação curta com os 5 blocos pedidos no guião:
1. Pergunta de investigação e motivação (RQ1 e RQ2);
2. Diagrama de arquitetura (`Gerador -> Agregador -> Stub`);
3. O que já está implementado (os 3 modelos funcionais);
4. Gráfico preliminar do piloto exploratório;
5. Limitações (ex.: servidor e gerador na mesma máquina) e próximos passos.

---

## 4. Passos Seguintes (Até à Entrega de 2 de Dezembro)

Após a apresentação de 11 de Novembro:
1. **Adicionar variáveis da proposta (RQ2):**
   - Latência variável e cauda longa no stub;
   - Múltiplas chamadas HTTP por pedido (1, 3 e 5);
   - Trabalho de CPU artificial (nenhum, moderado, alto) para testar a hipótese H2.
2. **Monitorização de Memória:** medir o consumo de RAM de Platform vs Virtual Threads.
3. **Execução Final Automatizada:** repetições para significância estatística.
4. **Artigo Final:** escrita no template LaTeX com análise estatística e referências bibliográficas.
