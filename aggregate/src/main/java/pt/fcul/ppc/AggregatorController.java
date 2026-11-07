package pt.fcul.ppc;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.Executors;

/**
 * Agregador — compara três modelos de concorrência no mesmo endpoint base.
 *
 * GET /aggregate/platform  → platform thread  + chamada HTTP bloqueante (baseline)
 * GET /aggregate/virtual   → virtual thread   + chamada HTTP bloqueante
 * GET /aggregate/async     → HttpClient.sendAsync() + CompletableFuture  (a implementar)
 *
 * Em todos os casos o trabalho realizado é idêntico: uma chamada ao /stub.
 * Só o modelo de concorrência muda — é isso que queremos medir.
 */
@RestController
@RequestMapping("/aggregate")
public class AggregatorController {

    private static final Logger log = LoggerFactory.getLogger(AggregatorController.class);

    private final HttpClient httpClient;

    @Value("${stub.url:http://localhost:8080/stub}")
    private String stubUrl;

    public AggregatorController(HttpClient httpClient) {
        this.httpClient = httpClient;
    }

    // -------------------------------------------------------------------------
    // Variante 1 — Platform Thread (baseline)
    //
    // O pedido chega numa thread do pool do Tomcat (platform thread).
    // Durante o Thread.sleep() do stub, essa thread fica BLOQUEADA
    // e não pode ser usada para outros pedidos.
    // -------------------------------------------------------------------------
    @GetMapping("/platform")
    public Map<String, Object> handlePlatform() throws IOException, InterruptedException {
        return doWork("platform");
    }

    // -------------------------------------------------------------------------
    // Variante 2 — Virtual Thread
    //
    // O pedido chega numa platform thread do Tomcat, mas o trabalho
    // é submetido a uma virtual thread dedicada. Quando essa virtual
    // thread bloqueia no I/O (chamada ao stub), a carrier thread fica
    // livre para correr outras virtual threads — sem desperdiçar recursos.
    // -------------------------------------------------------------------------
    @GetMapping("/virtual")
    public Map<String, Object> handleVirtual() throws Exception {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            return executor.submit(() -> doWork("virtual")).get();
        }
    }

    // -------------------------------------------------------------------------
    // Variante 3 — Async (a implementar no próximo passo)
    // -------------------------------------------------------------------------
    @GetMapping("/async")
    public Map<String, Object> handleAsync() {
        return Map.of("mode", "async", "status", "not implemented yet");
    }

    // -------------------------------------------------------------------------
    // Lógica comum às três variantes:
    //   1. Registar thread que está a tratar o pedido
    //   2. Fazer chamada bloqueante ao stub
    //   3. Medir tempo decorrido
    //   4. Devolver resultado
    // -------------------------------------------------------------------------
    private Map<String, Object> doWork(String mode) throws IOException, InterruptedException {
        String threadName = Thread.currentThread().toString();
        log.info("[{}] Pedido recebido | thread={}", mode, threadName);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(stubUrl))
                .timeout(Duration.ofSeconds(10))
                .GET()
                .build();

        long start = System.nanoTime();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        log.info("[{}] Resposta recebida | elapsedMs={} | thread={}", mode, elapsedMs, threadName);

        return Map.of(
                "mode",         mode,
                "thread",       threadName,
                "elapsedMs",    elapsedMs,
                "stubStatus",   response.statusCode(),
                "stubResponse", response.body()
        );
    }
}
