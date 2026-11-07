# Aggregate — Microserviço Agregador

Microserviço que chama o serviço simulado (`/stub`) e devolve a resposta.
Implementa o mesmo percurso de três formas diferentes para comparar modelos de concorrência.

## Endpoints

| Endpoint | Modo | Estado |
|---|---|---|
| `GET /aggregate/platform` | Platform thread + chamada bloqueante | ✅ Implementado |
| `GET /aggregate/virtual`  | Virtual thread + chamada bloqueante  | ✅ Implementado |
| `GET /aggregate/async`    | `HttpClient.sendAsync()` + `CompletableFuture` | 🔜 A implementar |

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

## Como testar

```powershell
# Variante 1 — Platform thread
curl http://localhost:8081/aggregate/platform

# Variante 2 — Virtual thread
curl http://localhost:8081/aggregate/virtual

# Variante 3 — Async (ainda não implementado)
curl http://localhost:8081/aggregate/async
```

### Resposta esperada (platform e virtual)

```json
{
  "mode":         "platform",
  "thread":       "Thread[#44,http-nio-8081-exec-1,5,main]",
  "elapsedMs":    52,
  "stubStatus":   200,
  "stubResponse": "{\"service\":\"stub\", \"delayMs\":50, ...}"
}
```

> **Dica:** compara o campo `thread` entre `/platform` e `/virtual`.
> - Platform: `Thread[#N, http-nio-8081-exec-N, ...]`
> - Virtual:  `VirtualThread[#N, ...]`

## Configuração

| Propriedade | Padrão | Descrição |
|---|---|---|
| `server.port` | `8081` | Porta do agregador |
| `stub.url` | `http://localhost:8080/stub` | URL do stub (muda se o stub estiver noutra máquina) |

Para alterar sem recompilar, usa argumentos na linha de comandos:
```powershell
mvn spring-boot:run -Dspring-boot.run.arguments="--stub.url=http://outra-maquina:8080/stub"
```

## Estrutura

```
aggregate/
  pom.xml
  src/main/java/pt/fcul/ppc/
    AggregateApplication.java    # Entry point + bean HttpClient
    AggregatorController.java    # GET /aggregate/{platform,virtual,async}
  src/main/resources/
    application.properties       # Porta 8081, URL do stub
```

## O que se mantém fixo em todas as variantes

- Uma única chamada HTTP por pedido ao stub
- Mesmo stub, mesmo atraso (50 ms por padrão)
- Sem trabalho de CPU extra
- Medição de `elapsedMs` com `System.nanoTime()`
