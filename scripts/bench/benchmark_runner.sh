#!/bin/bash

# TODO: Add scheduler health-check

set -e

BENCHMARK_NAME=''
PROCESS_EXP=''

RESULTS_DIR='benchmarks'
BENCHMARK_SCRIPT="$1"
shift

mkdir -p "$RESULTS_DIR"

source "$BENCHMARK_SCRIPT"

for f in benchmark_prep benchmark_func benchmark_cleanup; do
    if ! declare -F "$f" >/dev/null; then
        printf "%s is not defined in %s\n" "$f" "$BENCHMARK_SCRIPT"
        exit 1
    fi
done

for v in "$BENCHMARK_NAME" "$PROCESS_EXP"; do
    if [ -z "$v" ]; then
        printf "Variable %s is not set in %s\n" "$v" "$BENCHMARK_SCRIPT"
        exit 1
    fi
done

if [ -e "/sys/kernel/sched_ext/root/ops" ]; then
    printf "sched_ext is already active: %s\n" "$(cat /sys/kernel/sched_ext/root/ops)"
    exit 1
fi

runner_cleanup() {
    echo 0 > /sys/devices/system/cpu/cpufreq/boost
    benchmark_cleanup
}

echo 1 > /sys/devices/system/cpu/cpufreq/boost
cpupower frequency-set -g performance > /dev/null

benchmark_prep

for SCHED_PATH in "$@"
do
    SCHED_NAME=$(basename "$SCHED_PATH")

    LOGDIR="$RESULTS_DIR"/"$(date +%Y-%m-%d_%H-%M-%S)"_"$BENCHMARK_NAME"_"$SCHED_NAME"
    mkdir -p "$LOGDIR"
    
    if [ -e "$SCHED_PATH" ]; then
        "$SCHED_PATH" 1>"$LOGDIR"/"$SCHED_NAME".log 2>&1 &
    else
        printf "Scheduler not found at %s\n" "$SCHED_PATH"
        runner_cleanup
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

    benchmark_func

    killall "$SCHED_NAME" || { printf "Error: Stopping scheduler %s\n" "$SCHED_NAME" ; exit 1; }

    lscpu > "$LOGDIR"/cpuinfo
    
    perf sched latency -i "$LOGDIR"/perf.data | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log
    perf sched latency -i "$LOGDIR"/perf.data | grep -E "$PROCESS_EXP" >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log

    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | grep -E "$PROCESS_EXP" >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log

    perf sched latency -i "$LOGDIR"/perf.data >> "$LOGDIR"/all_latency.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' >> "$LOGDIR"/all_timehist.log

    rm -f "$LOGDIR"/perf.data
done

runner_cleanup