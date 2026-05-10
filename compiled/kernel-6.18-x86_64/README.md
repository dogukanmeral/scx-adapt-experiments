# Example schedulers

This directory contains the following example schedulers. These schedulers are
for testing and demonstrating different aspects of sched_ext. While some may be
useful in limited scenarios, they are not intended to be practical.

For more scheduler implementations, tools and documentation, visit
https://github.com/sched-ext/scx.

## scx_simple

A simple scheduler that provides an example of a minimal sched_ext scheduler.
scx_simple can be run in either global weighted vtime mode, or FIFO mode.

Though very simple, in limited scenarios, this scheduler can perform reasonably
well on single-socket systems with a unified L3 cache.

## scx_qmap

Another simple, yet slightly more complex scheduler that provides an example of
a basic weighted FIFO queuing policy. It also provides examples of some common
useful BPF features, such as sleepable per-task storage allocation in the
`ops.prep_enable()` callback, and using the `BPF_MAP_TYPE_QUEUE` map type to
enqueue tasks. It also illustrates how core-sched support could be implemented.

## scx_central

A "central" scheduler where scheduling decisions are made from a single CPU.
This scheduler illustrates how scheduling decisions can be dispatched from a
single CPU, allowing other cores to run with infinite slices, without timer
ticks, and without having to incur the overhead of making scheduling decisions.

The approach demonstrated by this scheduler may be useful for any workload that
benefits from minimizing scheduling overhead and timer ticks. An example of
where this could be particularly useful is running VMs, where running with
infinite slices and no timer ticks allows the VM to avoid unnecessary expensive
vmexits.

## scx_flatcg

A flattened cgroup hierarchy scheduler. This scheduler implements hierarchical
weight-based cgroup CPU control by flattening the cgroup hierarchy into a single
layer, by compounding the active weight share at each level. The effect of this
is a much more performant CPU controller, which does not need to descend down
cgroup trees in order to properly compute a cgroup's share.

Similar to scx_simple, in limited scenarios, this scheduler can perform
reasonably well on single socket-socket systems with a unified L3 cache and show
significantly lowered hierarchical scheduling overhead.
