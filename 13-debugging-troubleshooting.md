# Operating Systems - Debugging and Troubleshooting

## Table of Contents
1. [Debugging Tools Overview](#debugging-tools-overview)
2. [System Call Tracing](#system-call-tracing)
3. [Kernel Debugging](#kernel-debugging)
4. [Memory Debugging](#memory-debugging)
5. [Core Dumps Analysis](#core-dumps-analysis)
6. [Log Analysis](#log-analysis)
7. [Common Problems and Solutions](#common-problems-and-solutions)

---

## Debugging Tools Overview

### Essential Tools

```
DEBUG TOOLBOX:

Application Level:
├── gdb          : GNU Debugger
├── lldb         : LLVM Debugger
├── valgrind     : Memory debugger
└── strace       : System call tracer

System Level:
├── ltrace       : Library call tracer
├── ftrace       : Kernel function tracer
├── perf         : Performance analysis
└── bpftrace     : eBPF-based tracing

Kernel Level:
├── kgdb         : Kernel debugger
├── crash        : Kernel crash analyzer
├── systemtap    : Kernel probing
└── kdump        : Kernel crash dump

Logging:
├── dmesg        : Kernel messages
├── journalctl   : System logs (systemd)
├── syslog       : System logging
└── /var/log/*   : Traditional logs
```

### GDB Basics

```bash
GDB (GNU Debugger):

# Compile with debug symbols
$ gcc -g program.c -o program

# Start debugging
$ gdb ./program

GDB COMMANDS:

(gdb) break main         # Set breakpoint at main
(gdb) run               # Start program
(gdb) next              # Next line (step over)
(gdb) step              # Step into function
(gdb) continue          # Continue execution
(gdb) print variable    # Print variable value
(gdb) bt                # Backtrace (stack trace)
(gdb) info locals       # Show local variables
(gdb) quit              # Exit GDB

EXAMPLE: Debug segmentation fault

$ gdb ./program
(gdb) run
Program received signal SIGSEGV, Segmentation fault.
0x0000555555555169 in main () at program.c:10
10          *ptr = 42;

(gdb) print ptr
$1 = (int *) 0x0

(gdb) backtrace
#0  0x0000555555555169 in main () at program.c:10

Diagnosis: Dereferencing NULL pointer at line 10
```

---

## System Call Tracing

### strace

```bash
STRACE: Trace system calls

# Basic usage
$ strace ./program

# Common options
$ strace -c ./program          # Count calls summary
$ strace -T ./program          # Show time spent
$ strace -p 1234               # Attach to running process
$ strace -f ./program          # Follow forks
$ strace -e open ./program     # Trace only open() calls
$ strace -o trace.txt ./program # Save to file

EXAMPLE: Debug file access

$ strace -e openat cat /etc/passwd

openat(AT_FDCWD, "/etc/passwd", O_RDONLY) = 3
...

Shows:
- File opened successfully (fd=3)
- Flags used (O_RDONLY)

EXAMPLE: Find missing file

$ strace -e openat ./my_program 2>&1 | grep ENOENT

openat(AT_FDCWD, "/lib/libmissing.so", O_RDONLY) = -1 ENOENT

Diagnosis: Missing library file

EXAMPLE: Performance debugging

$ strace -c ls /usr/bin

% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 52.63    0.000050           0      1000           write
 31.58    0.000030           0       500           read
 15.79    0.000015           0       100           open
------ ----------- ----------- --------- --------- ----------------
100.00    0.000095                  1600           total

Analysis: write() consuming most time

FILTERING:

# Trace file operations
$ strace -e trace=file ./program

# Trace network operations
$ strace -e trace=network ./program

# Trace IPC
$ strace -e trace=ipc ./program

# Trace process management
$ strace -e trace=process ./program
```

### ltrace

```bash
LTRACE: Trace library calls

$ ltrace ./program

malloc(100)                              = 0x563f8e2f12a0
strcpy(0x563f8e2f12a0, "Hello")         = 0x563f8e2f12a0
printf("Message: %s\n", "Hello")        = 14
free(0x563f8e2f12a0)                    = <void>

Shows:
- Library functions called
- Parameters passed
- Return values

EXAMPLE: Debug string operations

$ ltrace -e 'str*' ./program

strlen("Hello")                          = 5
strcpy(0x..., "Hello")                  = 0x...
strcmp("Hello", "World")                = -1
```

---

## Kernel Debugging

### dmesg

```bash
DMESG: Kernel ring buffer messages

# View all messages
$ dmesg

# Follow new messages
$ dmesg -w

# Human-readable timestamps
$ dmesg -T

# Filter by facility
$ dmesg -f kern       # Kernel messages
$ dmesg -f daemon     # Daemon messages

# Filter by level
$ dmesg -l err        # Errors only
$ dmesg -l warn       # Warnings

EXAMPLE: Debug hardware issues

$ dmesg | grep -i error

[12345.678] usb 1-1: device descriptor read/64, error -110
[12346.789] ata1.00: failed command: READ FPDMA QUEUED

Diagnosis: USB device error, disk error

EXAMPLE: Check module loading

$ dmesg | grep module

[    2.345] module: loading module xyz
[    2.346] module xyz: initialized successfully
```

### ftrace

```bash
FTRACE: Kernel function tracer

# Enable function tracer
$ cd /sys/kernel/debug/tracing
$ echo function > current_tracer
$ echo 1 > tracing_on

# View trace
$ cat trace

# Trace specific function
$ echo do_sys_open > set_ftrace_filter
$ cat trace

# Function graph tracer
$ echo function_graph > current_tracer
$ cat trace

Shows call graphs with timing

EXAMPLE: Trace system call

$ echo do_sys_open > set_ftrace_filter
$ echo 1 > tracing_on
$ cat /etc/passwd > /dev/null
$ echo 0 > tracing_on
$ cat trace

  cat-1234  [000] .... 12345.678: do_sys_open <-SyS_open
```

---

## Memory Debugging

### Valgrind

```bash
VALGRIND: Memory error detector

MEMCHECK (default tool):

$ valgrind ./program

==12345== Invalid write of size 4
==12345==    at 0x400567: main (program.c:15)
==12345==  Address 0x52040a0 is 0 bytes after a block of size 400 alloc'd

Common errors detected:
- Memory leaks
- Invalid memory access
- Use of uninitialized values
- Double free
- Mismatched free/delete

LEAK DETECTION:

$ valgrind --leak-check=full ./program

==12345== HEAP SUMMARY:
==12345==     in use at exit: 1,000 bytes in 10 blocks
==12345==   total heap usage: 15 allocs, 5 frees, 1,500 bytes allocated
==12345== 
==12345== LEAK SUMMARY:
==12345==    definitely lost: 500 bytes in 5 blocks
==12345==    indirectly lost: 300 bytes in 3 blocks
==12345==    possibly lost: 200 bytes in 2 blocks

EXAMPLE: Find memory leak

C code:
void leak_memory() {
    char *ptr = malloc(100);
    // Missing: free(ptr);
}

$ valgrind --leak-check=full ./program

==12345== 100 bytes in 1 blocks are definitely lost
==12345==    at malloc (vg_replace_malloc.c:299)
==12345==    by leak_memory (program.c:10)
==12345==    by main (program.c:20)

Diagnosis: malloc() at line 10 never freed
```

### AddressSanitizer (ASan)

```bash
ADDRESSSANITIZER: Fast memory error detector

# Compile with ASan
$ gcc -fsanitize=address -g program.c -o program

# Run
$ ./program

EXAMPLE: Buffer overflow

C code:
int arr[10];
arr[11] = 42;  // Out of bounds!

Output:
=================================================================
==12345==ERROR: AddressSanitizer: stack-buffer-overflow
WRITE of size 4 at 0x7ffc1234 thread T0
    #0 main program.c:15
    
0x7ffc1234 is located 4 bytes to the right of 40-byte region
allocated in stack frame

Diagnosis: Writing beyond array bounds at line 15

ADVANTAGES:
- Much faster than Valgrind (2x slowdown vs 10-50x)
- Finds similar errors
- Better for large programs
```

---

## Core Dumps Analysis

### Generating Core Dumps

```bash
ENABLE CORE DUMPS:

# Check limit
$ ulimit -c
0  (disabled)

# Enable unlimited core dumps
$ ulimit -c unlimited

# Set core dump pattern
$ sudo sysctl kernel.core_pattern=/tmp/core.%e.%p

# Or use systemd-coredump
$ sudo systemctl enable systemd-coredump

TRIGGER CORE DUMP:

# Segmentation fault automatically creates core
$ ./buggy_program
Segmentation fault (core dumped)

# Or send signal
$ kill -SEGV <pid>
$ kill -ABRT <pid>
```

### Analyzing Core Dumps

```bash
GDB WITH CORE DUMP:

$ gdb ./program core.1234

(gdb) bt
#0  0x00005555555551a9 in crash_function () at program.c:25
#1  0x00005555555551c3 in main () at program.c:35

(gdb) frame 0
#0  0x00005555555551a9 in crash_function () at program.c:25
25          *ptr = 42;

(gdb) print ptr
$1 = (int *) 0x0

(gdb) info locals
ptr = 0x0
count = 10
buffer = "Hello"

Diagnosis: NULL pointer dereference in crash_function()

EXAMPLE: Debug crashed daemon

$ sudo coredumpctl list

TIME                            PID   UID   GID SIG COREFILE  EXE
Wed 2024-01-15 10:30:15 UTC   1234  1000  1000  11 present   /usr/bin/mydaemon

$ sudo coredumpctl gdb 1234

(gdb) bt
#0  0x00007f1234567890 in __memcpy_sse2 ()
#1  0x0000555555555678 in process_data () at daemon.c:150
#2  0x00005555555556a0 in main_loop () at daemon.c:200

(gdb) frame 1
(gdb) print data
$1 = (struct data *) 0x0

Diagnosis: Passing NULL pointer to memcpy() at daemon.c:150
```

---

## Log Analysis

### System Logs

```bash
JOURNALCTL (systemd):

# View all logs
$ journalctl

# Follow new logs
$ journalctl -f

# Show logs for specific unit
$ journalctl -u nginx.service

# Show logs since time
$ journalctl --since "2024-01-15 10:00:00"
$ journalctl --since "1 hour ago"

# Show only errors
$ journalctl -p err

# Show kernel messages
$ journalctl -k

# Show logs for specific process
$ journalctl _PID=1234

EXAMPLE: Debug service failure

$ systemctl status nginx
● nginx.service - nginx web server
   Active: failed (Result: exit-code)

$ journalctl -u nginx -n 50

Jan 15 10:30:15 nginx[1234]: [error] bind() to 0.0.0.0:80 failed (98: Address already in use)
Jan 15 10:30:15 systemd[1]: nginx.service: Main process exited, code=exited, status=1

Diagnosis: Port 80 already in use

$ sudo lsof -i :80
apache2  5678  root  4u  IPv4  0x12345  TCP *:80 (LISTEN)

Solution: Stop apache2 or use different port

TRADITIONAL SYSLOG:

$ tail -f /var/log/syslog         # General system log
$ tail -f /var/log/auth.log       # Authentication log
$ tail -f /var/log/kern.log       # Kernel log
$ tail -f /var/log/messages       # General messages
```

### Log Analysis Tools

```bash
GREP PATTERNS:

# Find errors
$ grep -i error /var/log/syslog

# Find with context
$ grep -C 5 "connection refused" /var/log/app.log

# Find in multiple files
$ grep -r "out of memory" /var/log/

# Count occurrences
$ grep -c "failed login" /var/log/auth.log

AWK ANALYSIS:

# Extract specific fields
$ awk '{print $1, $5}' /var/log/access.log

# Filter by time
$ awk '$0 ~ /Jan 15 10:/ {print}' /var/log/syslog

# Count by field
$ awk '{print $6}' /var/log/access.log | sort | uniq -c | sort -rn

EXAMPLE: Analyze access patterns

$ awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

   1234 192.168.1.100
    567 192.168.1.101
    234 192.168.1.102
    
Shows top IPs by request count
```

---

## Common Problems and Solutions

### High Load Average

```bash
SYMPTOM:
$ uptime
10:30:15 up 5 days,  3:24,  2 users,  load average: 15.23, 12.45, 10.67

4 CPUs, load > 4 → System overloaded!

DIAGNOSIS:

1. Check what's running
$ ps aux --sort=-%cpu | head

2. Check I/O wait
$ iostat -x 1
%iowait: 45%  (high!)

3. Check disk queue
$ iostat -x 1
avgqu-sz: 15  (high!)

SOLUTION:
- If CPU-bound: Add CPUs, optimize code
- If I/O-bound: Faster disks, optimize I/O
- If both: System overcommitted, need more resources
```

### Out of Memory

```bash
SYMPTOM:
$ dmesg | grep -i "out of memory"
Out of memory: Kill process 1234 (java) score 850

DIAGNOSIS:

1. Check memory usage
$ free -h
Mem:  8.0G   7.9G   100M  (99% used!)

2. Find memory hogs
$ ps aux --sort=-%mem | head

3. Check OOM killer logs
$ dmesg | grep -A 5 "Out of memory"

SOLUTIONS:

Immediate:
$ sudo sync
$ sudo sysctl vm.drop_caches=3  (free caches)
$ kill <pid>  (kill memory hog)

Long-term:
- Add more RAM
- Reduce memory usage
- Enable swap
- Tune OOM killer (vm.oom_kill_allocating_task)
```

### Disk Full

```bash
SYMPTOM:
No space left on device

DIAGNOSIS:

1. Check disk usage
$ df -h
/dev/sda1  20G  20G   0G  100% /

2. Find large files
$ du -sh /* | sort -h
$ du -sh /var/* | sort -h

3. Find deleted files still open
$ lsof +L1 | grep deleted

SOLUTIONS:

Immediate:
$ sudo journalctl --vacuum-time=3d  (clean old logs)
$ rm /tmp/*  (clean temp files)
$ docker system prune -a  (clean Docker)

Find and remove:
$ find /var/log -name "*.log" -mtime +30 -delete
$ find / -type f -size +100M  (find large files)

Recover deleted files still open:
$ lsof +L1 | grep deleted
program  1234  user  3w  /tmp/deleted.log (deleted)

$ cp /proc/1234/fd/3 /tmp/recovered.log
```

### Network Connectivity

```bash
SYMPTOM:
Cannot connect to server

DIAGNOSIS:

1. Check interface
$ ip addr show
$ ip link show

2. Check routes
$ ip route show
$ route -n

3. Check DNS
$ nslookup google.com
$ cat /etc/resolv.conf

4. Test connectivity
$ ping 8.8.8.8  (IP)
$ ping google.com  (DNS)

5. Check port
$ telnet server 80
$ nc -zv server 80

6. Check firewall
$ sudo iptables -L
$ sudo firewall-cmd --list-all

SOLUTIONS:

Interface down:
$ sudo ip link set eth0 up

No route:
$ sudo ip route add default via 192.168.1.1

DNS not working:
$ echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf

Firewall blocking:
$ sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
```

### Process Hangs

```bash
SYMPTOM:
Process not responding

DIAGNOSIS:

1. Check process state
$ ps aux | grep process
USER  PID  STAT  TIME  COMMAND
user  1234 D     0:05  process  (D = uninterruptible sleep)

2. Check what it's doing
$ strace -p 1234
futex(...) = ? (waiting)

3. Check stack trace
$ sudo cat /proc/1234/stack
[<0>] wait_for_completion+0x12/0x20
[<0>] do_sync_read+0x45/0x70

4. Check open files
$ lsof -p 1234

SOLUTIONS:

If waiting on I/O:
- Check disk/network
- May need to wait or restart

If deadlocked:
- Kill and restart
$ kill -9 1234

If zombie (defunct):
- Parent not waiting
$ kill -9 <parent_pid>
```

### Slow Application

```bash
DIAGNOSIS WORKFLOW:

1. Profile CPU
$ perf record -g -p <pid>
$ perf report

2. Check system calls
$ strace -c -p <pid>

3. Check I/O
$ iotop
$ iostat -x 1

4. Check network
$ nethogs
$ iftop

5. Check memory
$ cat /proc/<pid>/status
$ pmap <pid>

COMMON CAUSES:

High CPU:
- Optimize hot functions
- Add caching
- Parallelize

High I/O wait:
- Use buffering
- Async I/O
- Faster storage

Memory issues:
- Reduce memory usage
- Fix memory leaks
- Add more RAM

Network issues:
- Compress data
- Batch requests
- Better protocol
```

---

## Summary

- **Tools**: gdb, strace, ltrace, valgrind for debugging
- **System calls**: strace reveals what program doing
- **Kernel**: dmesg, ftrace for kernel-level debugging
- **Memory**: valgrind, ASan detect memory errors
- **Core dumps**: Analyze crashes with gdb
- **Logs**: journalctl, syslog for system events
- **Common issues**: High load, OOM, disk full, network issues

Systematic debugging: observe → hypothesize → test → fix → verify!

---

**Next: Network Stack & Boot Process**

