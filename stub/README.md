# PPC — Modelos de Concorrência num Microserviço Java

## Pergunta de trabalho

> Como muda o throughput e a latência de um microserviço Java quando aumento o número de pedidos concorrentes, comparando platform threads, virtual threads e I/O assíncrono?

## Variantes implementadas

| Modo         | Descrição                                        | Estado |
| ------------ | -------------------------------------------------- | ------ |
| `platform` | Platform thread + chamada HTTP bloqueante          | 🔜     |
| `virtual`  | Virtual thread + chamada HTTP bloqueante           | 🔜     |
| `async`    | `HttpClient.sendAsync()` + `CompletableFuture` | 🔜     |

* [ ] Estrutura do projeto

```
ppc-project/
  pom.xml                          # Build Maven (Java 21 target)
  src/main/java/pt/fcul/ppc/
    PpcApplication.java            # Entry point Spring Boot
    StubController.java            # GET /stub — serviço simulado com atraso fixo
  src/main/resources/
    application.properties         # Configuração (porta, atraso do stub, modo)
  results/raw/                     # CSVs brutos das medições
  results/figures/                 # Gráficos
  scripts/                         # Scripts de automação de carga
  notes/experiment-log.md          # Log do ambiente e das experiências
  README.md                        # Este ficheiro
```

## Como arrancar

### Pré-requisitos

- Java 25 (ou 21+) instalado
- Maven 3.x

### Compilar

```bash
mvn package -DskipTests
```

### Correr (modo padrão)

```bash
mvn spring-boot:run
```

### Testar o stub manualmente

```bash
# Atraso padrão (50 ms, definido em application.properties)
curl http://localhost:8080/stub

# Atraso personalizado
curl "http://localhost:8080/stub?delayMs=200"
```

Resposta esperada:

```json
{
  "service": "stub",
  "delayMs": 50,
  "timestamp": "2026-11-07T10:00:00Z",
  "thread": "...",
  "message": "OK"
}
```

## Configuração do piloto (a preencher)

| Parâmetro                    | Valor        |
| ----------------------------- | ------------ |
| Atraso do stub                | 50 ms        |
| Ferramenta de carga           | —           |
| Níveis de concorrência      | 10, 100, 500 |
| Nº de pedidos por execução | —           |
| Aquecimento                   | —           |
| Repetições                  | —           |

## O que se mantém fixo em todas as variantes

- Uma única chamada HTTP por pedido ao `/stub`
- Mesma resposta e atraso fixo no stub
- Sem trabalho de CPU extra

## Limitações conhecidas

- Gerador de carga e servidor na mesma máquina: competição pelos recursos pode influenciar resultados.

## Referências

- Proposta do projeto (ppc_proposal_67991.pdf)
- Enunciado (statement.pdf)
