#!/bin/bash
# https://www.postgresql.org/docs/current/pgbench.html 

set -e

BENCHMARK_NAME='pgbench'
RESULTS_DIR="benchmarks"

PGBENCH_DB='pgbench_db'
PGBENCH_SCALE=100
PGBENCH_CLIENT=15
PGBENCH_JOBS=8
PGBENCH_TRANSACTIONS=3000

cleanup () {
    echo 0 > /sys/devices/system/cpu/cpufreq/boost
    sudo -u postgres psql --command "DROP DATABASE $PGBENCH_DB"
}

echo 1 > /sys/devices/system/cpu/cpufreq/boost
cpupower frequency-set -g performance > /dev/null

if ! sudo -u postgres psql -lqt | grep $PGBENCH_DB; then
    sudo -u postgres psql --command "CREATE DATABASE $PGBENCH_DB"
fi

if [ -e "/sys/kernel/sched_ext/root/ops" ]; then
    printf "sched_ext is already active: %s\n" $(cat /sys/kernel/sched_ext/root/ops)
    cleanup
    exit 1
fi

mkdir -p "$RESULTS_DIR"

for SCHED_PATH in "$@"
do
    SCHED_NAME=$(basename $SCHED_PATH)

    LOGDIR="$RESULTS_DIR"/"$(date +%Y-%m-%d_%H:%M:%S)"_"$BENCHMARK_NAME"_"$SCHED_NAME"
    mkdir -p "$LOGDIR"
    
    if [ -e "$SCHED_PATH" ]; then
        "$SCHED_PATH" 1>"$LOGDIR"/"$SCHED_NAME".log 2>&1 &
    else
        printf "Scheduler not found at %s\n" "$SCHED_PATH"
        cleanup
        exit 1
    fi

    while [ ! -e "/sys/kernel/sched_ext/root/ops" ]
    do
        if ! pgrep "$SCHED_NAME" > /dev/null; then
            printf "Error: Starting scheduler %s\n" "$SCHED_NAME"
            continue 2
        fi
        sleep 1
    done
    
    printf "Scheduler attached: %s\n" "$SCHED_NAME"

    sudo -u postgres pgbench --initialize --scale="$PGBENCH_SCALE" "$PGBENCH_DB"

    perf sched record -o "$LOGDIR"/perf.data \
        sudo -u postgres pgbench \
        --client="$PGBENCH_CLIENT" \
        --jobs="$PGBENCH_JOBS" \
        --transactions="$PGBENCH_TRANSACTIONS" \
        "$PGBENCH_DB" >> "$LOGDIR"/"$BENCHMARK_NAME"_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$SCHED_NAME"

    killall $SCHED_NAME || { printf "Error: Stopping scheduler %s\n" "$SCHED_NAME" ; exit 1; }

    lscpu > "$LOGDIR"/cpuinfo
    
    perf sched latency -i "$LOGDIR"/perf.data | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log
    perf sched latency -i "$LOGDIR"/perf.data | grep "postgres" >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log

    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | grep "postgres" >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log

    perf sched latency -i "$LOGDIR"/perf.data >> "$LOGDIR"/all_latency.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' >> "$LOGDIR"/all_timehist.log

    rm -f "$LOGDIR"/perf.data
done

cleanup