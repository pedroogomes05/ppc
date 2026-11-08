/**
 * Script de benchmark k6 — PPC
 */

import http from 'k6/http';
import { check } from 'k6';

// Lê variáveis de ambiente passadas pelo script de automação
const MODE     = __ENV.MODE     || 'platform';
const VUS      = parseInt(__ENV.VUS || '10');
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8081';

export const options = {
    // Garante que o k6 calcula explicitamente p(50), p(95), p(99)
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(50)', 'p(95)', 'p(99)'],
    stages: [
        // Fase 1: Warm-up — sobe gradualmente até ao nº de VUs alvo
        { duration: '10s', target: VUS },

        // Fase 2: Medição — mantém VUs constante durante 30 segundos
        { duration: '30s', target: VUS },

        // Fase 3: Descida gradual
        { duration: '5s',  target: 0   },
    ],
    thresholds: {
        http_req_failed:   ['rate<0.05'],
        http_req_duration: ['p(99)<10000'],
    },
};

export default function () {
    const res = http.get(`${BASE_URL}/aggregate/${MODE}`, {
        timeout: '15s',
    });

    check(res, {
        'status 200': (r) => r.status === 200,
    });
}

/**
 * handleSummary — exporta métricas de forma segura
 */
export function handleSummary(data) {
    const duration = data.metrics.http_req_duration ? data.metrics.http_req_duration.values : {};
    const reqs     = data.metrics.http_reqs ? data.metrics.http_reqs.values : {};
    const failed   = data.metrics.http_req_failed ? data.metrics.http_req_failed.values : {};

    // Helper para extrair valores com fallback seguro para 0.0
    const getVal = (obj, key) => {
        if (!obj || obj[key] === undefined || obj[key] === null) return 0.0;
        return parseFloat(Number(obj[key]).toFixed(2));
    };

    const p50 = duration['p(50)'] !== undefined ? duration['p(50)'] : (duration['med'] !== undefined ? duration['med'] : 0.0);
    const p95 = duration['p(95)'] !== undefined ? duration['p(95)'] : 0.0;
    const p99 = duration['p(99)'] !== undefined ? duration['p(99)'] : 0.0;
    const avg = duration['avg'] !== undefined ? duration['avg'] : 0.0;
    const rate = reqs['rate'] !== undefined ? reqs['rate'] : 0.0;
    const count = reqs['count'] !== undefined ? reqs['count'] : 0;
    const failRate = failed['rate'] !== undefined ? failed['rate'] * 100 : 0.0;

    const summary = {
        mode:           MODE,
        vus:            VUS,
        throughput:     parseFloat(Number(rate).toFixed(2)),
        p50_ms:         parseFloat(Number(p50).toFixed(2)),
        p95_ms:         parseFloat(Number(p95).toFixed(2)),
        p99_ms:         parseFloat(Number(p99).toFixed(2)),
        avg_ms:         parseFloat(Number(avg).toFixed(2)),
        error_rate:     parseFloat(Number(failRate).toFixed(2)),
        total_requests: count,
    };

    const outFile = `results/raw/${MODE}_vus${VUS}.json`;

    console.log(`\n=== Resultado: ${MODE} @ ${VUS} VUs ===`);
    console.log(`Throughput : ${summary.throughput} req/s`);
    console.log(`Latência   : p50=${summary.p50_ms}ms  p95=${summary.p95_ms}ms  p99=${summary.p99_ms}ms`);
    console.log(`Erros      : ${summary.error_rate}%`);
    console.log(`Guardado em: ${outFile}\n`);

    return {
        [outFile]: JSON.stringify(summary, null, 2),
        stdout:    JSON.stringify(summary, null, 2),
    };
}
