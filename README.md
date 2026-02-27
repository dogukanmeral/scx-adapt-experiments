# scx-adapt-experiments

Main purpose of `scx-adapt-experiments` is to create a testing and experimenting environment for the [scx-adapt](https://github.com/dogukanmeral/scx-adapt) project. It consists of scheduling data, profile .yaml file examples and data analysis of the scheduling metrics combined with system variables. Also includes Bash and Go scripts which control and check [sched_ext](https://sched-ext.com/docs/OVERVIEW) status and compile [BPF](https://serverspace.io/support/help/what-is-bpf-in-linux-and-how-does-it-work/) schedulers written in C to [BPF bytecode](https://blogs.oracle.com/linux/bpf-in-depth-the-bpf-bytecode-and-the-bpf-verifier).

## Further experiments

Currently we as project maintainers are searching for a method to create optimal configurations with existing schedulers using ML and AI technologies. If you have any idea-suggestion in that matter or any suggestionabout the tools, feel free to contact current maintainers [Onur Karagür](https://github.com/onurkaragur/) and [Doğukan Meral](https://github.com/dogukanmeral/).

## Repository layout

- scripts/: Scripts to create `vmlinux.h`, trace sched_ext events and control sched_ext.
    - /bpf: Bash scripts to start-stop-show-build sched_ext schedulers.
- sample-traces/: Trace files created using `ftrace` utility, which can be visualised and analysed using [Perfetto](https://ui.perfetto.dev/).
- sample-bpf/: Source code for sched_ext schedulers written in C with [libbpf](https://www.kernel.org/doc/html/latest/bpf/libbpf/libbpf_overview.html).
- datasets/: CSV files which contains values of system variables under specific workloads, while a specific scheduler is loaded to sched_ext. 