# Operating Systems - Performance Tuning and Monitoring

## Table of Contents
1. [Performance Metrics](#performance-metrics)
2. [CPU Performance](#cpu-performance)
3. [Memory Performance](#memory-performance)
4. [Disk I/O Performance](#disk-io-performance)
5. [Network Performance](#network-performance)
6. [Profiling Tools](#profiling-tools)
7. [Benchmarking](#benchmarking)
8. [Optimization Techniques](#optimization-techniques)

---

## Performance Metrics

### Key Performance Indicators

```
FUNDAMENTAL METRICS:

1. THROUGHPUT:
   Amount of work completed per unit time
   Examples:
   - Requests/second
   - Transactions/second
   - Bytes/second

2. LATENCY (Response Time):
   Time to complete single operation
   Examples:
   - Request latency: 50ms
   - Disk latency: 5ms
   - Network latency: 10ms

3. UTILIZATION:
   Percentage of time resource is busy
   Examples:
   - CPU utilization: 75%
   - Disk utilization: 40%
   - Memory utilization: 60%

4. SATURATION:
   Amount of work resource cannot handle (queue depth)
   Examples:
   - Run queue length: 2.5
   - Disk I/O queue: 10
   - Network buffer full

RELATIONSHIP:

High Utilization → Increased Latency → Reduced Throughput → Saturation

Optimal Zone:
Utilization: 60-80%
Low latency
High throughput
No saturation
```

### USE Method

```
USE: Utilization, Saturation, Errors

For every resource, check:

CPU:
- Utilization: % CPU time busy
- Saturation: Run queue length
- Errors: CPU errors

MEMORY:
- Utilization: Used vs total
- Saturation: Swap activity, page faults
- Errors: Memory errors (ECC)

DISK:
- Utilization: % time disk busy
- Saturation: I/O wait queue length
- Errors: Disk errors

NETWORK:
- Utilization: % bandwidth used
- Saturation: Dropped packets
- Errors: Network errors

EXAMPLE ANALYSIS:

System slow?

1. Check CPU Utilization: 95% (high!)
2. Check CPU Saturation: Run queue = 8 (saturated!)
3. Check CPU Errors: None

Diagnosis: CPU bottleneck
Action: Add CPUs or optimize code
```

---

## CPU Performance

### CPU Monitoring

```bash
TOOLS:

1. top / htop
   Real-time process monitor
   
   $ top
   
   PID USER %CPU %MEM COMMAND
   1234 user 98.5 2.1  python script.py
   
   Key metrics:
   - %CPU: CPU usage per process
   - load average: 1-min, 5-min, 15-min
   - wa: I/O wait percentage

2. vmstat
   Virtual memory statistics
   
   $ vmstat 1
   
   procs    cpu
   r  b   us sy id wa
   2  0   25 10 60  5
   
   r: Runnable processes (should be < #CPUs)
   b: Blocked processes
   us: User time
   sy: System time
   id: Idle time
   wa: I/O wait

3. mpstat
   Per-CPU statistics
   
   $ mpstat -P ALL 1
   
   CPU  %usr %sys %iowait %idle
   0    25.0 10.0   5.0  60.0
   1    30.0  8.0   2.0  60.0
   2    22.0  5.0   3.0  70.0
   
   Identifies CPU imbalance

4. pidstat
   Per-process statistics
   
   $ pidstat -p 1234 1
   
   %usr %system %CPU  Command
   45.0   5.0  50.0  python

LOAD AVERAGE INTERPRETATION:

Number of CPUs: 4

Load average: 2.0, 2.5, 3.0
- 1-min: 2.0 (50% utilized, good)
- 5-min: 2.5 (62% utilized, good)
- 15-min: 3.0 (75% utilized, acceptable)

Load average: 8.0, 8.5, 9.0
- All values > 4 (# CPUs)
- System saturated!
- Need to reduce load or add CPUs
```

### CPU Optimization

```
TECHNIQUES:

1. PROCESS PRIORITY (nice):
   
   $ nice -n 10 ./background_job
   (Run with lower priority)
   
   $ renice -n -5 -p 1234
   (Increase priority of existing process)
   
   Nice values: -20 (highest) to +19 (lowest)

2. CPU AFFINITY:
   
   Pin process to specific CPUs
   
   $ taskset -c 0,1 ./my_program
   (Run on CPUs 0 and 1 only)
   
   Benefits:
   - Better cache utilization
   - Predictable performance
   - NUMA optimization

3. CPU GOVERNOR:
   
   Control CPU frequency scaling
   
   $ cpupower frequency-info
   $ cpupower frequency-set -g performance
   
   Governors:
   - performance: Max frequency always
   - powersave: Min frequency
   - ondemand: Scale based on load
   - conservative: Gradual scaling

4. CONTEXT SWITCH REDUCTION:
   
   $ perf stat -e context-switches ./my_program
   
   High context switches → Performance degradation
   
   Reduce by:
   - Fewer threads
   - Longer time slices
   - Thread affinity

EXAMPLE: Optimize CPU-bound application

# Before optimization
$ time ./my_program
real    0m30.5s
user    0m28.2s
sys     0m1.8s

# Analysis
$ perf stat ./my_program
30,000,000 context-switches  (high!)
95% CPU cache misses  (bad!)

# Optimization 1: Set CPU affinity
$ taskset -c 0-3 ./my_program

# Optimization 2: Set governor
$ sudo cpupower frequency-set -g performance

# After optimization
$ time ./my_program
real    0m22.1s  (27% faster!)
user    0m21.8s
sys     0m0.2s
```

---

## Memory Performance

### Memory Monitoring

```bash
TOOLS:

1. free
   Memory usage summary
   
   $ free -h
                total   used   free  shared  buffers  cached
   Mem:           8.0G   6.5G   1.5G   100M     200M    3.0G
   Swap:          2.0G   500M   1.5G
   
   Available = free + buffers + cached (mostly)
   Real used = used - buffers - cached

2. vmstat
   Memory statistics
   
   $ vmstat 1
   
   memory          swap
   free  buff cache  si  so
   1500  200  3000   0   10
   
   si: Swap in (pages/sec)
   so: Swap out (pages/sec)
   
   Non-zero swap activity → Memory pressure!

3. /proc/meminfo
   Detailed memory info
   
   $ cat /proc/meminfo
   MemTotal:        8192000 kB
   MemFree:         1500000 kB
   MemAvailable:    4700000 kB
   Buffers:          200000 kB
   Cached:          3000000 kB
   SwapTotal:       2048000 kB
   SwapFree:        1500000 kB

4. smem
   Per-process memory usage
   
   $ smem -tk
   PID  User  Command           USS     PSS     RSS
   1234 user  python          500M    550M    600M
   
   USS: Unique Set Size (private memory)
   PSS: Proportional Set Size (shared divided)
   RSS: Resident Set Size (total in RAM)

PAGE FAULT MONITORING:

$ ps -o pid,min_flt,maj_flt,cmd 1234

PID  MINFLT  MAJFLT  CMD
1234  50000     100   python script.py

MINFLT: Minor faults (page in memory)
MAJFLT: Major faults (page on disk, requires I/O)

High MAJFLT → Memory pressure, swapping
```

### Memory Optimization

```
TECHNIQUES:

1. REDUCE MEMORY USAGE:
   
   # Find memory hogs
   $ ps aux --sort=-%mem | head -10
   
   Optimization:
   - Reduce working set
   - Use memory-efficient data structures
   - Free unused memory

2. TUNE VM PARAMETERS:
   
   # Swappiness (0-100)
   $ cat /proc/sys/vm/swappiness
   60
   
   $ sudo sysctl vm.swappiness=10
   (Reduce swapping, keep more in RAM)
   
   # Dirty page writeback
   $ sudo sysctl vm.dirty_ratio=15
   $ sudo sysctl vm.dirty_background_ratio=5
   
   (Control when dirty pages written to disk)

3. HUGE PAGES:
   
   Enable transparent huge pages
   
   $ cat /sys/kernel/mm/transparent_hugepage/enabled
   [always] madvise never
   
   Benefits:
   - Fewer TLB misses
   - Lower page table overhead
   - Better for large memory applications

4. NUMA OPTIMIZATION:
   
   $ numactl --hardware
   
   node 0: CPUs 0-3, Memory 4GB
   node 1: CPUs 4-7, Memory 4GB
   
   # Run on specific NUMA node
   $ numactl --cpunodebind=0 --membind=0 ./my_program
   
   Benefits:
   - Local memory access (faster)
   - Avoid remote memory access

5. MEMORY COMPRESSION (zRAM):
   
   Compress pages before swapping to disk
   
   $ sudo modprobe zram
   $ sudo zramctl
   
   Faster than disk swap
   Good for systems with limited RAM

EXAMPLE: Reduce memory usage

# Before
$ free -h
Mem:  8G   7.5G  500M  (93% used!)
Swap: 2G   1.5G  500M  (swapping heavily!)

# Identify memory hogs
$ ps aux --sort=-%mem | head -5
USER   %MEM  COMMAND
user1  25.0  java -Xmx2G app.jar
user2  15.0  python ml_model.py
user3  10.0  chrome

# Optimization 1: Reduce Java heap
$ java -Xmx1G app.jar  (was -Xmx2G)

# Optimization 2: Drop caches (if safe)
$ sudo sync
$ sudo sysctl vm.drop_caches=3

# After
$ free -h
Mem:  8G   5.0G  3.0G  (62% used, better!)
Swap: 2G   100M  1.9G  (minimal swapping)
```

---

## Disk I/O Performance

### I/O Monitoring

```bash
TOOLS:

1. iostat
   Disk I/O statistics
   
   $ iostat -x 1
   
   Device  rrqm/s wrqm/s  r/s  w/s  rMB/s  wMB/s  %util
   sda       0.0    2.0  10   50    0.5    2.0     45
   
   Key metrics:
   - r/s, w/s: Reads/writes per second
   - rMB/s, wMB/s: Throughput
   - %util: Utilization (high → bottleneck)
   - await: Average I/O wait time (ms)
   
   %util > 80%  + high await → I/O bottleneck!

2. iotop
   Per-process I/O usage
   
   $ sudo iotop
   
   TID  DISK READ  DISK WRITE  COMMAND
   1234    10 MB/s     50 MB/s  python backup.py
   
   Identifies I/O-heavy processes

3. ioping
   Disk latency test
   
   $ ioping -c 10 /dev/sda
   
   4096 bytes from /dev/sda: time=0.5 ms
   4096 bytes from /dev/sda: time=0.6 ms
   ...
   
   Shows disk response time

4. blktrace
   Detailed block I/O tracing
   
   $ sudo blktrace -d /dev/sda -o trace
   $ blkparse trace
   
   Shows every I/O request to disk

IDENTIFY I/O PATTERNS:

Sequential:
Request 1: Sector 1000-1100
Request 2: Sector 1101-1200
Request 3: Sector 1201-1300
(Good for HDDs)

Random:
Request 1: Sector 1000
Request 2: Sector 50000
Request 3: Sector 2000
(Bad for HDDs, OK for SSDs)
```

### I/O Optimization

```
TECHNIQUES:

1. I/O SCHEDULER:
   
   $ cat /sys/block/sda/queue/scheduler
   noop deadline [cfq] mq-deadline
   
   Schedulers:
   - noop: No reordering (good for SSDs)
   - deadline: Deadline-based (balanced)
   - cfq: Completely Fair Queueing (default)
   - mq-deadline: Multi-queue deadline (modern)
   
   Change:
   $ echo deadline | sudo tee /sys/block/sda/queue/scheduler

2. READ-AHEAD:
   
   $ sudo blockdev --getra /dev/sda
   256  (sectors)
   
   $ sudo blockdev --setra 512 /dev/sda
   (Increase read-ahead for sequential workloads)

3. FILESYSTEM TUNING:
   
   Mount options:
   $ mount -o noatime,nodiratime /dev/sda1 /mnt
   
   - noatime: Don't update access time (faster)
   - nodiratime: Don't update dir access time
   - data=writeback: Don't wait for data writes (ext4)
   
   Warning: Some options reduce data safety!

4. USE BUFFERED I/O:
   
   Buffered (cached):
   $ dd if=/dev/zero of=file bs=1M count=1000
   (Uses page cache, faster)
   
   Direct I/O (unbuffered):
   $ dd if=/dev/zero of=file bs=1M count=1000 oflag=direct
   (Bypass cache, slower but predictable)

5. BATCH I/O OPERATIONS:
   
   Bad:
   for file in files:
       open(file)
       read()
       close()
   
   Good:
   open all files
   read all data
   close all files
   
   Reduces syscall overhead

6. SOLID STATE DRIVE OPTIMIZATION:
   
   # Enable TRIM
   $ sudo fstrim -v /
   
   # Or enable periodic TRIM
   $ sudo systemctl enable fstrim.timer
   
   # Check SSD health
   $ sudo smartctl -a /dev/sda

EXAMPLE: Optimize database I/O

# Before
$ iostat -x 1
Device  %util  await  r/s  w/s
sda      95%   100ms  500  500
(Very high utilization and latency!)

# Analysis
$ iotop
MySQL: 80% of disk I/O (random access)

# Optimization 1: Change I/O scheduler
$ echo deadline | sudo tee /sys/block/sda/queue/scheduler

# Optimization 2: Increase InnoDB buffer pool
my.cnf:
innodb_buffer_pool_size = 4G  (was 1G)

# Optimization 3: Move to SSD
(If possible, SSDs much better for random I/O)

# After
$ iostat -x 1
Device  %util  await  r/s   w/s
sda      65%    15ms  800  800
(Better utilization and latency!)
```

---

## Network Performance

### Network Monitoring

```bash
TOOLS:

1. netstat / ss
   Network statistics
   
   $ ss -s
   Total: 1000 TCP sockets
   Time-wait: 50
   Established: 200
   
   $ ss -tuln
   (Show listening ports)

2. iftop
   Real-time bandwidth monitor
   
   $ sudo iftop -i eth0
   
   Shows:
   - Source → Destination traffic
   - Bandwidth usage
   - Cumulative totals

3. nethogs
   Per-process bandwidth usage
   
   $ sudo nethogs eth0
   
   PID  PROGRAM          SENT    RECEIVED
   1234 firefox        1.5 MB/s   10 MB/s
   5678 rsync         50 MB/s     0 MB/s

4. nload
   Network load visualization
   
   $ nload eth0
   
   Shows incoming/outgoing traffic graphically

5. tcpdump / Wireshark
   Packet capture and analysis
   
   $ sudo tcpdump -i eth0 port 80
   (Capture HTTP traffic)

BANDWIDTH TEST:

$ iperf3 -s  (server)
$ iperf3 -c server_ip  (client)

[  ID] Interval       Transfer     Bandwidth
[   5]  0.0-10.0 sec  1.10 GBytes   944 Mbits/sec

LATENCY TEST:

$ ping -c 10 8.8.8.8
10 packets transmitted, 10 received
rtt min/avg/max = 10.5/15.2/25.1 ms
```

### Network Optimization

```
TECHNIQUES:

1. TCP TUNING:
   
   # Increase TCP window size
   $ sudo sysctl net.ipv4.tcp_rmem='4096 87380 16777216'
   $ sudo sysctl net.ipv4.tcp_wmem='4096 65536 16777216'
   
   Larger windows = better throughput on high-latency links

2. NETWORK BUFFER TUNING:
   
   # Increase buffer sizes
   $ sudo sysctl net.core.rmem_max=16777216
   $ sudo sysctl net.core.wmem_max=16777216
   
   Prevents buffer overflows under load

3. CONGESTION CONTROL:
   
   $ cat /proc/sys/net/ipv4/tcp_congestion_control
   cubic
   
   Algorithms:
   - cubic: Default, good for most cases
   - bbr: Google's algorithm, excellent for high-latency
   - reno: Old algorithm
   
   $ sudo sysctl net.ipv4.tcp_congestion_control=bbr

4. CONNECTION QUEUE TUNING:
   
   # Increase SYN backlog
   $ sudo sysctl net.ipv4.tcp_max_syn_backlog=8192
   
   # Increase listen backlog
   $ sudo sysctl net.core.somaxconn=4096
   
   Helps under high connection rate

5. JUMBO FRAMES:
   
   $ sudo ip link set eth0 mtu 9000
   
   Default MTU: 1500 bytes
   Jumbo: 9000 bytes
   
   Reduces packet overhead for large transfers

6. OFFLOADING:
   
   $ ethtool -k eth0
   tcp-segmentation-offload: on
   generic-receive-offload: on
   large-receive-offload: on
   
   Offload work to NIC (reduces CPU usage)

EXAMPLE: Optimize web server network

# Before
$ ss -s
TCP: 10,000 time-wait sockets  (high!)
$ netstat -an | grep TIME_WAIT | wc -l
10000

# Problem: Too many TIME_WAIT sockets

# Optimization 1: Reduce TIME_WAIT duration
$ sudo sysctl net.ipv4.tcp_fin_timeout=15  (was 60)

# Optimization 2: Enable socket reuse
$ sudo sysctl net.ipv4.tcp_tw_reuse=1

# Optimization 3: Increase connection queue
$ sudo sysctl net.core.somaxconn=8192

# After
$ ss -s
TCP: 500 time-wait sockets  (much better!)
```

---

## Profiling Tools

### CPU Profiling

```bash
1. perf
   Linux performance analyzer
   
   # Profile entire system
   $ sudo perf record -ag -- sleep 10
   $ sudo perf report
   
   Shows:
   - Which functions use most CPU
   - Call graphs
   - CPU cycles spent
   
   # Profile specific process
   $ sudo perf record -p 1234 -g -- sleep 10
   
   # Show live top functions
   $ sudo perf top

2. gprof
   GNU profiler
   
   # Compile with profiling
   $ gcc -pg program.c -o program
   
   # Run program
   $ ./program
   
   # Analyze
   $ gprof program gmon.out
   
   Shows:
   - Function call count
   - Time spent per function

3. valgrind --tool=callgrind
   Detailed profiling
   
   $ valgrind --tool=callgrind ./program
   $ callgrind_annotate callgrind.out.<pid>
   
   # Visualize with KCachegrind
   $ kcachegrind callgrind.out.<pid>

4. Flame Graphs
   Visualize stack traces
   
   $ sudo perf record -F 99 -ag -- sleep 60
   $ sudo perf script | ./flamegraph.pl > flame.svg
   
   Wide bars = hot functions
   Stack depth = call chain

EXAMPLE: Profile CPU-bound application

$ sudo perf record -g ./my_program
$ sudo perf report

Overhead  Command   Shared Object  Symbol
  45.00%  my_prog   my_program     compute_heavy()
  20.00%  my_prog   libc.so.6      memcpy
  15.00%  my_prog   my_program     sort_data()
  
Diagnosis: compute_heavy() is bottleneck
Action: Optimize that function
```

### Memory Profiling

```bash
1. valgrind --tool=massif
   Heap profiler
   
   $ valgrind --tool=massif ./program
   $ ms_print massif.out.<pid>
   
   Shows:
   - Heap usage over time
   - Where memory allocated
   
   Graph:
   GB
   |                     @@@@
   |                  @@@    @@@
   |             @@@@@          @@
   |        @@@@                  @@@
   +---------------------------------> Time

2. valgrind --tool=memcheck
   Memory error detector
   
   $ valgrind --leak-check=full ./program
   
   Detects:
   - Memory leaks
   - Invalid memory access
   - Use of uninitialized values
   
   ==12345== LEAK SUMMARY:
   ==12345==    definitely lost: 1,000 bytes
   ==12345==    indirectly lost: 500 bytes

3. heaptrack
   Heap memory profiler
   
   $ heaptrack ./program
   $ heaptrack_gui heaptrack.program.<pid>.gz
   
   Shows:
   - Allocation/deallocation patterns
   - Memory leaks
   - Peak memory usage

4. /proc/<pid>/status
   Process memory info
   
   $ cat /proc/1234/status | grep -i vm
   VmPeak:   500000 kB
   VmSize:   400000 kB
   VmRSS:    300000 kB

EXAMPLE: Find memory leak

$ valgrind --leak-check=full ./my_program

==12345== 10,000 bytes in 1 blocks are definitely lost
==12345==    at malloc (vg_replace_malloc.c:299)
==12345==    by main (my_program.c:42)

Diagnosis: Memory allocated at line 42 never freed
Action: Add free() call
```

---

## Benchmarking

### System Benchmarks

```bash
1. sysbench
   Multi-purpose benchmark
   
   # CPU benchmark
   $ sysbench cpu --threads=4 run
   
   # Memory benchmark
   $ sysbench memory --threads=4 run
   
   # File I/O benchmark
   $ sysbench fileio --file-test-mode=seqwr prepare
   $ sysbench fileio --file-test-mode=seqwr run
   $ sysbench fileio --file-test-mode=seqwr cleanup

2. fio
   Flexible I/O tester
   
   # Random read benchmark
   $ fio --name=randr --rw=randread --size=1G --bs=4k
   
   # Mixed workload
   $ fio --name=mixed --rw=randrw --rwmixread=70 --size=1G

3. UnixBench
   Comprehensive system benchmark
   
   $ ./Run
   
   Tests:
   - Dhrystone (CPU)
   - Whetstone (FP)
   - Execl throughput
   - File copy
   - Pipe throughput

4. stress-ng
   Stress testing tool
   
   # CPU stress
   $ stress-ng --cpu 4 --timeout 60s
   
   # Memory stress
   $ stress-ng --vm 2 --vm-bytes 1G --timeout 60s
   
   # I/O stress
   $ stress-ng --io 4 --timeout 60s

BENCHMARK BEST PRACTICES:

1. Run multiple times
2. Eliminate variance
3. Monitor during benchmark
4. Compare against baseline
5. Document configuration

EXAMPLE: Database benchmark

# Before optimization
$ sysbench oltp_read_write --tables=10 --table-size=100000 run
Transactions: 1000 (100.00 per sec)
Queries: 15000 (1500.00 per sec)
Latency: 50ms avg

# After optimization
Transactions: 1500 (150.00 per sec)  [+50%]
Queries: 22500 (2250.00 per sec)     [+50%]
Latency: 33ms avg                     [-34%]
```

---

## Optimization Techniques

### General Principles

```
1. MEASURE FIRST:
   - Profile before optimizing
   - Find actual bottleneck
   - Don't guess!

2. OPTIMIZE HOTSPOTS:
   - Focus on code that runs most
   - 80/20 rule: 80% time in 20% code
   - Optimize that 20%

3. ALGORITHMIC IMPROVEMENTS:
   - Better algorithm > micro-optimization
   - O(n²) → O(n log n) = huge improvement

4. CACHING:
   - Cache expensive operations
   - Reuse results
   - Trade memory for speed

5. REDUCE SYSTEM CALLS:
   - System calls expensive
   - Batch operations
   - Use buffering

6. PARALLELISM:
   - Use multiple cores
   - Threads or processes
   - Be careful with synchronization

7. MINIMIZE MEMORY COPIES:
   - Copy data less
   - Use references/pointers
   - Memory-map when possible

8. CHOOSE RIGHT DATA STRUCTURES:
   - Array vs linked list
   - Hash table vs tree
   - Match structure to access pattern
```

### Example Optimizations

```c
OPTIMIZATION 1: Reduce system calls

// Before: Many small writes
for (i = 0; i < 1000000; i++) {
    write(fd, &data[i], sizeof(int));
}

// After: Buffered writes
#define BUFFER_SIZE 4096
char buffer[BUFFER_SIZE];
int buf_pos = 0;

for (i = 0; i < 1000000; i++) {
    memcpy(&buffer[buf_pos], &data[i], sizeof(int));
    buf_pos += sizeof(int);
    
    if (buf_pos + sizeof(int) > BUFFER_SIZE) {
        write(fd, buffer, buf_pos);
        buf_pos = 0;
    }
}
if (buf_pos > 0) {
    write(fd, buffer, buf_pos);
}

Speedup: 10-100x!

OPTIMIZATION 2: Caching

// Before: Recompute every time
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

// After: Memoization
int fib_cache[1000] = {0};

int fibonacci(int n) {
    if (n <= 1) return n;
    if (fib_cache[n] != 0) return fib_cache[n];
    
    fib_cache[n] = fibonacci(n-1) + fibonacci(n-2);
    return fib_cache[n];
}

Complexity: O(2^n) → O(n)

OPTIMIZATION 3: Memory access pattern

// Before: Bad cache locality
for (i = 0; i < 1000; i++) {
    for (j = 0; j < 1000; j++) {
        sum += matrix[j][i];  // Column-major (cache miss!)
    }
}

// After: Good cache locality
for (i = 0; i < 1000; i++) {
    for (j = 0; j < 1000; j++) {
        sum += matrix[i][j];  // Row-major (cache hit!)
    }
}

Speedup: 5-10x on large matrices

OPTIMIZATION 4: Parallelization

// Before: Serial
for (i = 0; i < 1000000; i++) {
    result[i] = expensive_computation(data[i]);
}

// After: Parallel with OpenMP
#pragma omp parallel for
for (i = 0; i < 1000000; i++) {
    result[i] = expensive_computation(data[i]);
}

Speedup: Near-linear with # cores
```

---

## Summary

- **Metrics**: Throughput, latency, utilization, saturation
- **USE Method**: Check utilization, saturation, errors for every resource
- **CPU**: Monitor with top/vmstat, optimize with affinity/governor
- **Memory**: Monitor with free/vmstat, optimize swappiness/huge pages
- **Disk I/O**: Monitor with iostat, optimize scheduler/read-ahead
- **Network**: Monitor with ss/iftop, optimize TCP/buffers
- **Profiling**: perf for CPU, valgrind for memory
- **Benchmarking**: sysbench, fio for I/O, stress-ng for stress
- **Optimization**: Measure first, optimize hotspots, cache, parallelize

Performance tuning is iterative: measure, optimize, measure again!

---

**Next Topics:**
- Debugging and Troubleshooting
- Network Stack Deep Dive
- Boot Process

