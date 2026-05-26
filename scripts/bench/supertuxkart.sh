#!/bin/false
# https://supertuxkart.net/Performance_testing

BENCHMARK_NAME='supertuxkart'
PROCESS_EXP='supertuxkart'

benchmark_prep() {
    :
}

benchmark_func() {
    stress --cpu 12 > /dev/null 2>&1 & # Start CPU stress

    perf sched record -o "$LOGDIR"/perf.data supertuxkart --benchmark | grep "Profiler" >> "$LOGDIR"/"$BENCHMARK_NAME"_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$SCHED_NAME"

    killall stress # Stop CPU stress
}

benchmark_cleanup() {
    :
}