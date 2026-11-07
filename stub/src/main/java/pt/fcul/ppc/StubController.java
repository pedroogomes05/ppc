package pt.fcul.ppc;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

/**
 * Serviço simulado (stub).
 *
 * Simula um serviço externo lento (ex: base de dados, API remota).
 * Aguarda um tempo configurável antes de responder, permitindo
 * controlar a latência artificial nos experimentos de concorrência.
 *
 * Endpoint: GET /stub
 *   - Parâmetro opcional: delayMs (substitui o valor do application.properties)
 *   - Resposta: JSON com timestamp, thread que tratou o pedido, e atraso aplicado
 */
@RestController
@RequestMapping("/stub")
public class StubController {

    private static final Logger log = LoggerFactory.getLogger(StubController.class);

    /** Atraso padrão em ms, lido de application.properties (stub.delay-ms=50) */
    @Value("${stub.delay-ms:50}")
    private long defaultDelayMs;

    /**
     * Simula uma chamada a um serviço externo com latência artificial.
     *
     * @param delayMs atraso em ms a aplicar neste pedido;
     *                se não for fornecido usa stub.delay-ms do application.properties
     * @return JSON com informação do pedido
     */
    @GetMapping
    public Map<String, Object> handle(
            @RequestParam(name = "delayMs", required = false) Long delayMs) throws InterruptedException {

        long actualDelay = (delayMs != null) ? delayMs : defaultDelayMs;
        String threadName = Thread.currentThread().toString();

        log.info("Stub recebeu pedido | delay={}ms | thread={}", actualDelay, threadName);

        // Simula a latência de rede / I/O
        Thread.sleep(actualDelay);

        log.info("Stub a responder | delay={}ms | thread={}", actualDelay, threadName);

        return Map.of(
                "service",   "stub",
                "delayMs",   actualDelay,
                "timestamp", Instant.now().toString(),
                "thread",    threadName,
                "message",   "OK"
        );
    }
}
