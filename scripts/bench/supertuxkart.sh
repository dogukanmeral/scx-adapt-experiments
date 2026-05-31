#!/bin/false
# https://supertuxkart.net/Performance_testing

BENCHMARK_NAME='supertuxkart'
PROCESS_EXP='supertuxkart'
WARMUP_ITER=5

benchmark_warmup() {
    stress --cpu 12 > /dev/null 2>&1 & # Start CPU stress

    for ((i=0; i<WARMUP_ITER; i++)); do
        supertuxkart --benchmark > "/dev/null"
    done

    killall stress # Stop CPU stress
}

benchmark_prep() {
    :
}

benchmark_func() {
    entity_name_finder

    stress --cpu 12 > /dev/null 2>&1 & # Start CPU stress

    perf sched record -o "$LOGDIR"/perf.data supertuxkart --benchmark | grep "Profiler" >> "$LOGDIR"/"$BENCHMARK_NAME"_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$ENTITY_NAME"

    killall stress # Stop CPU stress
}

benchmark_cleanup() {
    pgrep stress > /dev/null && killall stress
}