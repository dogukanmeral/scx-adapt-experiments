#!/bin/bash

# TODO: Add scheduler health-check
# TODO: Add traps

set -e

VALID_BENCH_TYPES=("scx-adapt" "sched_ext")

# helpers
contains() {
    local seeking="$1"
    shift

    for item in "$@"; do
        [[ "$item" == "$seeking" ]] && return 0
    done

    return 1
}

sched_ext_active_check() {
    if [ -e "/sys/kernel/sched_ext/root/ops" ]; then
        printf "sched_ext is already active: %s\n" "$(cat /sys/kernel/sched_ext/root/ops)"
        runner_cleanup
        exit 1
    fi
}

scx-adapt_active_check() {
    if [ -e "/var/lib/scx-adapt/scx-adapt.lock" ]; then
        printf "scx-adapt is already active, lock file exists"
        runner_cleanup
        exit 1
    fi
}

entity_name_finder() {
    if [ "$BENCHMARK_TYPE" = "scx-adapt" ]; then
        ENTITY_NAME="$CONFIG_NAME"
    elif [ "$BENCHMARK_TYPE" = "sched_ext" ]; then
        ENTITY_NAME="$SCHED_NAME"
    else
        printf "Entity name not in %s" "${VALID_BENCH_TYPES[@]}"
        runner_cleanup
        exit 1
    fi
}

# Argument parsing
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--benchmark)
            BENCHMARK_SCRIPT="$2"
            shift # Past argument
            shift # Past value
            ;;
        -t|--type)
            BENCHMARK_TYPE="$2"
            if ! contains "$BENCHMARK_TYPE" "${VALID_BENCH_TYPES[@]}"; then
                printf "Invalid benchmark type %s\n" "$BENCHMARK_TYPE"
                exit 1
            fi 
            shift # Past argument
            shift # Past value
            ;;
        -*)
            printf "Unknown option %s\n" "$1"
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1") # Save positional arg
            shift # Past argument
            ;;
    esac
done


set -- "${POSITIONAL_ARGS[@]}" # Restore positional parameters

for v in "$BENCHMARK_SCRIPT" "$BENCHMARK_TYPE"; do
    if [ -z "$v" ]; then
        printf "Requried argument missing: %s\n" "$v"
        exit 1
    fi
done

# These values are set in benchmark's script 
BENCHMARK_NAME=''
PROCESS_EXP=''

RESULTS_DIR='benchmarks'

mkdir -p "$RESULTS_DIR"

source "$BENCHMARK_SCRIPT"

for f in benchmark_prep benchmark_func benchmark_cleanup; do
    if ! declare -F "$f" >/dev/null; then
        printf "Function %s is not defined in %s\n" "$f" "$BENCHMARK_SCRIPT"
        exit 1
    fi
done

for v in "$BENCHMARK_NAME" "$PROCESS_EXP"; do
    if [ -z "$v" ]; then
        printf "Variable %s is not set in %s\n" "$v" "$BENCHMARK_SCRIPT"
        exit 1
    fi
done

runner_cleanup() {
    echo 0 > /sys/devices/system/cpu/cpufreq/boost
    benchmark_cleanup
}

echo 1 > /sys/devices/system/cpu/cpufreq/boost
cpupower frequency-set -g performance > /dev/null

benchmark_prep

perf_postproc() {
    lscpu > "$LOGDIR"/cpuinfo
    
    perf sched latency -i "$LOGDIR"/perf.data | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log
    perf sched latency -i "$LOGDIR"/perf.data | grep -E "$PROCESS_EXP" >> "$LOGDIR"/"$BENCHMARK_NAME"_latency.log

    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | head -n 4 >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' | grep -E "$PROCESS_EXP" >> "$LOGDIR"/"$BENCHMARK_NAME"_timehist.log

    perf sched latency -i "$LOGDIR"/perf.data >> "$LOGDIR"/all_latency.log
    perf sched timehist --with-summary -i "$LOGDIR"/perf.data | awk '/Runtime summary/{found=1} found' >> "$LOGDIR"/all_timehist.log

    rm -f "$LOGDIR"/perf.data
}

bench_run_sched_ext() {
    for SCHED_PATH in "$@"
    do
        sched_ext_active_check

        SCHED_NAME=$(basename "$SCHED_PATH")

        LOGDIR="$RESULTS_DIR"/"$(date +%Y-%m-%d_%H-%M-%S)"_"$BENCHMARK_NAME"_"$SCHED_NAME"_ext
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

        perf_postproc
    done
}

bench_run_scx-adapt() {
    for CONFIG_PATH in "$@"
    do
        sched_ext_active_check
        scx-adapt_active_check

        CONFIG_NAME=$(basename "$CONFIG_PATH" '.yaml')

        LOGDIR="$RESULTS_DIR"/"$(date +%Y-%m-%d_%H-%M-%S)"_"$BENCHMARK_NAME"_"$CONFIG_NAME"_adapt
        mkdir -p "$LOGDIR"

        if [ -e "$CONFIG_PATH" ]; then
            scx-adapt start-profile "$CONFIG_PATH" 1>"$LOGDIR"/"$CONFIG_NAME".log 2>&1 &
        else
            printf "YAML config not found at %s\n" "$CONFIG_PATH"
            runner_cleanup
            exit 1
        fi

        sleep 3

        if ! pgrep "scx-adapt" > /dev/null; then
            printf "Error: Starting scx-adapt configuration %s\n" "$CONFIG_PATH"
            continue
        fi

        printf "scx-adapt configuration attached: %s\n" "$CONFIG_NAME"

        benchmark_warmup
        benchmark_func

        killall "scx-adapt" || { printf "Error: Stopping scx-adapt configuration %s\n" "$CONFIG_PATH" ; runner_cleanup; exit 1; }

        perf_postproc
    done
}

case "$BENCHMARK_TYPE" in 
    "sched_ext")
        bench_run_sched_ext "$@"
        ;;
    "scx-adapt")
        bench_run_scx-adapt "$@"
        ;;
esac

runner_cleanup