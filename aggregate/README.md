# Aggregate — Microserviço Agregador

Microserviço que chama o serviço simulado (`/stub`) e devolve a resposta.
Implementa o mesmo percurso de três formas diferentes para comparar modelos de concorrência.

## Pergunta de investigação

> Como muda o throughput e a latência de um microserviço Java quando aumento
> o número de pedidos concorrentes, comparando platform threads, virtual threads
> e I/O assíncrono?

---

## Os três modelos de concorrência

### 1. Platform Threads — `GET /aggregate/platform`

**Como funciona:**
```
Pedido → Tomcat retira uma thread do pool fixo
       → thread executa httpClient.send() [BLOQUEANTE]
       → thread fica PARADA enquanto o stub "dorme"
       → stub responde → thread constrói resposta e devolve
```

**Comportamento chave:** cada pedido concorrente ocupa uma thread do pool.
O Tomcat tem por defeito **200 threads** no pool. Com 500 pedidos concorrentes,
300 ficam na fila à espera — o que faz o **p99 de latência disparar**.

**Resposta:**
```json
{
  "mode":         "platform",
  "thread":       "Thread[#44,http-nio-8081-exec-1,5,main]",
  "elapsedMs":    52,
  "stubStatus":   200,
  "stubResponse": "..."
}
```

---

### 2. Virtual Threads — `GET /aggregate/virtual`

**Como funciona:**
```
Pedido → Tomcat recebe numa platform thread
       → submete a tarefa ao executor partilhado de virtual threads
       → o controller devolve um CompletableFuture ao Spring MVC
       → Spring MVC liberta a thread do Tomcat enquanto aguarda
       → virtual thread executa httpClient.send() [BLOQUEANTE para a virtual thread]
       → quando bloqueia no I/O, a JVM DESMONTA a virtual thread do carrier thread
       → o carrier thread fica livre para executar outras virtual threads
       → stub responde → JVM remonta a virtual thread → constrói resposta
```

**Comportamento chave:** existe uma virtual thread por tarefa. Quando a chamada
HTTP bloqueia em I/O, a JVM pode libertar o carrier para executar outra tarefa;
o Spring MVC também mantém o pedido HTTP assíncrono em vez de prender a thread
do Tomcat à espera do resultado.

**Resposta:**
```json
{
  "mode":         "virtual",
  "thread":       "VirtualThread[#96]/runnable@ForkJoinPool-1-worker-3",
  "elapsedMs":    52,
  "stubStatus":   200,
  "stubResponse": "..."
}
```

> **Repara:** várias virtual threads podem aparecer no mesmo `worker-3` — a JVM
> multiplexou-as todas em cima de um único carrier thread físico.

---

### 3. I/O Assíncrono — `GET /aggregate/async`

**Como funciona:**
```
Pedido → Tomcat recebe numa platform thread (threadRequest)
       → httpClient.sendAsync() dispara pedido e devolve CompletableFuture IMEDIATAMENTE
       → thread do Tomcat é LIBERTADA (pode servir outros pedidos já)
       → Spring MVC regista callback no CompletableFuture e aguarda
       → stub responde → callback thenApply() corre numa thread do HttpClient (threadCompletion)
       → Spring MVC envia a resposta ao cliente
```

**Comportamento chave:** a thread do Tomcat **nunca bloqueia**. É libertada logo após
lançar o pedido HTTP. Com 10 000 pedidos concorrentes, o Tomcat consegue aceitá-los
todos com apenas ~200 threads, pois cada uma é usada por microsegundos (só para lançar
o pedido e receber a resposta), não durante os 50 ms de espera pelo stub.

**Resposta (tem DUAS threads — prova de que o modelo é assíncrono):**
```json
{
  "mode":             "async",
  "threadRequest":    "Thread[#44,http-nio-8081-exec-1,5,main]",
  "threadCompletion": "Thread[#60,HttpClient-1-Worker-0,5,main]",
  "elapsedMs":        52,
  "stubStatus":       200,
  "stubResponse":     "..."
}
```

> **`threadRequest` ≠ `threadCompletion`** — esta é a diferença visual fundamental
> do modelo assíncrono: a thread que recebeu o pedido não é a mesma que processou a resposta.

---

## Comparação dos três modelos

| | Platform | Virtual | Async |
|---|---|---|---|
| **Thread durante a chamada bloqueante ao stub** | 1 platform thread do Tomcat | 1 virtual thread (leve) | Chamada não bloqueante |
| **Bloqueia no I/O?** | ✅ Sim (platform thread parada) | ✅ Sim (mas o carrier é libertado) | ❌ Não (non-blocking) |
| **Limite prático** | ~200 pedidos concorrentes | Dezenas de milhar | Dezenas de milhar |
| **Pior métrica sob carga** | p99 dispara | p99 estável | p99 mais estável |
| **Complexidade do código** | Baixa | Baixa | Média |

---

## Como arrancar

> **Requisito:** o stub tem de estar a correr na porta 8080 antes de arrancar o agregador.

**Terminal 1 — Stub:**
```powershell
cd C:\FCUL\PC\ppc\stub
mvn spring-boot:run
```

**Terminal 2 — Agregador:**
```powershell
cd C:\FCUL\PC\ppc\aggregate
mvn spring-boot:run
```

O agregador arranca na porta **8081**.

---

## Como testar

```powershell
# Variante 1 — Platform thread
curl http://localhost:8081/aggregate/platform

# Variante 2 — Virtual thread
curl http://localhost:8081/aggregate/virtual

# Variante 3 — Async
curl http://localhost:8081/aggregate/async
```

### Teste de concorrência rápido (PowerShell)

```powershell
# Dispara 30 pedidos em paralelo — observa os nomes das threads
1..30 | ForEach-Object -Parallel {
    $r = Invoke-RestMethod -Uri "http://localhost:8081/aggregate/platform"
    $r.thread
} -ThrottleLimit 30

1..30 | ForEach-Object -Parallel {
    $r = Invoke-RestMethod -Uri "http://localhost:8081/aggregate/virtual"
    $r.thread
} -ThrottleLimit 30

1..30 | ForEach-Object -Parallel {
    $r = Invoke-RestMethod -Uri "http://localhost:8081/aggregate/async"
    "$($r.threadRequest)  -->  $($r.threadCompletion)"
} -ThrottleLimit 30
```

---

## Configuração

| Propriedade | Padrão | Descrição |
|---|---|---|
| `server.port` | `8081` | Porta do agregador |
| `stub.url` | `http://localhost:8080/stub` | URL do stub |

---

## Estrutura

```
aggregate/
  pom.xml
  .mvn/
    jvm.config          # SSL truststore (automático, não precisas de passar flags)
    truststore.jks      # Certificado para o Maven descarregar dependências
  src/main/java/pt/fcul/ppc/
    AggregateApplication.java    # Entry point + bean HttpClient partilhado
    AggregatorController.java    # GET /aggregate/{platform,virtual,async}
  src/main/resources/
    application.properties       # Porta 8081, URL do stub
  README.md                      # Este ficheiro
```
