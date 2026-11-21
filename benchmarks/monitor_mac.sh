#!/bin/bash
# Regista a cada segundo a memória (RSS) e o CPU das JVMs do agregador e do stub.
# Correr no Mac antes de iniciar a série no Windows; parar com Ctrl+C no fim.
# Também impede o Mac de entrar em repouso enquanto estiver a correr.
#
# Uso:  ./monitor_mac.sh            (escreve em results/rq1_final/)

cd "$(dirname "$0")"
OUT_DIR="results/rq1_final"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/mac_monitor_$(date -u +%Y%m%d_%H%M%S).csv"

caffeinate -dims -w $$ &

echo "timestamp_utc,service,pid,rss_kb,cpu_percent,threads" > "$OUT"
echo "A registar em $OUT (Ctrl+C para parar)"

while true; do
    ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    ps -Ao pid=,rss=,%cpu=,command= | grep '[j]ava' | while read -r pid rss cpu cmd; do
        case "$cmd" in
            *aggregate*|*AggregateApplication*) svc="aggregate" ;;
            *stub*|*PpcApplication*)           svc="stub" ;;
            *) continue ;;
        esac
        threads=$(ps -M -p "$pid" 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
        echo "$ts,$svc,$pid,$rss,$cpu,$threads" >> "$OUT"
    done
    sleep 1
done
