#!/bin/bash

set -e

BENCHMARK_NAME=git-compile
GIT_REPO_URL='https://github.com/git/git'
REPO_NAME=git
MAKE_THREADS=8
RESULTS_DIR="benchmarks"

cleanup () {
    echo 0 > /sys/devices/system/cpu/cpufreq/boost
    rm -rf cloned
}

echo 1 > /sys/devices/system/cpu/cpufreq/boost
cpupower frequency-set -g performance > /dev/null

if [ -e cloned ]; then
    rm -rf cloned
fi

git clone --depth=1 "$GIT_REPO_URL" cloned/"$REPO_NAME"

if [ -e "/sys/kernel/sched_ext/root/ops" ]; then
    printf "sched_ext is already active: %s\n" $(cat /sys/kernel/sched_ext/root/ops)
    cleanup
    exit 1
fi

mkdir -p "$RESULTS_DIR"

for SCHED_PATH in "$@"
do
    SCHED_NAME=$(basename $SCHED_PATH)
    COMPILE_DIR=cloned/"$SCHED_NAME"_"$REPO_NAME"


    git clone cloned/"$REPO_NAME" "$COMPILE_DIR"

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

    perf sched record -o "$LOGDIR"/perf.data \
        make --directory "$COMPILE_DIR" -j"$MAKE_THREADS" >> "$LOGDIR"/"$BENCHMARK_NAME"_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$SCHED_NAME"

    killall $SCHED_NAME || { printf "Error: Stopping scheduler %s\n" "$SCHED_NAME" ; exit 1; }

    lscpu > "$LOGDIR"/cpuinfo
    
    perf sched latency -i "$LOGDIR"/perf.data | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log
    perf sched latency -i "$LOGDIR"/perf.data | grep -E '\b(ln|cc|ld)\b' >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log

    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | grep -E '\b(ln|cc|ld)\b' >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log

    perf sched latency -i "$LOGDIR"/perf.data >> "$LOGDIR"/all_latency.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' >> "$LOGDIR"/all_timehist.log

    rm -f "$LOGDIR"/perf.data
done

cleanup