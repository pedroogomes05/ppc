/**
 * k6 benchmark for the PPC concurrency study.
 *
 * Warm-up and measurement run in the SAME k6 process, in one scenario:
 *   - warm-up (WARMUP_SECONDS): VUs ramp gradually from 0 to VUS, so TCP
 *     connections are opened a few at a time instead of all at once;
 *   - measurement (MEASUREMENT_SECONDS): VUS constant, connections already open.
 * Every request is tagged with phase=warmup|measure according to when it STARTED.
 * Only requests tagged phase=measure are reported.
 *
 * Errors in the measurement window are classified by type so they can be
 * diagnosed (timeout, network/connection, HTTP 5xx, other).
 */

import http from 'k6/http';
import exec from 'k6/execution';
import { Counter } from 'k6/metrics';

const MODE = __ENV.MODE || 'platform';
const VUS = Number.parseInt(__ENV.VUS || '10', 10);
const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8081').replace(/\/+$/, '');
const RUN_ID = __ENV.RUN_ID || 'manual';
const REPETITION = Number.parseInt(__ENV.REPETITION || '1', 10);
const STUB_DELAY_MS = Number.parseInt(__ENV.STUB_DELAY_MS || '1000', 10);
const TOMCAT_MAX_THREADS = Number.parseInt(__ENV.TOMCAT_MAX_THREADS || '200', 10);
const WARMUP_SECONDS = Number.parseInt(__ENV.WARMUP_SECONDS || '10', 10);
const MEASUREMENT_SECONDS = Number.parseInt(__ENV.MEASUREMENT_SECONDS || '30', 10);
const REQUEST_TIMEOUT = '15s';
const RESULTS_DIR = (__ENV.RESULTS_DIR || 'results/raw_rq1')
    .replace(/\\/g, '/')
    .replace(/^\/+|\/+$/g, '');

// Error counters (measurement window only) + one counter for warm-up errors.
const errTimeout = new Counter('err_timeout');
const errNetwork = new Counter('err_network');
const errHttp5xx = new Counter('err_http_5xx');
const errOther = new Counter('err_other');
const errWarmup = new Counter('err_warmup');

export const options = {
    scenarios: {
        main: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: `${WARMUP_SECONDS}s`, target: VUS },      // gradual warm-up
                { duration: `${MEASUREMENT_SECONDS}s`, target: VUS }, // steady measurement
            ],
            gracefulRampDown: '0s',
            gracefulStop: '20s', // let in-flight requests (timeout 15s) finish
        },
    },
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(50)', 'p(95)', 'p(99)'],
    // Thresholds that always pass: they only exist so that k6 exposes the
    // phase=measure sub-metrics in handleSummary().
    thresholds: {
        'http_req_duration{phase:measure}': ['max>=0'],
        'http_reqs{phase:measure}': ['count>=0'],
        'http_req_failed{phase:measure}': ['rate>=0'],
    },
};

export default function () {
    const elapsedMs = Date.now() - exec.scenario.startTime;
    const phase = elapsedMs < WARMUP_SECONDS * 1000 ? 'warmup' : 'measure';

    const res = http.get(`${BASE_URL}/aggregate/${MODE}`, {
        timeout: REQUEST_TIMEOUT,
        tags: { phase },
    });

    if (res.status === 200) {
        return;
    }
    if (phase === 'warmup') {
        errWarmup.add(1);
        return;
    }
    // k6 error codes: 1050 = request timeout; 1000-1999 = network/connection problems.
    if (res.error_code === 1050) {
        errTimeout.add(1);
    } else if (res.status === 0) {
        errNetwork.add(1);
        console.warn(`network error: code=${res.error_code} msg=${res.error}`);
    } else if (res.status >= 500) {
        errHttp5xx.add(1);
    } else {
        errOther.add(1);
        console.warn(`unexpected status ${res.status}`);
    }
}

export function handleSummary(data) {
    const metric = (name) => data.metrics[name]?.values || {};
    const duration = metric('http_req_duration{phase:measure}');
    const requests = metric('http_reqs{phase:measure}');
    const failures = metric('http_req_failed{phase:measure}');
    const count = (name) => metric(name).count ?? 0;

    const roundMetric = (value) => (value === null || value === undefined) ? null : Number(Number(value).toFixed(2));
    const requestCount = requests.count ?? 0;
    const failureRate = failures.rate ?? 0;
    const failedCount = Math.round(requestCount * failureRate);
    const okCount = requestCount - failedCount;

    // Throughput is divided by the planned measurement interval.
    const summary = {
        run_id: RUN_ID,
        repetition: REPETITION,
        mode: MODE,
        vus: VUS,
        base_url: BASE_URL,
        stub_delay_ms: STUB_DELAY_MS,
        tomcat_max_threads: TOMCAT_MAX_THREADS,
        warmup_duration_s: WARMUP_SECONDS,
        measurement_duration_s: MEASUREMENT_SECONDS,
        completed_at_utc: new Date().toISOString(),
        throughput: Number((requestCount / MEASUREMENT_SECONDS).toFixed(2)),
        throughput_ok: Number((okCount / MEASUREMENT_SECONDS).toFixed(2)),
        p50_ms: roundMetric(duration['p(50)'] ?? duration.med),
        p95_ms: roundMetric(duration['p(95)']),
        p99_ms: roundMetric(duration['p(99)']),
        avg_ms: roundMetric(duration.avg),
        max_ms: roundMetric(duration.max),
        error_rate: Number((failureRate * 100).toFixed(2)),
        total_requests: requestCount,
        ok_requests: okCount,
        errors: {
            timeout: count('err_timeout'),
            network: count('err_network'),
            http_5xx: count('err_http_5xx'),
            other: count('err_other'),
            warmup_errors: count('err_warmup'),
        },
    };

    const outputFile = `${RESULTS_DIR}/${RUN_ID}_${MODE}_vus${VUS}.json`;
    const output = JSON.stringify(summary, null, 2);

    console.log(`\n=== Resultado: ${MODE} @ ${VUS} VUs (${RUN_ID}) ===`);
    console.log(`Throughput : ${summary.throughput} req/s (ok: ${summary.throughput_ok} req/s)`);
    console.log(`Latência   : p50=${summary.p50_ms}ms  p95=${summary.p95_ms}ms  p99=${summary.p99_ms}ms`);
    console.log(`Erros      : ${summary.error_rate}% | ${JSON.stringify(summary.errors)}`);
    console.log(`Guardado em: ${outputFile}\n`);

    return {
        [outputFile]: output,
        stdout: output,
    };
}
