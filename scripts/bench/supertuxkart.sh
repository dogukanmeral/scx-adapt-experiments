#!/bin/bash

set -e

echo 1 > /sys/devices/system/cpu/cpufreq/boost
cpupower frequency-set -g performance > /dev/null

if [ -e "/sys/kernel/sched_ext/root/ops" ]; then
    printf "sched_ext is already active: %s\n" $(cat /sys/kernel/sched_ext/root/ops)
    exit 1
fi

RESULTS_DIR="benchmarks"
mkdir -p "$RESULTS_DIR"

for SCHED_PATH in "$@"
do
    SCHED_NAME=$(basename $SCHED_PATH)

    LOGDIR="$RESULTS_DIR"/"$(date +%Y-%m-%d_%H:%M:%S)"_supertuxkart_"$SCHED_NAME"
    mkdir -p "$LOGDIR"
    
    if [ -e "$SCHED_PATH" ]; then
        "$SCHED_PATH" 1>"$LOGDIR"/"$SCHED_NAME".log 2>&1 &
    else
        printf "Scheduler not found at %s\n" "$SCHED_PATH"
        echo 0 > /sys/devices/system/cpu/cpufreq/boost
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

    stress --cpu 12 > /dev/null 2>&1 & # Start CPU stress

    perf sched record -o "$LOGDIR"/perf.data supertuxkart --benchmark | grep "Profiler" >> "$LOGDIR"/supertux_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$SCHED_NAME"

    killall stress # Stop CPU stress

    killall $SCHED_NAME || { printf "Error: Stopping scheduler %s\n" "$SCHED_NAME" ; exit 1; }

    lscpu > "$LOGDIR"/cpuinfo
    
    perf sched latency -i "$LOGDIR"/perf.data | head -n 4 >> "$LOGDIR"/supertux_latency.log
    perf sched latency -i "$LOGDIR"/perf.data | grep "supertux" >> "$LOGDIR"/supertux_latency.log

    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | head -n 4 >> "$LOGDIR"/supertux_timehist.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | grep "supertux" >> "$LOGDIR"/supertux_timehist.log

    perf sched latency -i "$LOGDIR"/perf.data >> "$LOGDIR"/all_latency.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' >> "$LOGDIR"/all_timehist.log

    rm -f "$LOGDIR"/perf.data
done

echo 0 > /sys/devices/system/cpu/cpufreq/boost