#!/bin/sh
OBJ_FILE=$1

if [ "$1" = "--help" ]; then
    echo "Usage: ./start.sh scheduler_bytecode.o"
    # print all the available scheduler files in the directory
    echo "Available schedulers:"
    ls -1 bytecode/*
    exit 0
fi

./scripts/bpf/stop.sh

# Register the scheduler
bpftool struct_ops register ${OBJ_FILE} /sys/fs/bpf/sched_ext || (echo "Error attaching scheduler, consider calling stop.sh before" || exit 1)

# Print scheduler name, fails if it isn't registered properly
cat /sys/kernel/sched_ext/root/ops || (echo "No sched-ext scheduler installed" && exit 1)
