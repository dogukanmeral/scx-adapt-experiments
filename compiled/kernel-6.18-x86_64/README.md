# Example schedulers

This directory contains the following example schedulers. These schedulers are
for testing and demonstrating different aspects of sched_ext. While some may be
useful in limited scenarios, they are not intended to be practical.

[sched_ext examples Linux kernel tree](https://github.com/torvalds/linux/tree/master/tools/sched_ext)

# scx_simple

- Can be run in either global weighted vtime mode, or FIFO mode.
- In limited scenarios, this scheduler can perform reasonably well on single-socket systems with a unified L3 cache.

# scx_qmap

- Provides a basic weighted FIFO queuing policy.
- Also provides examples of some common useful BPF features, such as sleepable per-task storage allocation in the `ops.prep_enable()` callback, and using the `BPF_MAP_TYPE_QUEUE` map type to
enqueue tasks.
- Also illustrates how core-sched support could be implemented.

# scx_central

- Scheduling decisions are made from a single CPU.
- Illustrates how scheduling decisions can be dispatched from a single CPU, allowing other cores to run with infinite slices, without timer ticks, and without having to incur the overhead of making scheduling decisions.
- May be useful for any workload that benefits from minimizing scheduling overhead and timer ticks.
    - Example: running VMs, where running with infinite slices and no timer ticks allows the VM to avoid unnecessary expensive vmexits.

# scx_flatcg

- Flattened cgroup hierarchy scheduler.
- Implements hierarchical weight-based cgroup CPU control by flattening the cgroup hierarchy into a single layer, by compounding the active weight share at each level.
    - The effect of this is a much more performant CPU controller, which does not need to descend down cgroup trees in order to properly compute a cgroup's share.
- In limited scenarios, this scheduler can perform reasonably well on single socket-socket systems with a unified L3 cache and show significantly lowered hierarchical scheduling overhead.