/**
 * k6 benchmark for the PPC concurrency study.
 *
 * The runner performs a separate warm-up process and a 30-second measurement
 * process. This keeps warm-up and shutdown traffic out of the saved metrics.
 */

import http from 'k6/http';
import { check } from 'k6';

const MODE = __ENV.MODE || 'platform';
const VUS = Number.parseInt(__ENV.VUS || '10', 10);
const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8081').replace(/\/+$/, '');
const RUN_ID = __ENV.RUN_ID || 'manual';
const REPETITION = Number.parseInt(__ENV.REPETITION || '1', 10);
const STUB_DELAY_MS = Number.parseInt(__ENV.STUB_DELAY_MS || '1000', 10);
const TOMCAT_MAX_THREADS = Number.parseInt(__ENV.TOMCAT_MAX_THREADS || '200', 10);
const WARMUP = __ENV.WARMUP === 'true';
const RESULTS_DIR = (__ENV.RESULTS_DIR || 'results/raw_rq1')
    .replace(/\\/g, '/')
    .replace(/^\/+|\/+$/g, '');

const WARMUP_DURATION_SECONDS = 10;
const MEASUREMENT_DURATION_SECONDS = 30;

export const options = {
    // Each invocation uses a constant VU count. The runner invokes this script
    // once for warm-up and again for the measured 30-second interval.
    vus: VUS,
    duration: `${WARMUP ? WARMUP_DURATION_SECONDS : MEASUREMENT_DURATION_SECONDS}s`,
    gracefulStop: '15s',
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(50)', 'p(95)', 'p(99)'],
};

export default function () {
    const response = http.get(`${BASE_URL}/aggregate/${MODE}`, {
        timeout: '15s',
    });

    check(response, {
        'status 200': (r) => r.status === 200,
    });
}

export function handleSummary(data) {
    // Warm-up metrics are intentionally discarded.
    if (WARMUP) {
        return { stdout: '' };
    }

    const duration = data.metrics.http_req_duration?.values || {};
    const requests = data.metrics.http_reqs?.values || {};
    const failures = data.metrics.http_req_failed?.values || {};

    const p50 = duration['p(50)'] ?? duration.med ?? null;
    const p95 = duration['p(95)'] ?? null;
    const p99 = duration['p(99)'] ?? null;
    const average = duration.avg ?? null;
    const requestCount = requests.count ?? 0;
    const failureRate = failures.rate ?? 0;
    const roundMetric = (value) => value === null ? null : Number(Number(value).toFixed(2));

    // Divide by the planned steady-state interval, not by the warm-up or the
    // time needed to drain in-flight requests after the 30-second interval.
    const summary = {
        run_id: RUN_ID,
        repetition: REPETITION,
        mode: MODE,
        vus: VUS,
        base_url: BASE_URL,
        stub_delay_ms: STUB_DELAY_MS,
        tomcat_max_threads: TOMCAT_MAX_THREADS,
        measurement_duration_s: MEASUREMENT_DURATION_SECONDS,
        completed_at_utc: new Date().toISOString(),
        throughput: Number((requestCount / MEASUREMENT_DURATION_SECONDS).toFixed(2)),
        p50_ms: roundMetric(p50),
        p95_ms: roundMetric(p95),
        p99_ms: roundMetric(p99),
        avg_ms: roundMetric(average),
        error_rate: Number((failureRate * 100).toFixed(2)),
        total_requests: requestCount,
    };

    const outputFile = `${RESULTS_DIR}/${RUN_ID}_${MODE}_vus${VUS}.json`;
    const output = JSON.stringify(summary, null, 2);

    console.log(`\n=== Resultado: ${MODE} @ ${VUS} VUs (${RUN_ID}) ===`);
    console.log(`Throughput : ${summary.throughput} req/s`);
    console.log(`Latência   : p50=${summary.p50_ms}ms  p95=${summary.p95_ms}ms  p99=${summary.p99_ms}ms`);
    console.log(`Erros      : ${summary.error_rate}%`);
    console.log(`Guardado em: ${outputFile}\n`);

    return {
        [outputFile]: output,
        stdout: output,
    };
}
