#!/bin/sh
BPF_FILE=$1
BASE_FILE=$(basename ${BPF_FILE})

# Create the vmlinux header with all the eBPF Linux functions
# if it doesn'r exist
if [ ! -f sample-bpf/include/scx/vmlinux.h ]; then
    echo "Creating vmlinux.h"
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > sample-bpf/include/scx/vmlinux.h
fi

# Compile the scheduler
clang -target bpf -g -O2 -c $BPF_FILE -o bytecode/${BASE_FILE}.o -Isample-bpf/include