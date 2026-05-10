#!/bin/sh
BPF_FILE=$1
BASE_FILE=$(basename ${BPF_FILE})
VMLINUX_H_PATH="sample-bpf/minimal-scheduler/vmlinux.h"

# Create the vmlinux header with all the eBPF Linux functions
# if it doesn'r exist
if [ ! -f $VMLINUX_H_PATH ]; then
    echo "Creating vmlinux.h"
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > $VMLINUX_H_PATH
fi

mkdir -p compiled/kernelonly

# Compile the scheduler
clang -target bpf -g -O2 -c $BPF_FILE -o compiled/kernelonly/${BASE_FILE}.o -Isample-bpf/include