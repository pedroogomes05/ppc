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
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;

/**
 * Agregador — compara três modelos de concorrência no mesmo endpoint base.
 *
 * GET /aggregate/platform  → platform thread  + chamada HTTP bloqueante (baseline)
 * GET /aggregate/virtual   → virtual thread   + chamada HTTP bloqueante
 * GET /aggregate/async     → HttpClient.sendAsync() + CompletableFuture
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

    // =========================================================================
    // Variante 1 — Platform Thread (baseline)
    //
    // COMO FUNCIONA:
    //   1. O pedido HTTP chega ao Tomcat.
    //   2. O Tomcat retira uma thread do seu pool fixo (ex: exec-1, exec-2...)
    //      e entrega o pedido a essa thread.
    //   3. Essa thread executa doWork(): faz a chamada HTTP ao stub com
    //      httpClient.send() — um método BLOQUEANTE.
    //   4. Enquanto o stub está a "dormir" os 50 ms, a thread fica PARADA
    //      (bloqueada) sem fazer nada. Não pode ser usada para outros pedidos.
    //   5. Quando o stub responde, a thread constrói a resposta e devolve.
    //
    // IMPLICAÇÃO:
    //   Com um pool de 200 threads (limite padrão do Tomcat) e 500 pedidos
    //   concorrentes, os últimos 300 pedidos ficam numa fila de espera até
    //   que uma thread fique livre — o que faz a latência disparar (p99 alto).
    // =========================================================================
    @GetMapping("/platform")
    public Map<String, Object> handlePlatform() throws IOException, InterruptedException {
        return doWork("platform");
    }


    // =========================================================================
    // Variante 2 — Virtual Thread
    //
    // COMO FUNCIONA:
    //   1. O pedido HTTP chega ao Tomcat (numa platform thread do pool).
    //   2. Criamos um Executor especial que cria uma nova Virtual Thread
    //      por cada tarefa submetida.
    //   3. O trabalho (doWork) é submetido a essa Virtual Thread.
    //      A platform thread do Tomcat fica à espera que a virtual thread acabe.
    //   4. Quando a virtual thread bloqueia no I/O (httpClient.send()),
    //      a JVM DESMONTA essa virtual thread do seu carrier thread (uma
    //      thread real do OS) e usa esse carrier thread para executar
    //      outras virtual threads que estejam prontas.
    //   5. Quando o stub responde, a JVM remonta a virtual thread no carrier
    //      thread e ela termina o trabalho.
    //
    // IMPLICAÇÃO:
    //   Com 10.000 pedidos concorrentes podemos ter 10.000 virtual threads,
    //   mas o número de carrier threads (threads reais do OS) continua
    //   pequeno — igual ao nº de CPUs. Não há fila de espera por threads,
    //   apenas por carrier threads disponíveis (que são libertados no I/O).
    // =========================================================================
    @GetMapping("/virtual")
    public Map<String, Object> handleVirtual() throws Exception {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            return executor.submit(() -> doWork("virtual")).get();
        }
    }


    // =========================================================================
    // Variante 3 — Async (I/O Não-Bloqueante com CompletableFuture)
    //
    // COMO FUNCIONA:
    //   1. O pedido HTTP chega ao Tomcat (numa platform thread do pool).
    //   2. Criamos o pedido HTTP ao stub e chamamos sendAsync() —
    //      um método NÃO-BLOQUEANTE que devolve imediatamente um
    //      CompletableFuture (uma "promessa de resposta futura").
    //   3. A thread do Tomcat NÃO fica à espera! Em vez disso, retornamos
    //      o CompletableFuture ao Spring MVC. O Spring regista um callback
    //      e LIBERTA a thread do Tomcat imediatamente para servir outros pedidos.
    //   4. Quando o stub finalmente responde, o HttpClient usa o seu
    //      próprio thread pool interno para activar o callback (thenApply).
    //   5. É esse callback que constrói a resposta final.
    //
    // NOTA SOBRE AS THREADS NA RESPOSTA:
    //   "threadRequest"    — thread do Tomcat que recebeu o pedido (libertada imediatamente)
    //   "threadCompletion" — thread do HttpClient que processou a resposta do stub
    //   São SEMPRE threads diferentes — essa é a prova visual de que o modelo é assíncrono!
    //
    // IMPLICAÇÃO:
    //   O Tomcat consegue aceitar muito mais pedidos concorrentes porque as
    //   suas threads não ficam bloqueadas à espera de I/O. A thread só é usada
    //   no início (para lançar o pedido) e no fim (para enviar a resposta).
    // =========================================================================
    @GetMapping("/async")
    public CompletableFuture<Map<String, Object>> handleAsync() {
        // Capturamos a thread AGORA — antes de qualquer coisa assíncrona
        String requestThread = Thread.currentThread().toString();
        log.info("[async] Pedido recebido | thread={}", requestThread);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(stubUrl))
                .timeout(Duration.ofSeconds(10))
                .GET()
                .build();

        long start = System.nanoTime();

        // sendAsync() dispara o pedido HTTP e devolve IMEDIATAMENTE.
        // A thread do Tomcat fica livre — o Spring MVC aguarda o CompletableFuture.
        return httpClient
                .sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(response -> {
                    // Este código corre numa thread DIFERENTE (do pool interno do HttpClient),
                    // quando o stub finalmente responde.
                    long elapsedMs = (System.nanoTime() - start) / 1_000_000;
                    String completionThread = Thread.currentThread().toString();

                    log.info("[async] Resposta recebida | elapsedMs={} | completionThread={}",
                            elapsedMs, completionThread);

                    return Map.of(
                            "mode",             "async",
                            "threadRequest",    requestThread,    // thread do Tomcat (já foi libertada)
                            "threadCompletion", completionThread, // thread do HttpClient (processou a resposta)
                            "elapsedMs",        elapsedMs,
                            "stubStatus",       response.statusCode(),
                            "stubResponse",     response.body()
                    );
                });
    }


    // =========================================================================
    // Lógica comum às variantes bloqueantes (platform e virtual):
    //   1. Registar thread que está a tratar o pedido
    //   2. Fazer chamada bloqueante ao stub com httpClient.send()
    //   3. Medir tempo decorrido (System.nanoTime() para precisão)
    //   4. Devolver resultado com metadados da thread
    // =========================================================================
    private Map<String, Object> doWork(String mode) throws IOException, InterruptedException {
        String threadName = Thread.currentThread().toString();
        log.info("[{}] Pedido recebido | thread={}", mode, threadName);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(stubUrl))
                .timeout(Duration.ofSeconds(10))
                .GET()
                .build();

        long start = System.nanoTime();

        // BLOQUEANTE: a thread fica parada aqui até o stub responder
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
