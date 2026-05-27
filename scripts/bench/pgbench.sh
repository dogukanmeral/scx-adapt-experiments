#!/bin/false
# https://www.postgresql.org/docs/current/pgbench.html 

BENCHMARK_NAME='pgbench'
PROCESS_EXP="postgres"

PGBENCH_DB='pgbench_db'
PGBENCH_SCALE=100
PGBENCH_CLIENT=15
PGBENCH_JOBS=8
PGBENCH_TRANSACTIONS=3000

benchmark_warmup() {
    :
}

benchmark_cleanup() {
    sudo -u postgres psql --command "DROP DATABASE $PGBENCH_DB"
}

benchmark_prep() {
    if ! sudo -u postgres psql -lqt | grep $PGBENCH_DB; then
        sudo -u postgres psql --command "CREATE DATABASE $PGBENCH_DB"
    fi
}

benchmark_func() {
    entity_name_finder

    sudo -u postgres pgbench --initialize --scale="$PGBENCH_SCALE" "$PGBENCH_DB"

    perf sched record -o "$LOGDIR"/perf.data \
        sudo -u postgres pgbench \
        --client="$PGBENCH_CLIENT" \
        --jobs="$PGBENCH_JOBS" \
        --transactions="$PGBENCH_TRANSACTIONS" \
        "$PGBENCH_DB" >> "$LOGDIR"/"$BENCHMARK_NAME"_out.log || \
        printf "Error: Scheduling performance recording %s\n" "$ENTITY_NAME"
}   