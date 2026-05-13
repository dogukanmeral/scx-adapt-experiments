# scx_beerland

## Overview
- Designed to prioritize locality and scalability.
- Uses separate DSQ (deadline ordered) for each CPU. Tasks get a chance to migrate only on wakeup, when the system is not saturated.
    - If the system becomes saturated, CPUs also start pulling tasks from the remote DSQs, always selecting the task with the smallest deadline.

## Typical use case
Cache-intensive workloads, systems with a large amount of CPUs.

# scx_bpfland

## Overview
- vruntime-based `sched_ext` scheduler that prioritizes interactive workloads.
- Derived from `scx_rustland`, but it is fully implemented in BPF.
    - It has a minimal user-space `Rust` part to process command line options, collect metrics and log out scheduling statistics.
    - The BPF part makes all the scheduling decisions.
- Tasks are categorized as either interactive or regular based on their average rate of voluntary context switches per second. 
    - Tasks that exceed a specific voluntary context switch threshold are classified as interactive.
    - Interactive tasks are prioritized in a higher-priority queue, while regular tasks are placed in a lower-priority queue.
    - Within each queue, tasks are sorted based on their weighted runtime: tasks that have higher weight (priority) or use the CPU for less time (smaller runtime) are scheduled sooner, due to their a higher position in the queue.
- Each task gets a time slice budget. When a task is dispatched, it receives a time slice equivalent to the remaining unused portion of its previously allocated time slice (with a minimum threshold applied).
    - This gives latency-sensitive workloads more chances to exceed their time slice when needed to perform short bursts of CPU activity without being interrupted (i.e., real-time audio encoding / decoding workloads).

## Typical use case
Interactive workloads, such as gaming, live streaming, multimedia, real-time audio encoding/decoding, especially when these workloads are running alongside CPU-intensive background tasks.

# scx_cosmos

## Overview
- Lightweight scheduler optimized for preserving task-to-CPU locality.
- When the system is not saturated, the scheduler prioritizes keeping tasks on the same CPU using local DSQs.
    - This not only maintains locality but also reduces locking contention compared to shared DSQs, enabling good scalability across many CPUs.
- Under saturation, the scheduler switches to a deadline-based policy and uses a shared DSQ (or per-node DSQs if NUMA optimizations are enabled).
    - This increases task migration across CPUs and boosts the chances for interactive tasks to run promptly over the CPU-intensive ones.
- To further improve responsiveness, the scheduler batches and defers CPU wakeups using a timer.
    - This reduces the task enqueue overhead and allows the use of very short time slices (10 us by default).
- The scheduler tries to keep tasks running on the same CPU as much as possible when the system is not saturated.

## Typical Use Case
The scheduler should adapt itself both for server workloads or desktop workloads.

# scx_flash

## Overview
- Focuses on ensuring fairness among tasks and performance predictability.
- Operates using an earliest deadline first (EDF) policy, where each task is assigned a "latency" weight.
    - This weight is dynamically adjusted based on how often a task release the CPU before its full time slice is used.
    - Tasks that release the CPU early are given a higher latency weight, prioritizing them over tasks that fully consume their time slice.

## Typical use case
- Combination of dynamic latency weights and EDF scheduling ensures responsive and consistent performance, even in overcommitted systems.
- Well-suited for latency-sensitive workloads, such as multimedia or real-time audio processing.

# scx_lavd

## Overview
- Implements an LAVD (Latency-criticality Aware Virtual Deadline) scheduling algorithm.
- While LAVD is new and still evolving, its core ideas are
  1. Measuring how much a task is latency critical
  2. Leveraging the task's latency-criticality information in making various scheduling decisions (e.g., task's deadline, time slice, etc.).
- LAVD is based on the foundation of deadline scheduling.
- BPF part makes all the scheduling decisions.
- Rust part provides high-level information (e.g., CPU topology) to the BPF code, loads the BPF code and conducts other chores (e.g., printing sampled scheduling decisions).

## Typical use case
Highly interactive applications, such as gaming, which requires high throughput and low tail latencies. Aims to improve interactivity and reduce stuttering while playing games. 

# scx_layered

## Overview
- Highly configurable multi-layer BPF / user space hybrid scheduler.
- Allows the user to classify tasks into multiple layers, and apply different scheduling policies to those layers.
    - For example, a layer could be created of all tasks that are part of the `user.slice` cgroup slice, and a policy could be specified that ensures that the layer is given at least 80% CPU utilization for some subset of CPUs on the system.
    
## Typical use case
- Designed to be highly customizable, and can be targeted for specific applications.
    - For example, if you had a high-priority service that required priority access to all but 1 physical core to ensure acceptable p99 latencies, you could specify that the service would get priority access to all but 1 core on the system.
    - If that service ends up not utilizing all of those cores, they could be used by other layers until they're needed.

## Tuning
<https://github.com/sched-ext/scx/tree/main/scheds/rust/scx_layered#tuning-scx_layered>

# scx_mitosis

## Overview
- cgroup-aware scheduler that isolates workloads into *cells*.
- Cgroups that restrict their parent's cpuset get their own *cell*—a dedicated CPU set with a shared dispatch queue.
    - Tasks within a cell are scheduled using weighted vtime.
    - CPU-pinned tasks (typically system threads) use per-CPU queues.
    - Cell and CPU tasks compete for dispatch based on their vtime.
- On multi-LLC systems, LLC-awareness keeps tasks on cache-sharing CPUs.
    - In this case, the single cell queue is split into multiple queues, one per LLC.

## Typical use case
The eventual goal is to enable overcomitting workloads on datacenter servers.

# scx_rustland

## Overview
- Based on `scx_rustland_core`, a BPF component that abstracts the low-level `sched_ext` functionalities.
- Designed to prioritize interactive workloads over background CPU-intensive workloads.
- The actual scheduling policy is entirely implemented in user space and it is written in Rust.

## Typical use case
- Low-latency interactive applications, such as gaming, video conferencing and live streaming.
- Designed to be an "easy to read" template that can be used by any developer to quickly experiment more complex scheduling policies fully implemented in Rust.

# scx_rusty

## Overview
- Multi-domain, BPF / user space hybrid scheduler.
    - BPF portion of the scheduler does a simple round robin in each domain
    - User space portion (written in Rust) calculates the load factor of each domain, and informs BPF of how tasks should be load balanced accordingly.

## Typical use case
- Designed to be flexible, accommodating different architectures and workloads.

## Tuning
- Various load balancing thresholds (e.g. greediness, frequency, etc), as well as how `scx_rusty` should partition the system into scheduling domains, can be tuned to achieve the optimal configuration for any given system or workload.

# scx_tickless

## Overview
- Server-oriented scheduler designed for cloud computing, virtualization, and high-performance computing workloads.
- Scheduler works by routing all scheduling events through a pool of primary CPUs assigned to handle these events.
    - This allows disabling the scheduler's tick on other CPUs, reducing OS noise.

## Typical use case

Cloud computing, virtualization and high performance computing workloads. This scheduler is not designed for latency-sensitive workloads.

## Tuning
- By default, only CPU 0 is included in the pool of primary CPUs. However, the pool size can be adjusted using the `--primary-domain CPUMASK` option.
    - On systems with a large number of CPUs, allocating multiple CPUs to the primary pool may be beneficial.
- In order to effectively disable ticks on the "tickless" CPUs the kernel must be booted with `nohz_full`. 
    - `nohz_full` introduces syscall overhead, so this may regress latency-sensitive workloads.