#!/bin/false

BENCHMARK_NAME=git-compile
PROCESS_EXP='\b(ln|cc|ld)\b'

GIT_REPO_URL='https://github.com/git/git'
REPO_NAME=git
MAKE_THREADS=8

benchmark_cleanup() {
    rm -rf cloned
}

benchmark_prep() {
    if [ -e cloned ]; then
        rm -rf cloned
    fi

    git clone --depth=1 "$GIT_REPO_URL" cloned/"$REPO_NAME"
}

benchmark_func() {
    COMPILE_DIR=cloned/"$SCHED_NAME"_"$REPO_NAME"
    git clone cloned/"$REPO_NAME" "$COMPILE_DIR"
 
    perf sched record -o "$LOGDIR"/perf.data \
        make --directory "$COMPILE_DIR" -j"$MAKE_THREADS" >> "$LOGDIR"/"$BENCHMARK_NAME"_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$SCHED_NAME"
}