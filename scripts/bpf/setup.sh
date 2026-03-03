#!/bin/sh
# Generate the vmlinux.h file to start using in the IDE

bpftool btf dump file /sys/kernel/btf/vmlinux format c | tee sample-bpf/include/scx/vmlinux.h > sample-bpf/minimal-scheduler/vmlinux.h
