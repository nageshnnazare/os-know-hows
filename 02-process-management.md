# Operating Systems - Process Management

## Table of Contents
1. [Process Concept](#process-concept)
2. [Process States](#process-states)
3. [Process Control Block](#process-control-block)
4. [Process Operations](#process-operations)
5. [Inter-Process Communication](#inter-process-communication)
6. [Threads](#threads)
7. [Process Scheduling](#process-scheduling)

---

## Process Concept

### What is a Process?

A **process** is a program in execution. It is the unit of work in a modern operating system.

**Program vs Process:**

```
PROGRAM                          PROCESS
+---------------+               +---------------+
| Passive       |               | Active        |
| Entity        |               | Entity        |
|               |               |               |
| Code on       |  =========>   | Code +        |
| Disk          |   (Execute)   | Data +        |
|               |               | Execution     |
| Static        |               | Dynamic       |
+---------------+               +---------------+
```

### Process Components

A process consists of multiple parts:

```
Process Memory Layout:

High Memory (0xFFFFFFFF)
+---------------------------+
|      KERNEL SPACE         |  (Protected, not accessible)
+---------------------------+
|         STACK             |  <- Stack Pointer (SP)
|           |               |     Local variables
|           v               |     Function parameters
|                           |     Return addresses
|           ^               |
|           |               |
+---------------------------+
|          HEAP             |  <- Dynamically allocated
|           ^               |     memory (malloc/new)
|           |               |
+---------------------------+
|    UNINITIALIZED DATA     |  BSS (Block Started by Symbol)
|         (BSS)             |  Uninitialized global variables
+---------------------------+
|    INITIALIZED DATA       |  Initialized global and
|                           |  static variables
+---------------------------+
|          TEXT             |  Program code (instructions)
|      (Code Segment)       |  Read-only
+---------------------------+
Low Memory (0x00000000)
```

---

## Process States

A process transitions through various states during its lifetime.

### Five-State Process Model

```
                        +-------+
                        | NEW   |  (Process being created)
                        +-------+
                            |
                            | admit
                            v
                        +-------+
              +-------->| READY |  (Waiting for CPU)
              |         +-------+
              |             |
              |             | dispatch (scheduler)
              |             v
              |         +----------+
              |         | RUNNING  |  (Executing on CPU)
              |         +----------+
              |           |   |
              |  timeout/ |   | I/O or
              |  interrupt|   | event wait
              |           |   |
              |           |   v
              |           | +------------+
              +-----------+ | WAITING/   |  (Waiting for I/O
                            | BLOCKED    |   or event)
                            +------------+
                                  |
                                  | I/O or event
                                  | completion
                                  v
                            +-------+
                            | READY |
                            +-------+
                                |
                                | exit
                                v
                            +------------+
                            | TERMINATED |  (Process finished)
                            +------------+
```

### State Descriptions

1. **NEW**: Process is being created
2. **READY**: Process is waiting to be assigned to a processor
3. **RUNNING**: Instructions are being executed
4. **WAITING/BLOCKED**: Process is waiting for some event (I/O completion, signal)
5. **TERMINATED**: Process has finished execution

### Extended Seven-State Model (with Suspend States)

```
                    +-------+
                    | NEW   |
                    +-------+
                        |
                        v
    +--------+      +-------+      +----------+
    |SUSPEND |<---->| READY |<---->| RUNNING  |
    | READY  |      +-------+      +----------+
    +--------+          ^              |   |
        ^               |              |   |
        |               |              |   v
        |               |              | +----------+
        |               +--------------|>| WAITING  |
        |                              | +----------+
        |                              |      |
        |                              v      v
        |                          +-------------+
        +------------------------->| SUSPEND     |
                                   | WAITING     |
                                   +-------------+
                                         |
                                         v
                                   +------------+
                                   | TERMINATED |
                                   +------------+
```

**Suspend States**: When memory is overcommitted, some processes are swapped to disk.

---

## Process Control Block (PCB)

The PCB (also called Task Control Block) is a data structure that stores all information about a process.

### PCB Structure

```
+--------------------------------------------------+
|             PROCESS CONTROL BLOCK                |
+--------------------------------------------------+
| Process ID (PID):           12345                |
+--------------------------------------------------+
| Process State:              READY                |
+--------------------------------------------------+
| Program Counter (PC):       0x08048000           |
+--------------------------------------------------+
| CPU Registers:                                   |
|   - General Purpose Registers (EAX, EBX, ...)    |
|   - Stack Pointer (SP)                           |
|   - Base Pointer (BP)                            |
|   - Status Registers (FLAGS)                     |
+--------------------------------------------------+
| CPU Scheduling Information:                      |
|   - Priority: 5                                  |
|   - Scheduling Queue Pointers                    |
|   - Scheduling Parameters                        |
+--------------------------------------------------+
| Memory Management Information:                   |
|   - Base and Limit Registers                     |
|   - Page Tables / Segment Tables                 |
+--------------------------------------------------+
| Accounting Information:                          |
|   - CPU Time Used: 150ms                         |
|   - Time Limits                                  |
|   - Process Numbers                              |
+--------------------------------------------------+
| I/O Status Information:                          |
|   - List of Open Files                           |
|   - List of I/O Devices Allocated                |
|   - Pending I/O Operations                       |
+--------------------------------------------------+
| Parent Process ID (PPID):   1024                 |
+--------------------------------------------------+
| Process Owner (UID):        1000                 |
+--------------------------------------------------+
| Pointers:                                        |
|   - Parent Process Pointer                       |
|   - Child Process Pointers                       |
|   - Next Process in Queue                        |
+--------------------------------------------------+
```

### Context Switch

When CPU switches from one process to another:

```
Process P0 Executing                Process P1 Executing

    RUNNING                             RUNNING
       |                                    |
       | (1) Interrupt or                  |
       |     System Call                   |
       v                                    |
+---------------+                           |
| Save state of |                           |
| P0 into PCB0  |                           |
+---------------+                           |
       |                                    |
       | (2) Context Switch                |
       v                                    |
+---------------+                           |
| Restore state|                            |
| of P1 from   |                            |
| PCB1         |                            |
+---------------+                           |
       |                                    |
       +------------------------------------+
       
Timeline:
|<-- P0 -->|<- Switch ->|<------ P1 ------>|<- Switch ->|<-- P0 -->|
           Overhead                         Overhead
           (1-10 μs)                        (1-10 μs)
```

**Context Switch Overhead**: Time spent saving and restoring process state (pure overhead).

---

## Process Operations

### 1. Process Creation

Processes can create other processes using system calls (e.g., `fork()` in UNIX).

#### Process Tree

```
                     init (PID=1)
                         |
        +----------------+------------------+
        |                |                  |
     sshd (100)      systemd-logind    apache2 (500)
        |                                   |
    +---+---+                    +----------+---------+
    |       |                    |          |         |
 bash(200) bash(201)       worker(501) worker(502) worker(503)
    |
    |
  vim(202)
```

#### Fork System Call (UNIX/Linux)

```c
Parent Process          fork()          Child Process
+-------------+          |              +-------------+
| PID = 1000  |          |              | PID = 1001  |
| PPID = 500  |          |              | PPID = 1000 |
|             |          v              |             |
| Code        |   +-----------+         | Code (copy) |
| Data        |   | Duplicate |         | Data (copy) |
| Heap        |   | Process   |         | Heap (copy) |
| Stack       |   +-----------+         | Stack(copy) |
+-------------+                         +-------------+
      |                                       |
      | fork() returns                        | fork() returns
      | child PID (1001)                      | 0
      v                                       v
Parent continues                        Child executes
```

**Example Code:**

```c
#include <stdio.h>
#include <unistd.h>

int main() {
    pid_t pid;
    
    printf("Before fork (PID: %d)\n", getpid());
    
    pid = fork();  // Create child process
    
    if (pid < 0) {
        // Fork failed
        fprintf(stderr, "Fork failed\n");
        return 1;
    }
    else if (pid == 0) {
        // Child process
        printf("Child process (PID: %d, Parent: %d)\n", 
               getpid(), getppid());
    }
    else {
        // Parent process
        printf("Parent process (PID: %d, Child: %d)\n", 
               getpid(), pid);
    }
    
    return 0;
}
```

#### Exec System Call

Replaces the current process's memory space with a new program:

```
Before exec():                After exec():

+-------------+              +-------------+
| Program A   |              | Program B   |
+-------------+              +-------------+
| A's Code    |   exec()     | B's Code    |
| A's Data    | ==========>  | B's Data    |
| A's Stack   |              | B's Stack   |
| A's Heap    |              | B's Heap    |
+-------------+              +-------------+
  PID: 1000                    PID: 1000 (same)
```

### 2. Process Termination

A process terminates when:
1. It executes the last statement (`exit()`)
2. It is killed by another process (`kill()`)
3. Parent process terminates (cascading termination)

```
Normal Termination:
Process ----> exit(0) ----> Return to OS ----> Cleanup resources

Abnormal Termination:
Process ----> Error/Exception ----> Signal ----> Terminate
                                     (SIGSEGV, SIGKILL, etc.)
```

#### Zombie and Orphan Processes

**Zombie Process:**
- Process has terminated but PCB still exists
- Parent hasn't called `wait()` yet
- Occupies PID and entry in process table

```
Parent (running)           Child (terminated)
     |                            |
     |                            | exit()
     |                            v
     |                     +-------------+
     |                     | ZOMBIE      |
     |                     | (PCB exists)|
     |                     | No code/data|
     |  wait()             +-------------+
     |<------------------------+
     |
     v
Reap zombie
(remove PCB)
```

**Orphan Process:**
- Parent terminates before child
- Child adopted by `init` process (PID 1)

```
Before:                    After Parent Dies:
Parent (PID=100)          
    |                      init (PID=1)
    |                          |
Child (PID=200)           Child (PID=200)
                          (PPID changes to 1)
```

---

## Inter-Process Communication (IPC)

Processes may need to communicate and synchronize with each other.

### IPC Models

```
1. SHARED MEMORY                2. MESSAGE PASSING

Process A    Process B          Process A    Process B
+-------+    +-------+          +-------+    +-------+
|       |    |       |          |       |    |       |
|  Read |    | Write |          | send()|    | recv()|
+-------+    +-------+          +-------+    +-------+
    |            |                  |            |
    v            v                  v            v
+-------------------+          +-------------------+
|  Shared Memory    |          |    OS Kernel      |
|      Region       |          | Message Queue/    |
|                   |          | Mailbox           |
+-------------------+          +-------------------+

Fast (no kernel      Slower (kernel involvement)
involvement after    but easier to implement
setup)               and more portable
```

### 1. Shared Memory

Multiple processes share a region of memory.

```
Process A Memory           Process B Memory
+-------------+            +-------------+
|   Stack     |            |   Stack     |
+-------------+            +-------------+
|   Heap      |            |   Heap      |
+-------------+            +-------------+
| Shared Mem  |<---------->| Shared Mem  |
| (mapped)    |            | (mapped)    |
+-------------+            +-------------+
|   Data      |            |   Data      |
+-------------+            +-------------+
|   Code      |            |   Code      |
+-------------+            +-------------+

         Both point to same physical memory
                +------------------+
                | Physical Memory  |
                | Shared Segment   |
                +------------------+
```

**Characteristics:**
- Very fast (direct memory access)
- Requires synchronization (semaphores, mutexes)
- Processes must coordinate access

**System Calls:**
- `shmget()` - Create shared memory segment
- `shmat()` - Attach to shared memory
- `shmdt()` - Detach from shared memory

### 2. Message Passing

Processes communicate by sending messages through the OS kernel.

#### Direct Communication

```
Process P                    Process Q
    |                            |
    | send(Q, message)           |
    +--------------------------->|
    |                            | receive(P, message)
    |                            |
    | receive(Q, message)        |
    |<---------------------------+
    |                            | send(P, message)
```

#### Indirect Communication (Mailbox/Ports)

```
Process A         Mailbox M         Process B
    |                 |                 |
    | send(M, msg1)   |                 |
    +---------------->|                 |
    |                 |                 |
    |                 | receive(M, msg1)|
    |                 |<----------------+
    |                 |                 |
    |                 | send(M, msg2)   |
    |                 |<----------------+
    | receive(M, msg2)|                 |
    |<----------------+                 |
```

#### Synchronization in Message Passing

```
BLOCKING (Synchronous):

Sender                         Receiver
  |                               |
  | send(msg)                     |
  +------------------------------>|
  | BLOCKED                       | receive(msg)
  | (waiting)                     | BLOCKED (waiting)
  |                               |
  | <-----------------------------|
  | UNBLOCKED                     | Got message
  v                               v


NON-BLOCKING (Asynchronous):

Sender                         Receiver
  |                               |
  | send(msg)                     |
  +------------------------------>|
  | Continues immediately         | receive(msg)
  v (not blocked)                 | Returns immediately
                                  | (message or null)
                                  v
```

### 3. Pipes

A pipe is a conduit allowing communication between processes.

#### Ordinary Pipes (Anonymous)

```
Parent Process
     |
     | fork()
     +------------------+
     |                  |
Parent              Child
     |                  |
     | write()          | read()
     +-----> PIPE ----->+
     |   +---------+    |
     |   | Buffer  |    |
     |   +---------+    |
     
Unidirectional, Parent-Child only
```

**Example:**
```c
int fd[2];  // fd[0]: read end, fd[1]: write end
pipe(fd);
if (fork() == 0) {
    // Child: read from pipe
    close(fd[1]);  // Close write end
    read(fd[0], buffer, size);
}
else {
    // Parent: write to pipe
    close(fd[0]);  // Close read end
    write(fd[1], data, size);
}
```

#### Named Pipes (FIFO)

```
Process A                      Process B
(any process)                  (any process)
     |                              |
     | open("/tmp/myfifo")          | open("/tmp/myfifo")
     |                              |
     | write()                      | read()
     +--------> Named FIFO -------->+
               (filesystem)
               
Can be used by unrelated processes
Bidirectional possible
Persists in filesystem
```

### 4. Sockets

For communication between processes on different machines (or same machine).

```
Machine A                      Machine B
+-----------+                  +-----------+
| Process 1 |                  | Process 2 |
|           |                  |           |
| socket()  |                  | socket()  |
| bind()    |                  | bind()    |
| listen()  |                  | connect() |
| accept()  |<---------------->|           |
|           |  Network (TCP/IP)|           |
| send()    |----------------->| recv()    |
| recv()    |<-----------------| send()    |
+-----------+                  +-----------+

   Port 8080                      Port 5000
```

### 5. Signals

Asynchronous notifications sent to processes.

```
Process A                    OS Kernel
    |                            |
    | (doing work)               |
    |                            |
    |                            | Signal (e.g., SIGINT)
    |<---------------------------+
    |                            | from Ctrl+C or kill
    | Interrupt                  |
    | current work               |
    |                            |
    | Execute signal             |
    | handler                    |
    +--------------------------->|
    |                            |
    | Resume or Terminate        |
    v                            v
```

**Common Signals:**
- `SIGINT` (2): Interrupt (Ctrl+C)
- `SIGKILL` (9): Kill (cannot be caught)
- `SIGSEGV` (11): Segmentation fault
- `SIGTERM` (15): Termination request
- `SIGCHLD` (17): Child process terminated

---

## Threads

A thread is a basic unit of CPU utilization; a lightweight process.

### Process vs Thread

```
PROCESS                          THREAD
+---------------------------+    +-----------------+
| Has own:                  |    | Shares with     |
| - Address Space           |    | other threads:  |
| - Resources               |    | - Address Space |
| - File descriptors        |    | - Resources     |
| - Heap                    |    | - Heap          |
|                           |    | - Code          |
| Expensive to create       |    | - Data          |
| Heavy context switch      |    |                 |
+---------------------------+    | Has own:        |
                                 | - Thread ID     |
Single-Threaded Process:         | - Registers     |
+---------------------------+    | - Stack         |
|         Stack             |    | - PC            |
|         Heap              |    |                 |
|         Data              |    | Cheap to create |
|         Code              |    | Light context   |
+---------------------------+    | switch          |
         1 thread                +-----------------+

Multi-Threaded Process:
+---------------------------+
| Stack | Stack | Stack     | <- One per thread
|-------|-------|-----------|
|                           |
|         Heap              | <- Shared
|                           |
|         Data              | <- Shared
|                           |
|         Code              | <- Shared
+---------------------------+
   T1      T2      T3
```

### Benefits of Multithreading

1. **Responsiveness**: Program continues running even if part is blocked
2. **Resource Sharing**: Threads share memory and resources
3. **Economy**: Cheaper to create and context-switch
4. **Scalability**: Can utilize multiple CPU cores

### Multithreading Models

#### 1. Many-to-One Model

```
User Threads          Kernel Thread
     |                     |
    T1 -------+            |
    T2 -------+---> mapped |
    T3 -------+     to     K1
    T4 -------+            |
     |                     |
```

- Many user threads map to one kernel thread
- Thread management in user space (efficient)
- One blocking call blocks all threads
- Cannot run in parallel on multicore
- Example: Green threads, GNU Portable Threads

#### 2. One-to-One Model

```
User Threads          Kernel Threads
     |                     |
    T1 ---------------->  K1
    T2 ---------------->  K2
    T3 ---------------->  K3
    T4 ---------------->  K4
     |                     |
```

- Each user thread maps to a kernel thread
- More concurrency
- Can run in parallel on multicore
- Creating user thread requires creating kernel thread (overhead)
- Example: Linux, Windows

#### 3. Many-to-Many Model

```
User Threads          Kernel Threads
     |                     |
    T1 ----+               |
    T2 ----+---> mapped    K1
    T3 ----+     to        K2
    T4 ----+               K3
    T5 ----+               |
     |                     |
     
5 user threads on 3 kernel threads
```

- Many user threads multiplexed to smaller/equal number of kernel threads
- Best of both worlds
- Flexible scheduling
- Example: Older Solaris, IRIX

### Thread Libraries

```
POSIX Threads (Pthreads)     Java Threads
+------------------------+   +------------------------+
| pthread_create()       |   | Thread t = new Thread()|
| pthread_join()         |   | t.start()              |
| pthread_exit()         |   | t.join()               |
| pthread_mutex_*()      |   | synchronized blocks    |
+------------------------+   +------------------------+

Windows Threads              
+------------------------+
| CreateThread()         |
| WaitForSingleObject()  |
| ExitThread()           |
+------------------------+
```

### Thread Cancellation

Two approaches to terminate a thread:

```
1. ASYNCHRONOUS CANCELLATION
   Thread A                  Thread B
      |                          |
      | cancel(B)                |
      +------------------------->| (Killed immediately)
      |                          X
      |
      
   Dangerous: May leave resources in inconsistent state

2. DEFERRED CANCELLATION
   Thread A                  Thread B
      |                          |
      | cancel(B)                |
      +------------------------->| (Sets flag)
      |                          |
      |                          | (Continues)
      |                          |
      |                          | (Checks cancellation point)
      |                          |
      |                          | (Cleanup & exit)
      |                          X
      
   Safe: Thread checks cancellation points and cleans up
```

---

## Process Scheduling Queues

The OS maintains various queues to manage processes.

```
                          NEW PROCESSES
                               |
                               | admit
                               v
                          +----------+
                          | Job Queue|  (All processes)
                          +----------+
                               |
                +--------------+--------------+
                |                             |
                v                             |
           +------------+                     |
           | Ready Queue|                     |
           +------------+                     |
                |                             |
                | dispatch                    |
                v                             |
              [CPU]                           |
                |                             |
        +-------+--------+                    |
        |                |                    |
    time out         I/O request              |
        |                |                    |
        |                v                    |
        |         +---------------+           |
        |         | I/O Queue     |           |
        |         | (Device Queue)|           |
        |         +---------------+           |
        |                |                    |
        |         I/O complete                |
        +-------+--------+                    |
                |                             |
                v                             |
           +------------+                     |
           | Ready Queue|                     |
           +------------+                     |
                                              |
                                exit          |
                                |             |
                                v             |
                          +----------+        |
                          |TERMINATED|        |
                          +----------+        |
                                              |
      All queues feed back to ready queue  ---+
```

### Queueing Diagram Detail

```
Ready Queue (Linked List):
+-----+    +-----+    +-----+    +-----+
|PCB1 |--->|PCB3 |--->|PCB7 |--->|PCB9 |---> NULL
+-----+    +-----+    +-----+    +-----+

I/O Device Queue (Disk):
+-----+    +-----+
|PCB2 |--->|PCB5 |---> NULL
+-----+    +-----+

I/O Device Queue (Printer):
+-----+
|PCB4 |---> NULL
+-----+
```

---

## Schedulers

### Types of Schedulers

```
                +------------------------+
                |   Long-Term Scheduler  |
                |   (Job Scheduler)      |
                +------------------------+
                           |
                           | Controls degree of
                           | multiprogramming
                           v
                    [JOB POOL]
                           |
                           v
                +------------------------+
                |  Short-Term Scheduler  |
                |  (CPU Scheduler)       |
                +------------------------+
                           |
                           | Selects which process
                           | executes next
                           v
                        [CPU]
                           |
                           v
                +------------------------+
                | Medium-Term Scheduler  |
                | (Swapper)              |
                +------------------------+
                           |
                           | Swapping in/out
                           | to manage memory
                           v
                      [DISK SWAP]
```

#### 1. Long-Term Scheduler (Job Scheduler)
- Selects processes from job pool and loads into memory
- Controls degree of multiprogramming
- Executes infrequently (seconds, minutes)
- Can be slow
- Not present in some systems (UNIX, Windows)

#### 2. Short-Term Scheduler (CPU Scheduler)
- Selects which ready process executes next
- Executes very frequently (milliseconds)
- Must be very fast
- Present in all multiprogramming systems

#### 3. Medium-Term Scheduler
- Swaps processes in/out of memory
- Reduces degree of multiprogramming
- Manages memory contention

### Process Mix

```
I/O-Bound Process:
CPU |*|     |*|      |*|     |*|
I/O |  *****|  ******|  *****| 
    +-------+--------+-------+-----> Time
    More I/O than CPU time

CPU-Bound Process:
CPU |*****************|    |****|
I/O |                 ****|    ****
    +-----------------+----+----+---> Time
    More CPU than I/O time
```

**Good mix**: Both I/O-bound and CPU-bound processes for optimal resource utilization.

---

## Summary

- **Process**: Program in execution with code, data, stack, heap, and PCB
- **Process States**: New, Ready, Running, Waiting, Terminated (+ Suspended states)
- **PCB**: Data structure storing all process information
- **Context Switch**: Saving and restoring process state (overhead)
- **Process Operations**: Creation (fork), Execution (exec), Termination (exit)
- **IPC Methods**: Shared Memory, Message Passing, Pipes, Sockets, Signals
- **Threads**: Lightweight processes sharing address space
- **Multithreading Models**: Many-to-One, One-to-One, Many-to-Many
- **Scheduling Queues**: Job queue, Ready queue, Device queues
- **Schedulers**: Long-term, Short-term, Medium-term

---

**Next Topics:**
- CPU Scheduling Algorithms
- Process Synchronization
- Deadlocks

