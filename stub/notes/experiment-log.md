# Experiment Log — PPC

## Ambiente

| Item | Valor |
|------|-------|
| OS | Windows 10 (10.0 amd64) |
| Java | OpenJDK 25.0.5 (Temurin) — target de compilação: 21 |
| Maven | 3.10.0 |
| Locale | pt_PT / Europe/Lisbon |

> **Nota:** Java 25 é totalmente compatível com as funcionalidades usadas (virtual threads, CompletableFuture). O pom.xml usa `<java.version>21</java.version>` conforme o enunciado.

---

## 2026-11-07 — Arranque do projeto

- Criada estrutura de pastas do projeto
- Implementado `/stub` (StubController) com atraso configurável via `stub.delay-ms` ou parâmetro `?delayMs=`
- Compilação e arranque do stub a ser verificados

### Próximo passo
- Verificar stub com `curl http://localhost:8080/stub`
- Implementar endpoint `/aggregate` com platform threads (baseline)
