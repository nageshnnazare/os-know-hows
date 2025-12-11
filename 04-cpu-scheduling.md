# Operating Systems - CPU Scheduling

## Table of Contents
1. [Basic Concepts](#basic-concepts)
2. [Scheduling Criteria](#scheduling-criteria)
3. [Scheduling Algorithms](#scheduling-algorithms)
4. [Multi-Level Queue Scheduling](#multi-level-queue-scheduling)
5. [Thread Scheduling](#thread-scheduling)
6. [Real-Time Scheduling](#real-time-scheduling)
7. [Algorithm Evaluation](#algorithm-evaluation)

---

## Basic Concepts

### CPU-I/O Burst Cycle

Process execution consists of alternating CPU and I/O bursts.

```
Process Execution Pattern:

CPU Burst I/O Burst CPU Burst I/O Burst CPU Burst
|████████| |------| |████████| |------| |████|
    ↓         ↓         ↓         ↓         ↓
  Computing  Waiting  Computing  Waiting   End
             for I/O              for I/O

Timeline:
+--------+----+--------+----+----+
|  CPU   | I/O|  CPU   | I/O|CPU |
|  Burst |    |  Burst |    |    |
+--------+----+--------+----+----+

CPU-Bound Process:
+---------------+---+---------------+
| Long CPU      |I/O| Long CPU      |
+---------------+---+---------------+

I/O-Bound Process:
+---+----+---+----+---+----+---+
|CPU| I/O|CPU| I/O|CPU| I/O|CPU|
+---+----+---+----+---+----+---+
```

### CPU Scheduler

Selects from ready queue which process gets CPU next.

```
READY QUEUE:

+-----+     +-----+     +-----+     +-----+
| P1  | --> | P3  | --> | P5  | --> | P7  |
+-----+     +-----+     +-----+     +-----+
              ↓
         CPU SCHEDULER
              ↓
         Dispatch to CPU
              ↓
            [CPU]
              ↓
    Process runs until:
    - Terminates
    - I/O request
    - Time quantum expires
    - Higher priority process arrives
              ↓
         Back to ready or waiting queue
```

### Preemptive vs Non-Preemptive

```
NON-PREEMPTIVE SCHEDULING:

Process runs until:           Timeline:
- Voluntarily releases CPU    P1      P2      P3
- Terminates                  |████████|██████|████████|
- Blocks on I/O               ↑              ↑        ↑
                              Runs until     Runs     Runs
                              completion     until    until
                                            blocked   done
No interruption once CPU
is allocated

Examples: Windows 3.x, Original Macintosh


PREEMPTIVE SCHEDULING:

OS can interrupt process:     Timeline:
- Timer interrupt            P1  P2  P1  P3  P2  P1
- Higher priority arrives    |██|██|███|██|███|██|
- After I/O completion       ↑  ↑  ↑           ↑
                             Switch points (forced)

Process can be switched out
anytime

Examples: Modern OS (Linux, Windows NT+, macOS)

Preemptive Advantages:
+ Better response time
+ Fairer CPU sharing
+ Prevents CPU hogging

Preemptive Challenges:
- Race conditions (shared data)
- Kernel mode interrupts
- More complex
```

### Dispatcher

Gives control of CPU to process selected by scheduler.

```
DISPATCHER FUNCTIONS:

1. Context Switch
   +-------------------+
   | Save state of     |
   | current process   |
   +-------------------+
          ↓
   +-------------------+
   | Load state of     |
   | selected process  |
   +-------------------+
          ↓
2. Switch to user mode
          ↓
3. Jump to proper location
   in user program
          ↓
   PROCESS RESUMES

Dispatch Latency:
Time taken to stop one process
and start another

+-----+-------+-----+
|Stop |Context|Start|
| P1  |Switch | P2  |
+-----+-------+-----+
  1μs    5μs    1μs
  └─────────────┘
  Dispatch Latency
  (Pure overhead)
```

---

## Scheduling Criteria

Metrics to evaluate scheduling algorithms:

### 1. CPU Utilization
Percentage of time CPU is busy.
```
Target: 40% (light) to 90% (heavy)

    Busy          Idle
|██████████| |----| 
      ↑          ↑
   Computing  Waiting

Utilization = Busy Time / Total Time
```

### 2. Throughput
Number of processes completed per time unit.
```
Example:
10 processes complete in 100 seconds
Throughput = 10/100 = 0.1 processes/second
```

### 3. Turnaround Time
Total time from submission to completion.
```
Process P1:
Submit  Admit   Start      Complete
  ↓      ↓       ↓            ↓
  |------|-------|████████████|
  0      2       5           15

Turnaround Time = Completion - Arrival
                = 15 - 0 = 15

Includes:
- Waiting in ready queue
- Executing on CPU
- I/O time
```

### 4. Waiting Time
Total time spent in ready queue.
```
Process execution:
Ready  Exec  Ready  Exec  Done
|----| |████| |---| |████| 
  3      2     2     3

Waiting Time = 3 + 2 = 5
(Only time in ready queue, not execution or I/O)
```

### 5. Response Time
Time from submission to first response.
```
Process P1:
Submit         First Response
  ↓                  ↓
  |------------------|████
  0                  8

Response Time = 8 - 0 = 8

Important for interactive systems!
Different from Turnaround Time
(first response vs. completion)
```

---

## Scheduling Algorithms

### 1. First-Come, First-Served (FCFS)

Simplest algorithm: processes served in order of arrival.

```
Process  Arrival  Burst
  P1       0        24
  P2       0         3
  P3       0         3

GANTT CHART:
+----+--+--+
| P1 |P2|P3|
+----+--+--+
0   24 27 30

Waiting Time:
P1: 0
P2: 24
P3: 27
Average: (0 + 24 + 27)/3 = 17

Turnaround Time:
P1: 24
P2: 27
P3: 30
Average: (24 + 27 + 30)/3 = 27
```

#### Convoy Effect

Short processes wait for long process.

```
With P1, P2, P3 (order above):
All short processes wait for P1
Average waiting: 17

If order was P2, P3, P1:
+--+--+----+
|P2|P3| P1 |
+--+--+----+
0  3  6   30

Waiting Time:
P2: 0
P3: 3
P1: 6
Average: (0 + 3 + 6)/3 = 3  Much better!

Convoy Effect: Long process holds up short ones
```

**Characteristics:**
- Non-preemptive
- Simple to implement
- Poor average waiting time
- No starvation (everyone eventually gets CPU)

### 2. Shortest Job First (SJF)

Process with shortest CPU burst gets CPU.

```
Process  Arrival  Burst
  P1       0        6
  P2       0        8
  P3       0        7
  P4       0        3

NON-PREEMPTIVE SJF:
+--+---+----+----+
|P4| P1| P3 | P2 |
+--+---+----+----+
0  3   9   16   24

Waiting Time:
P4: 0
P1: 3
P3: 9
P2: 16
Average: (0 + 3 + 9 + 16)/4 = 7

PREEMPTIVE SJF (SRTF - Shortest Remaining Time First):

Process  Arrival  Burst
  P1       0        8
  P2       1        4
  P3       2        9
  P4       3        5

Timeline:
T=0: P1 arrives (8)
T=1: P2 arrives (4), P1 has 7 left → Switch to P2
T=2: P3 arrives (9), P2 has 3 left → Continue P2
T=3: P4 arrives (5), P2 has 2 left → Continue P2
T=5: P2 done, select P4 (5 < 7 < 9)
...

+--+---+-----+----+----+
|P1|P2 | P4  | P1 | P3 |
+--+---+-----+----+----+
0  1   5    10   17   26

Waiting Time:
P1: (0-0) + (10-1) = 9
P2: (1-1) = 0
P3: (17-2) = 15
P4: (5-3) = 2
Average: (9 + 0 + 15 + 2)/4 = 6.5
```

**Characteristics:**
- Optimal: Minimum average waiting time
- Problem: Estimating burst time (use exponential averaging)
- Starvation possible for long processes
- Preemptive version called SRTF

**Estimating Next CPU Burst:**
```
Exponential Average:
τ(n+1) = α * t(n) + (1-α) * τ(n)

Where:
τ(n+1) = predicted next burst
t(n) = actual burst of nth instance
τ(n) = predicted nth burst
α = weight (typically 0.5)

Example:
τ(0) = 10 (initial guess)
t(0) = 6 (actual)
τ(1) = 0.5*6 + 0.5*10 = 8

t(1) = 4
τ(2) = 0.5*4 + 0.5*8 = 6

Recent history weighted more heavily
```

### 3. Priority Scheduling

Each process has priority; highest priority gets CPU.

```
Process  Burst  Priority
  P1      10      3
  P2       1      1  (highest)
  P3       2      4
  P4       1      5
  P5       5      2

NON-PREEMPTIVE PRIORITY:
+--+-----+----+---+--+
|P2| P5  | P1 |P3 |P4|
+--+-----+----+---+--+
0  1     6   16  18 19

PREEMPTIVE PRIORITY:

Process  Arrival  Burst  Priority
  P1       0        4      2
  P2       1        3      1  (highest)
  P3       2        1      3
  P4       3        5      4

T=0: P1 runs
T=1: P2 arrives (priority 1 > 2) → Preempt P1, run P2
T=4: P2 done, P1 resumes
T=5: P1 done, run P3
T=6: P3 done, run P4

+--+---+---+--+-----+
|P1|P2 |P1 |P3| P4  |
+--+---+---+--+-----+
0  1   4   5  6    11
```

**Problem: Starvation (Indefinite Blocking)**
```
High priority processes keep arriving:
P(pri=1), P(pri=1), P(pri=1), ...

Low priority process P(pri=5) waits forever!

   Ready Queue:
   +---+---+---+     +--------+
   |P1 |P2 |P3 | ... | P_low  | <-- Never gets CPU
   +---+---+---+     +--------+
   Pri Pri Pri       Pri=5
   =1  =1  =1
```

**Solution: Aging**
```
Increase priority of waiting processes over time:

Initial:  P1(pri=5, wait=0)
After 1s: P1(pri=4, wait=1)
After 2s: P1(pri=3, wait=2)
...
Eventually gets high enough priority to run

Aging Formula:
New_Priority = Initial_Priority - (Wait_Time / K)

Where K is aging factor
```

### 4. Round Robin (RR)

Each process gets small time quantum; rotate through processes.

```
Process  Burst
  P1      24
  P2       3
  P3       3

Time Quantum = 4

GANTT CHART:
+--+--+--+--+--+--+--+--+--+--+
|P1|P2|P3|P1|P1|P1|P1|P1|P1|  |
+--+--+--+--+--+--+--+--+--+--+
0  4  7 10 14 18 22 26 30

Execution:
T=0-4:   P1 (20 left) → back to queue
T=4-7:   P2 (0 left)  → done
T=7-10:  P3 (0 left)  → done
T=10-14: P1 (16 left) → back to queue
T=14-18: P1 (12 left) → back to queue
T=18-22: P1 (8 left)  → back to queue
T=22-26: P1 (4 left)  → back to queue
T=26-30: P1 (0 left)  → done

Waiting Time:
P1: (10-4) + (14-10) + (18-14) + (22-18) + (26-22) = 36
P2: 4
P3: 7
Average: (36 + 4 + 7)/3 = 15.67

Turnaround Time:
P1: 30
P2: 7
P3: 10
Average: (30 + 7 + 10)/3 = 15.67
```

**Effect of Time Quantum:**

```
SMALL TIME QUANTUM (q=1):
+--+--+--+--+--+--+...
|P1|P2|P3|P1|P2|P3|...
+--+--+--+--+--+--+...

Pros: Better response time
Cons: High context switch overhead

LARGE TIME QUANTUM (q=100):
+----------+------+------+
|    P1    |  P2  |  P3  |
+----------+------+------+

Pros: Low overhead
Cons: Degenerates to FCFS

OPTIMAL:
Time quantum should be large
compared to context switch time
Rule of thumb: 80% of bursts
should be shorter than quantum

Context Switch Time: 10ms
Good quantum: 100-200ms
```

**Performance Visualization:**

```
Average Turnaround Time vs Time Quantum:

TAT
 |
 |     *
 |    * *
 |   *   *
 |  *     *
 | *       *___
 |*            *___
 +-------------------> Time Quantum
   Small    Optimal  Large

Too small: Context switch overhead dominates
Too large: Poor response time (like FCFS)
Optimal: Balance between response and overhead
```

**Characteristics:**
- Preemptive (by timer)
- Fair: Every process gets equal CPU time
- No starvation
- Good for time-sharing systems
- Performance depends on quantum size

### 5. Multi-Level Feedback Queue

Multiple queues with different priorities and quanta.

```
MULTI-LEVEL FEEDBACK QUEUE EXAMPLE:

Queue 0 (Highest Priority) - Quantum = 8ms
+-----+-----+
| New | New |
+-----+-----+
   ↓ (if not finished)
   
Queue 1 (Medium Priority) - Quantum = 16ms
+-----+-----+-----+
| P1  | P2  | P3  |
+-----+-----+-----+
   ↓ (if not finished)
   
Queue 2 (Low Priority) - FCFS
+-----+-----+-----+-----+
| P4  | P5  | P6  | P7  |
+-----+-----+-----+-----+

Rules:
1. New processes enter Queue 0
2. If process uses full quantum, demoted to next queue
3. If process blocks or finishes before quantum, stays in same queue
4. Higher queue has priority
5. Process in lower queue runs only if higher queues empty
```

**Example Execution:**

```
Process  Burst
  P1      50
  P2       5
  P3      15

T=0: P1 arrives → Q0
T=0-8: P1 runs (q=8), not done → Demote to Q1
       Queue 0: []
       Queue 1: [P1]
       Queue 2: []

T=8: P2 arrives → Q0
T=8-13: P2 runs (5 < 8), done → Stays in Q0
       Queue 0: []
       Queue 1: [P1]
       Queue 2: []

T=13: P3 arrives → Q0
T=13-21: P3 runs (q=8), not done → Demote to Q1
       Queue 0: []
       Queue 1: [P1, P3]
       Queue 2: []

T=21-37: P1 runs (q=16), not done → Demote to Q2
T=37-44: P3 runs (7 < 16), done → Stays in Q1
T=44-70: P1 runs (FCFS in Q2), done

GANTT CHART:
+----+-----+----+------+----+-------+
| P1 | P2  | P3 | P1   | P3 |  P1   |
+----+-----+----+------+----+-------+
0    8    13   21     37   44      70
Q0   Q0   Q0   Q1     Q1   Q2
```

**Advantages:**
- Favors short processes (good response time)
- Favors I/O-bound processes
- Adapts to process behavior
- Prevents starvation (aging can move processes up)

**Configurable Parameters:**
- Number of queues
- Scheduling algorithm for each queue
- When to upgrade/downgrade processes
- Which queue new process enters

---

## Multi-Level Queue Scheduling

Processes permanently assigned to queues based on type.

```
MULTI-LEVEL QUEUE STRUCTURE:

+----------------------------------+
| System Processes (Highest)      |  Quantum=2, Priority=5
+----------------------------------+
             ↓ (if empty)
+----------------------------------+
| Interactive Processes           |  Quantum=4, Priority=4
+----------------------------------+
             ↓ (if empty)
+----------------------------------+
| Batch Processes (Lowest)        |  FCFS, Priority=1
+----------------------------------+

Each queue:
- Has own scheduling algorithm
- Has priority over lower queues
- May have different time quantum

Inter-queue scheduling:
a) Fixed Priority:
   Higher queue always runs first
   (can starve lower queues)

b) Time Slicing:
   Each queue gets percentage of CPU time
   Example: 
   - System: 20%
   - Interactive: 50%
   - Batch: 30%
```

**Example with Time Slicing:**

```
Queue     Type          %CPU  Algorithm
Q0       Foreground     80%   RR (q=10)
Q1       Background     20%   FCFS

Timeline (100ms total):
+----------------------------------------+----------+
|         Foreground (80ms)              | Back-    |
|                                        | ground   |
|                                        | (20ms)   |
+----------------------------------------+----------+
0                                       80         100

Even if Q1 has processes, Q0 gets 80% of time
```

---

## Thread Scheduling

### Process-Contention Scope (PCS)

Competition among threads within same process.

```
Process A:
+---+---+---+---+
| T1| T2| T3| T4|  User threads
+---+---+---+---+
      ↓
  Many-to-One or Many-to-Many
      ↓
+------------+
| Kernel     |  One or few kernel threads
| Thread(s)  |
+------------+

Library schedules T1-T4 onto kernel thread(s)
OS doesn't see user threads
```

### System-Contention Scope (SCS)

Competition among all threads in system.

```
Process A:              Process B:
+---+---+              +---+---+
| T1| T2|              | T3| T4|  User threads
+---+---+              +---+---+
  ↓   ↓                  ↓   ↓
+---+---+              +---+---+
| K1| K2|              | K3| K4|  Kernel threads
+---+---+              +---+---+
    ↓                      ↓
+-----------------------------------+
|    OS Scheduler                   |
|  Schedules all kernel threads     |
+-----------------------------------+
             ↓
          [CPU(s)]
```

### Pthread Scheduling

```c
#include <pthread.h>
#include <stdio.h>

pthread_attr_t attr;

// Get default attributes
pthread_attr_init(&attr);

// Set to PROCESS scope (PCS)
pthread_attr_setscope(&attr, PTHREAD_SCOPE_PROCESS);

// Or set to SYSTEM scope (SCS)
pthread_attr_setscope(&attr, PTHREAD_SCOPE_SYSTEM);

// Create thread with these attributes
pthread_create(&tid, &attr, runner, NULL);
```

---

## Real-Time Scheduling

Time constraints are critical; must meet deadlines.

### Hard vs Soft Real-Time

```
HARD REAL-TIME:
Task must complete before deadline (absolute requirement)

Deadline: 100ms
Task takes: 90ms  ✓ Success
Task takes: 110ms ✗ FAILURE (catastrophic)

Example: Airbag deployment, nuclear reactor control

SOFT REAL-TIME:
Task should complete before deadline (degraded if missed)

Deadline: 100ms
Task takes: 90ms  ✓ Good
Task takes: 110ms ~ Acceptable (degraded quality)

Example: Video streaming, audio playback
```

### Real-Time Scheduling Concepts

```
Task Parameters:

Processing Time (C):  Time to execute
Period (P):           Time between arrivals
Deadline (D):         Time by which must complete
Release Time (R):     Time when task becomes ready

Timeline:
R     D           R     D           R     D
↓     ↓           ↓     ↓           ↓     ↓
+-----+           +-----+           +-----+
|█████|           |█████|           |█████|
+-----+           +-----+           +-----+
0  C  P          P+C  2P          2P+C  3P

Periodic task: Repeats every P time units
```

### Rate Monotonic Scheduling (RMS)

Static priority based on period (shorter period = higher priority).

```
Tasks:
P1: Period=50ms,  Burst=20ms
P2: Period=100ms, Burst=35ms

Priority: P1 > P2 (shorter period)

Timeline:
+----+----+----+----+----+----+----+----+----+----+
|P1  |P2  |P1  |P2  |P1  |P2  |P1  |P2  |P1  |P2  |
+----+----+----+----+----+----+----+----+----+----+
0   20   55   75   90  110  130  165  185  200

         P1 deadline    P1 deadline    P1 deadline
             ✓              ✓              ✓
             |              |              |
            50ms          100ms          150ms

Schedulability Test:
U = Σ(C_i / P_i) ≤ n(2^(1/n) - 1)

Where:
U = CPU utilization
C_i = Computation time
P_i = Period
n = Number of tasks

For 2 tasks: Limit ≈ 0.828 (82.8%)

Example:
U = 20/50 + 35/100 = 0.4 + 0.35 = 0.75
0.75 < 0.828 → Schedulable!
```

### Earliest Deadline First (EDF)

Dynamic priority based on deadline (earlier deadline = higher priority).

```
Tasks:
P1: Period=50ms,  Burst=25ms
P2: Period=80ms,  Burst=35ms

Timeline (dynamic priorities):
T=0:   P1(D=50), P2(D=80) → P1 has priority
T=25:  P2(D=80) runs
T=50:  P1(D=100), P2(D=80) → P2 has priority
T=60:  P1(D=100) runs
...

GANTT CHART:
+-----+--------+-------+-----+--------+------+
| P1  |  P2    |  P2   | P1  |  P1    |  P2  |
+-----+--------+-------+-----+--------+------+
0    25       60      67    92      117     

Schedulability Test:
U = Σ(C_i / P_i) ≤ 1

Example:
U = 25/50 + 35/80 = 0.5 + 0.4375 = 0.9375
0.9375 < 1 → Schedulable!

EDF is optimal: If any algorithm can schedule, EDF can
```

### Priority Inversion Problem

```
Three processes:
P1 (High priority)
P2 (Medium priority)
P3 (Low priority)

Semaphore S (initially free)

T=0:   P3 runs, acquires S
T=1:   P1 arrives (preempts P3)
       P1 needs S → Blocked by P3
T=2:   P2 arrives (preempts P3)
       P2 doesn't need S, runs
T=10:  P2 done
T=11:  P3 resumes, releases S
T=12:  P1 runs

Problem: High priority P1 waits for medium priority P2!

Timeline:
+--+----+--------+--+
|P3| P1 |   P2   |P1|
|  |blk |        |  |
+--+----+--------+--+
0  1    2       10 12
   P1 waits (11 - 1 = 10ms)
   Effective priority inversion!

Solution: Priority Inheritance Protocol
When P3 holds resource needed by P1:
- P3 temporarily inherits P1's priority
- P3 can preempt P2
- When P3 releases S, priority returns to normal
```

---

## Algorithm Evaluation

### 1. Deterministic Modeling

Use specific workload and analyze.

```
Process  Arrival  Burst
  P1       0        10
  P2       0        1
  P3       0        2
  P4       0        1
  P5       0        5

FCFS: Average Wait = (0+10+11+13+14)/5 = 9.6ms
SJF:  Average Wait = (0+1+2+3+8)/5 = 2.8ms

Conclusion: SJF better for this workload
```

### 2. Queueing Models

Mathematical analysis using queueing theory.

```
Little's Formula:
L = λ × W

Where:
L = Average number in system
λ = Arrival rate (processes/second)
W = Average waiting time

Example:
λ = 10 processes/second arrive
W = 0.5 seconds average wait
L = 10 × 0.5 = 5 processes average in system

Utilization:
ρ = λ/μ

Where:
μ = Service rate (processes/second)

ρ < 1 for stable system
```

### 3. Simulation

Implement scheduling algorithms and run with trace data.

```
Simulator Components:

+----------------+
| Workload       |
| Generator      |
| (Trace/Random) |
+----------------+
        ↓
+----------------+
| Scheduling     |
| Algorithm      |
| Implementation |
+----------------+
        ↓
+----------------+
| Statistics     |
| Collection     |
| (Waiting time, |
|  Throughput,   |
|  etc.)         |
+----------------+

Run for millions of events
Collect statistics
Compare algorithms
```

### 4. Implementation

Implement in real system and measure.

```
Linux Completely Fair Scheduler (CFS):
- Tracks virtual runtime for each process
- Selects process with minimum vruntime
- Uses red-black tree for efficiency

Windows Scheduler:
- 32 priority levels
- Round-robin within each level
- Dynamic priority adjustment

Measurement:
- Profile real workloads
- Collect timing data
- Analyze performance
```

---

## Multi-Processor Scheduling

### Approaches

```
1. ASYMMETRIC MULTIPROCESSING:

       Master Processor
            (CPU 0)
              |
    All scheduling decisions
              |
    +----+----+----+----+
    |    |    |    |    |
   CPU0 CPU1 CPU2 CPU3
    |    |    |    |
  Execute processes

Simple, but master is bottleneck

2. SYMMETRIC MULTIPROCESSING (SMP):

Each CPU self-schedules:

Ready Queue (Common):
+---+---+---+---+
|P1 |P2 |P3 |P4 |
+---+---+---+---+
  ↓   ↓   ↓   ↓
+---+---+---+---+
|CPU|CPU|CPU|CPU|
| 0 | 1 | 2 | 3 |
+---+---+---+---+

More complex (need locks)
But better scalability

3. PER-CPU QUEUES:

CPU0 Queue:     CPU1 Queue:
+---+---+       +---+---+
|P1 |P2 |       |P3 |P4 |
+---+---+       +---+---+
  ↓               ↓
+-----+         +-----+
|CPU 0|         |CPU 1|
+-----+         +-----+

No contention for queue
But load imbalancing possible
Need load balancing (migration)
```

### Processor Affinity

Process prefers to run on same CPU.

```
WHY AFFINITY?

CPU 0                  CPU 1
+-------+              +-------+
| Cache |              | Cache |
+-------+              +-------+
    ↑                      ↑
    |                      |
Process P runs on CPU 0
Cache filled with P's data

If P moves to CPU 1:
- CPU 0 cache wasted (warm → cold)
- CPU 1 cache must be filled (cold → warm)
- Performance penalty

TYPES:

Soft Affinity:
OS tries to keep process on same CPU
But can migrate if needed

Hard Affinity:
Process pinned to specific CPU(s)
Cannot migrate

Linux:
taskset -c 0,1 ./myprogram
(Run on CPUs 0 and 1 only)
```

### Load Balancing

```
PUSH MIGRATION:
Periodic task checks load
Pushes processes from overloaded to idle CPUs

CPU 0 (4 processes)     CPU 1 (0 processes)
+---+---+---+---+            +---+
|P1 |P2 |P3 |P4 |    Push    |   |
+---+---+---+---+  ------->  +---+
     Overloaded               Idle

After:
CPU 0                   CPU 1
+---+---+               +---+---+
|P1 |P2 |               |P3 |P4 |
+---+---+               +---+---+
 Balanced               Balanced

PULL MIGRATION:
Idle CPU pulls process from busy CPU

CPU 0                   CPU 1 (idle)
+---+---+---+               +---+
|P1 |P2 |P3 |      Pull     |   |
+---+---+---+  <-----------+---+
     Busy                   Idle

Modern systems use both push and pull
```

---

## Summary Table

```
Algorithm      Preemptive  Starvation  Overhead  Use Case
----------------------------------------------------------------
FCFS           No          No          Low       Batch systems
SJF            No          Yes         Low       Known burst times
SRTF           Yes         Yes         Medium    Minimize avg wait
Priority       Yes/No      Yes         Medium    Prioritized tasks
RR             Yes         No          Medium    Time-sharing
Multi-Level    Yes         No          High      General purpose
RMS            Yes         No          Medium    Hard real-time
EDF            Yes         No          Medium    Real-time (optimal)
```

---

## Key Takeaways

- **FCFS**: Simple but suffers from convoy effect
- **SJF**: Optimal for minimizing average waiting time, but impractical
- **Priority**: Flexible but can cause starvation (use aging)
- **Round Robin**: Fair, good response time, quantum size critical
- **Multi-Level Feedback**: Adapts to process behavior, used in practice
- **Real-Time**: Hard deadlines (RMS, EDF), soft deadlines (similar)
- **Multi-Processor**: Affinity, load balancing, common vs per-CPU queues
- **Evaluation**: Deterministic, queueing, simulation, implementation

Modern OS (Linux, Windows) use complex multi-level feedback queues with sophisticated heuristics, priority adjustments, and load balancing.

---

**Next Topics:**
- File Systems
- Process Synchronization
- Deadlocks

