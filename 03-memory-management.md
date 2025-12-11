# Operating Systems - Memory Management

## Table of Contents
1. [Memory Hierarchy](#memory-hierarchy)
2. [Address Binding](#address-binding)
3. [Logical vs Physical Address](#logical-vs-physical-address)
4. [Memory Allocation Strategies](#memory-allocation-strategies)
5. [Paging](#paging)
6. [Segmentation](#segmentation)
7. [Virtual Memory](#virtual-memory)
8. [Page Replacement Algorithms](#page-replacement-algorithms)
9. [Thrashing](#thrashing)

---

## Memory Hierarchy

Computer systems have multiple levels of memory, organized by speed and size.

```
                    Faster, Smaller, More Expensive
                              ^
                              |
+-------------------------------------------------------------+
|  CPU REGISTERS                                              |
|  - Fastest access (< 1 ns)                                  |
|  - Smallest size (bytes)                                    |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|  CACHE MEMORY (L1, L2, L3)                                  |
|  - Very fast (1-10 ns)                                      |
|  - Small size (KB - MB)                                     |
|  - L1: ~32-128 KB per core                                  |
|  - L2: ~256 KB - 1 MB per core                              |
|  - L3: ~8-64 MB shared                                      |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|  MAIN MEMORY (RAM)                                          |
|  - Fast (50-100 ns)                                         |
|  - Medium size (GB)                                         |
|  - Volatile (loses data on power off)                       |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|  SECONDARY STORAGE (SSD/HDD)                                |
|  - Slow (microseconds - milliseconds)                       |
|  - Large size (TB)                                          |
|  - Non-volatile (persistent)                                |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|  TERTIARY STORAGE (Tape, Optical)                           |
|  - Very slow (seconds)                                      |
|  - Very large size (TB - PB)                                |
|  - Archival storage                                         |
+-------------------------------------------------------------+
                              |
                              v
                    Slower, Larger, Cheaper
```

### Memory Access Pattern

```
CPU Request:
    |
    v
+----------+
| Register | ---> Hit (0.5 ns)
+----------+
    | Miss
    v
+----------+
| L1 Cache | ---> Hit (1 ns)
+----------+
    | Miss
    v
+----------+
| L2 Cache | ---> Hit (3 ns)
+----------+
    | Miss
    v
+----------+
| L3 Cache | ---> Hit (10 ns)
+----------+
    | Miss
    v
+----------+
| RAM      | ---> Hit (100 ns)
+----------+
    | Miss (Page Fault)
    v
+----------+
| Disk     | ---> Access (10 ms = 10,000,000 ns)
+----------+
```

---

## Address Binding

The process of mapping program addresses to actual physical memory addresses.

### Binding Time

```
SOURCE PROGRAM
    |
    | Compilation
    v
OBJECT MODULE (Relocatable addresses)
    |
    | Linkage
    v
LOAD MODULE (May have absolute or relocatable addresses)
    |
    | Loading
    v
IN-MEMORY BINARY IMAGE (Physical addresses)
    |
    | Execution
    v
RUNNING PROCESS
```

#### Types of Address Binding

**1. Compile Time Binding:**
```
Source Code:            Compiled Code:
int x = 10;      ===>   MOV [0x1000], 10
                        
Absolute address (0x1000) fixed at compile time
- Must know memory location in advance
- Cannot move program in memory
- Used in embedded systems
```

**2. Load Time Binding:**
```
Compiled Code:          Loaded Code:
MOV [R+100], 10  ===>   MOV [0x5100], 10
(Relocatable)           (If loaded at 0x5000)

Addresses assigned when program is loaded
- Relocatable code
- If memory location changes, must reload
```

**3. Execution Time Binding (Dynamic):**
```
Compiled Code:              Running Code:
MOV [R+100], 10      ===>   MMU translates dynamically
                            0x2000 + 100 = 0x2100

Addresses can change during execution
- Requires hardware support (MMU)
- Most modern systems use this
```

---

## Logical vs Physical Address

### Address Spaces

```
LOGICAL ADDRESS SPACE          PHYSICAL ADDRESS SPACE
(Virtual/Logical Addresses)    (Physical Addresses)

Process View:                  Hardware View:
+-------------------+          +-------------------+
| 0x00000000        |          | 0x00000000        |
|                   |          |                   |
|                   |          | OS Kernel         |
| Process           |          |                   |
| Address           |  MMU     +-------------------+
| Space             | =======> | 0x10000000        |
|                   |  (Maps)  |                   |
| 0xFFFFFFFF        |          | Process A         |
+-------------------+          |                   |
                               +-------------------+
Each process has               | 0x20000000        |
its own logical                |                   |
address space                  | Process B         |
                               |                   |
                               +-------------------+
                               | 0x30000000        |
                               |     ...           |
```

### Memory Management Unit (MMU)

```
CPU                       MMU                      Memory
+-----+                +-------+                  +------+
|     |  Logical Addr  |       |  Physical Addr   |      |
| CPU |--------------->|  MMU  |----------------->| RAM  |
|     |   (e.g. 346)   |       |  (e.g. 14346)    |      |
+-----+                +-------+                  +------+
                           |
                      Relocation
                      Register
                      (14000)
                      
Physical Address = Logical Address + Relocation Register
                 = 346 + 14000
                 = 14346
```

### Base and Limit Registers

Protect memory spaces of different processes:

```
+---------------------+
| Base Register       | = 14000 (Start of process)
+---------------------+
| Limit Register      | = 3000 (Size of process)
+---------------------+
        |
        | For each memory access:
        v
+------------------------+
| Check:                 |
| 0 <= Logical Addr      |
|      < Limit           |
+------------------------+
        |
        | If valid
        v
+------------------------+
| Physical Address =     |
| Base + Logical Address |
+------------------------+

Example:
Logical Address: 500
Check: 0 <= 500 < 3000? YES
Physical Address: 14000 + 500 = 14500

Logical Address: 4000
Check: 0 <= 4000 < 3000? NO
Action: TRAP to OS (Segmentation Fault)
```

---

## Memory Allocation Strategies

### 1. Contiguous Allocation

Each process occupies a single contiguous section of memory.

#### Fixed Partitioning

```
Physical Memory:
+-------------------+ 0 KB
|   Operating       |
|   System          |
+-------------------+ 100 KB
|   Partition 1     |
|   (200 KB)        |  Fixed size partitions
+-------------------+ 300 KB
|   Partition 2     |
|   (300 KB)        |
+-------------------+ 600 KB
|   Partition 3     |
|   (400 KB)        |
+-------------------+ 1000 KB

Problems:
- Internal Fragmentation (unused space within partition)
- Limit on process size
```

#### Dynamic Partitioning

Memory divided dynamically based on process needs:

```
Initial State:           After P1 loads:         After P2 loads:
+-------------+          +-------------+         +-------------+
|             |          | Process P1  |         | Process P1  |
|             |          | (100 KB)    |         | (100 KB)    |
|   Free      |          +-------------+         +-------------+
|   Memory    |          |             |         | Process P2  |
|   (1 MB)    |          |   Free      |         | (200 KB)    |
|             |          |   (900 KB)  |         +-------------+
|             |          |             |         |   Free      |
+-------------+          +-------------+         |   (700 KB)  |
                                                 +-------------+

After P1 exits:          After P3 loads:
+-------------+          +-------------+
|    Hole     |          | Process P3  |
|  (100 KB)   |          | (50 KB)     |
+-------------+          +-------------+
| Process P2  |          |    Hole     |
| (200 KB)    |          |  (50 KB)    |
+-------------+          +-------------+
|   Free      |          | Process P2  |
|  (700 KB)   |          | (200 KB)    |
+-------------+          +-------------+
                         |   Free      |
                         |  (700 KB)   |
                         +-------------+
```

### Memory Allocation Algorithms

#### First Fit
Allocate the first hole that is big enough.

```
Holes: [100KB] [500KB] [200KB] [300KB]
Process needs 150KB
         ↓
Result: [100KB] [150KB|350KB free] [200KB] [300KB]
                 └─ Allocated here (first fit)

Fast, may create small holes at beginning
```

#### Best Fit
Allocate the smallest hole that is big enough.

```
Holes: [100KB] [500KB] [200KB] [300KB]
Process needs 150KB
                        ↓
Result: [100KB] [500KB] [150KB|50KB] [300KB]
                         └─ Allocated here (best fit)

Minimizes wasted space, but slower
Creates smallest leftover holes
```

#### Worst Fit
Allocate the largest hole.

```
Holes: [100KB] [500KB] [200KB] [300KB]
Process needs 150KB
                 ↓
Result: [100KB] [150KB|350KB free] [200KB] [300KB]
                 └─ Allocated here (worst fit)

Leaves largest leftover hole
Not commonly used
```

### Fragmentation

```
EXTERNAL FRAGMENTATION:
+----------+
| Process  |  Total free memory = 300 KB
+----------+  But largest contiguous = 100 KB
| 100 KB   |  Cannot allocate 200 KB process!
| Hole     |
+----------+
| Process  |
+----------+
| 100 KB   |
| Hole     |
+----------+
| Process  |
+----------+
| 100 KB   |
| Hole     |
+----------+

INTERNAL FRAGMENTATION:
+----------------------+
|     Process (3 KB)   |
|                      |
|----------------------|
|   Wasted (1 KB)      |  Partition size: 4 KB
+----------------------+  Process size: 3 KB
                          Internal waste: 1 KB
```

#### Solution: Compaction

```
Before Compaction:           After Compaction:
+----------+                 +----------+
| Process A|                 | Process A|
+----------+                 +----------+
|   Hole   |                 | Process B|
+----------+                 +----------+
| Process B|                 | Process C|
+----------+                 +----------+
|   Hole   |                 |          |
+----------+        ===>     |   Hole   |
| Process C|                 | (Large   |
+----------+                 |  & Cont- |
|   Hole   |                 |  iguous) |
+----------+                 |          |
                             +----------+

Expensive: Must move all processes
Only possible with dynamic relocation
```

---

## Paging

Divide physical memory into fixed-size blocks called **frames**.
Divide logical memory into blocks of same size called **pages**.

### Paging Concept

```
LOGICAL ADDRESS SPACE         PHYSICAL ADDRESS SPACE
(Process View)                (Hardware View)

Page 0  +-------+             Frame 3  +-------+
        |       |             Frame 1  |       | <- Page 2
Page 1  +-------+             Frame 0  +-------+
        |       |             Frame 5  |       | <- Page 0
Page 2  +-------+             Frame 2  +-------+
        |       |             Frame 6  |       | <- Page 1
Page 3  +-------+             Frame 4  +-------+
                              Frame 7  +-------+
                                       |       | <- Page 3
                                       +-------+

Pages can be loaded into any available frame
No external fragmentation!
Small internal fragmentation (last page)
```

### Page Table

Maps logical pages to physical frames:

```
Page Table (per process):
+------------+-------------+
| Page #     | Frame #     |
+------------+-------------+
|   0        |    5        |
|   1        |    6        |
|   2        |    1        |
|   3        |    7        |
+------------+-------------+
```

### Address Translation in Paging

```
Logical Address (32-bit, 4KB pages):

+----------------------+-------------------+
| Page Number (20 bits)| Offset (12 bits) |
+----------------------+-------------------+
                |                |
                |                |
                v                |
         +------------+          |
         | Page Table |          |
         +------------+          |
                |                |
                v                |
         Frame Number            |
                |                |
                v                v
+----------------------+-------------------+
| Frame Number         | Offset (12 bits) |
+----------------------+-------------------+
         Physical Address

Example:
Logical Address: 8192 (binary: 0000 0000 0010 0000 0000 0000 0000 0000)
Page Size: 4096 bytes (4 KB)

Page Number = 8192 / 4096 = 2
Offset = 8192 % 4096 = 0

If Page Table[2] = Frame 1:
Physical Address = (1 * 4096) + 0 = 4096
```

### Paging Hardware

```
                CPU
                 |
                 | Logical Address
                 v
        +--------+--------+
        | Page # | Offset |
        +--------+--------+
             |        |
             |        |
             v        |
     +-------------+  |
     | Page Table  |  |
     | Base Reg    |  |
     +-------------+  |
             |        |
             v        |
     +-------------+  |
     |             |  |
     | Page Table  |  |
     | in Memory   |  |
     |             |  |
     | Page 0 -> 5 |  |
     | Page 1 -> 6 |  |
     | Page 2 -> 1 |  |
     | Page 3 -> 7 |  |
     +-------------+  |
             |        |
             v        |
        Frame Number  |
             |        |
             |        v
             +--------+
                 |
                 v
        +--------+--------+
        | Frame# | Offset |
        +--------+--------+
                 |
                 | Physical Address
                 v
              Memory
```

### Multi-Level Paging

For large address spaces, page table itself becomes too large.

#### Two-Level Page Table

```
Logical Address (32-bit):
+------------+------------+-----------+
| P1 (10 bit)| P2 (10 bit)| d (12 bit)|
+------------+------------+-----------+
     |            |             |
     |            |             |
     v            |             |
+----------+      |             |
| Outer PT |      |             |
|  (1024   |      |             |
|  entries)|      |             |
+----------+      |             |
     |            |             |
     v            v             |
+----------+ +----------+       |
| Inner PT | | Inner PT |       |
| (1024    | | (1024    |       |
| entries) | | entries) |       |
+----------+ +----------+       |
     |                          |
     v                          |
  Frame #                       |
     |                          |
     +----------+---------------+
                |
                v
        Physical Address

Advantages:
- Page table can be paged itself
- Don't need contiguous memory for page table
- Can leave inner page tables unallocated if not needed
```

### Translation Lookaside Buffer (TLB)

Cache for page table entries to speed up translation.

```
      CPU
       |
       | Logical Address
       v
+-------------+
| TLB         |
| (Fast Cache)|
+-------------+
   |       |
   | Hit   | Miss
   v       v
Frame#  +----------+
   |    | Page     |
   |    | Table    |
   |    | (in RAM) |
   |    +----------+
   |         |
   |         v
   |      Frame #
   |         |
   +---------+
       |
       v
Physical Address
       |
       v
     Memory

TLB Hit Ratio: ~99%
TLB Hit Time: 1 ns
TLB Miss Time: 100 ns (access page table in memory)

Effective Access Time (EAT):
EAT = 0.99 * 1 + 0.01 * 100 = 1.99 ns (vs 100 ns without TLB)
```

### Page Table Entry (PTE) Structure

```
+---+---+---+---+---+---+------------------+
| V | R | M | P | U | X |  Frame Number    |
+---+---+---+---+---+---+------------------+

Bits:
V = Valid bit (is page in memory?)
R = Referenced bit (recently accessed?)
M = Modified/Dirty bit (has page been written to?)
P = Protection bits (read/write/execute permissions)
U = User/Supervisor bit
X = Execute disable bit

Frame Number: Points to physical frame

Example 32-bit PTE (4KB pages):
+---+---+---+-------+--------------------+
| V | R | M |  Prot |  Frame # (20 bits) |
+---+---+---+-------+--------------------+
 31  30  29  28-24         23-0

Can address 2^20 frames * 4KB = 4 GB physical memory
```

---

## Segmentation

Divide memory into logical segments (not fixed size).

### Segment Types

```
Logical Address Space:

+-------------------+  Segment 0
|      Stack        |  (Stack segment)
+-------------------+  
|                   |
|       ↓           |
|                   |
|       ↑           |
+-------------------+  Segment 1
|      Heap         |  (Heap segment)
+-------------------+  
|                   |
+-------------------+  Segment 2
|      Data         |  (Data segment)
+-------------------+  
|      Code         |  Segment 3
|                   |  (Code segment)
+-------------------+  

Each segment:
- Logical unit (code, data, stack, etc.)
- Variable size
- Has meaning to programmer
```

### Segmentation Hardware

```
Logical Address:
+------------------+------------------+
| Segment Number   |     Offset       |
+------------------+------------------+
        |                   |
        v                   |
+----------------+          |
| Segment Table  |          |
+----------------+          |
        |                   |
        v                   |
+----------------+          |
| Base  | Limit  |          |
+----------------+          |
    |       |               |
    |       v               |
    |   Check: offset       |
    |   < limit?            |
    |       |               |
    |       | Yes           |
    |       v               |
    +-------+---------------+
            |
            v
    Physical Address =
    Base + Offset
```

### Segment Table Entry

```
+-----------+--------+-----------------+
| Base      | Limit  | Protection Bits |
+-----------+--------+-----------------+

Base: Starting physical address of segment
Limit: Length of segment
Protection: Read/Write/Execute permissions

Example:
Segment 0 (Code):   Base=4000,  Limit=2000,  Protection=RX
Segment 1 (Data):   Base=8000,  Limit=3000,  Protection=RW
Segment 2 (Stack):  Base=12000, Limit=1000,  Protection=RW
```

### Segmentation with Paging

Combine advantages of both:

```
Logical Address:
+----------+------------+-----------+
| Segment# | Page#      | Offset    |
+----------+------------+-----------+
     |          |            |
     v          |            |
Segment Table   |            |
     |          |            |
     v          v            |
  Page Table                 |
     |                       |
     v                       |
  Frame #                    |
     |                       |
     +-----------------------+
                |
                v
        Physical Address

Example: Intel x86 (before x86-64):
- Segmentation for logical division
- Paging for memory management
- Best of both worlds
```

---

## Virtual Memory

Separation of logical memory from physical memory.

### Concept

```
Virtual Address Space         Physical Memory
(e.g., 4 GB per process)     (e.g., 1 GB total)

Process A:                    RAM:
+------------+               +-----------+
| 0-4GB      |               | OS Kernel |
| (Virtual)  |               +-----------+
+------------+               | Process A |
                             | (parts)   |
Process B:                   +-----------+
+------------+               | Process B |
| 0-4GB      |  <======>     | (parts)   |
| (Virtual)  |    MMU+OS     +-----------+
+------------+               | Free      |
                             +-----------+
Process C:
+------------+               Disk (Swap):
| 0-4GB      |               +-----------+
| (Virtual)  |               | Process A |
+------------+               | (parts)   |
                             +-----------+
                             | Process B |
Each process thinks it       | (parts)   |
has entire address space     +-----------+
                             | Process C |
                             | (parts)   |
                             +-----------+
```

### Benefits of Virtual Memory

1. **More processes in memory**: Only active pages need to be in RAM
2. **Larger address space**: Process can be larger than physical memory
3. **Protection**: Each process has its own virtual space
4. **Sharing**: Pages can be shared between processes (shared libraries)
5. **Efficiency**: Only load needed pages

### Demand Paging

Load pages only when needed (on demand).

```
Process starts:
+----------+
| Only     |
| essential|  <-- Only these in memory
| pages    |
| loaded   |
+----------+

     Disk:
+------------+
| All other  |
| pages      |
| waiting    |
+------------+

When page accessed:
    |
    v
Page in memory? (Check Valid bit)
    |
    +---> Yes: Use it
    |
    +---> No: Page Fault
            |
            v
       +---------+
       | 1. Trap |
       | to OS   |
       +---------+
            |
            v
       +---------+
       | 2. Find |
       | page on |
       | disk    |
       +---------+
            |
            v
       +---------+
       | 3. Load |
       | into    |
       | memory  |
       +---------+
            |
            v
       +---------+
       | 4. Update|
       | page    |
       | table   |
       +---------+
            |
            v
       +---------+
       | 5. Restart|
       | instruction|
       +---------+
```

### Page Fault Handling

```
Step-by-step:

1. Process accesses page:
   +--------+
   | MOV AX,|
   | [1000] |  <-- Address in page not in memory
   +--------+

2. MMU generates page fault (trap):
   User Mode -----> Kernel Mode

3. OS handles page fault:
   a) Check if address is valid
   b) Find free frame (or evict a page)
   c) Read page from disk into frame
   d) Update page table
   e) Set valid bit

4. Resume process:
   Kernel Mode -----> User Mode
   Restart instruction

Effective Access Time with demand paging:
EAT = (1 - p) * memory_access + p * page_fault_time

Where:
p = page fault rate (typically 0.001 or less)
memory_access = 100 ns
page_fault_time = 10 ms (disk access)

EAT = 0.999 * 100ns + 0.001 * 10ms
    = 99.9 ns + 10,000 ns
    = 10,099.9 ns
    
Even 1 page fault per 1000 accesses increases time by 100x!
Goal: Keep page fault rate very low
```

### Copy-on-Write (COW)

Efficient process creation technique.

```
Parent Process          After fork()         After write by child

+--------+                                    +--------+  +--------+
| Page A |             Parent:                | Page A |  | Page A'|
+--------+             +--------+             +--------+  +--------+
| Page B |             | Page A |                 |           |
+--------+             +--------+             +--------+  +--------+
| Page C |             | Page B |             | Page B |  | Page B |
+--------+             +--------+             +--------+  +--------+
                       | Page C |                 |           |
                       +--------+             +--------+  +--------+
                                              | Page C |  | Page C |
    fork()            Child:                  +--------+  +--------+
      |               +--------+                                |
      |               | Page A | <-- Points to same            |
      v               +--------+     physical pages            |
                      | Page B |     (read-only)               |
Child Process         +--------+                               |
+--------+            | Page C |                               |
| Page A |            +--------+        Child writes to Page A |
+--------+                              Copy made, redirect    |
| Page B |                              +----------------------+
+--------+
| Page C |            Benefits:
+--------+            - Fast fork (no immediate copy)
                      - Memory efficient
                      - Copy only what changes
```

---

## Page Replacement Algorithms

When memory is full and page fault occurs, must replace a page.

### Page Replacement Process

```
1. Page fault occurs
2. Find page on disk
3. Find free frame:
   a) If free frame exists: use it
   b) If no free frame:
      - Select victim page (page replacement algorithm)
      - Write victim to disk if modified (dirty bit set)
      - Mark victim's page table entry as invalid
      - Load new page into freed frame
4. Update page table
5. Resume process

With Page Replacement:
+---------+    +---------+    +---------+
| Disk    |    | Memory  |    | Disk    |
|         |    |         |    |         |
| Page X  |--->| Frame   |--->| Page Y  |
|         | Load|         |Save|         |
+---------+    +---------+    +---------+
  Needed       Evict victim    Old page
   page           page
```

### 1. FIFO (First-In-First-Out)

Replace the oldest page in memory.

```
Reference String: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
Number of Frames: 3

Time: 1  2  3  4  5  6  7  8  9  10 11 12 13
Page: 7  0  1  2  0  3  0  4  2  3  0  3  2

Frame 1: 7  7  7  2  2  2  2  4  4  4  0  0  0
Frame 2:    0  0  0  0  3  3  3  2  2  2  2  2
Frame 3:       1  1  1  1  0  0  0  3  3  3  3
         
         F  F  F  F     F     F  F     F  F     
         
F = Page Fault
Page Faults: 10

Simple queue:
+---------+     +---------+     +---------+
| Page 7  | --> | Page 0  | --> | Page 1  | --> Remove oldest
+---------+     +---------+     +---------+
 Oldest                          Newest

Problem: Belady's Anomaly
More frames can sometimes cause more page faults!
```

### 2. Optimal Algorithm (OPT)

Replace page that will not be used for longest period (theoretical, needs future knowledge).

```
Reference String: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
Number of Frames: 3

Time: 1  2  3  4  5  6  7  8  9  10 11 12 13
Page: 7  0  1  2  0  3  0  4  2  3  0  3  2

Frame 1: 7  7  7  2  2  2  2  2  2  2  2  2  2
Frame 2:    0  0  0  0  0  0  4  4  4  0  0  0
Frame 3:       1  1  1  3  3  3  3  3  3  3  3
         
         F  F  F  F     F     F              F
         
Page Faults: 7 (optimal - minimum possible)

Look ahead:
At time 6, pages in memory: 2, 0, 1
Next uses: 0@7, 2@9, 1@never (in visible future)
Replace 1 (used farthest in future)

Not practical (need to know future), but used as benchmark
```

### 3. LRU (Least Recently Used)

Replace page that has not been used for longest time (approximation of OPT).

```
Reference String: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
Number of Frames: 3

Time: 1  2  3  4  5  6  7  8  9  10 11 12 13
Page: 7  0  1  2  0  3  0  4  2  3  0  3  2

Frame 1: 7  7  7  2  2  2  2  4  4  3  3  3  3
Frame 2:    0  0  0  0  3  3  3  2  2  0  0  0
Frame 3:       1  1  1  1  0  0  0  0  0  0  2
         
         F  F  F  F     F     F     F  F  F     F
         
Page Faults: 10

Implementation options:
a) Counter: Timestamp each page access
b) Stack: Keep stack of page numbers (most recent on top)

Time  Stack (top = most recent)
1     [7]
2     [0, 7]
3     [1, 0, 7]
4     [2, 1, 0]  (7 evicted)
5     [0, 2, 1]  (0 moved to top)
...
```

### 4. LRU Approximation: Second Chance (Clock Algorithm)

Use reference bit, approximate LRU with less overhead.

```
Circular Queue (Clock):

     R=1        R=0        R=1
   +-----+    +-----+    +-----+
   |  A  |    |  B  |    |  C  |
   +-----+    +-----+    +-----+
                           |
                           | Clock hand
                           v
   +-----+              +-----+
   |  F  |              |  D  |
   +-----+              +-----+
     R=0                  R=1
     
Algorithm:
1. Check page at clock hand
2. If R=0: Replace this page
3. If R=1: Set R=0, advance hand
4. Repeat until R=0 found

Example:
Need to replace page, hand points to D:
- D has R=1, set R=0, advance to C
- C has R=1, set R=0, advance to B
- B has R=0, replace B!

"Second chance": Pages get R=1 set to R=0 before replacement
```

### 5. Enhanced Second Chance

Use both reference (R) and modify (M) bits.

```
Four classes (in order of preference for replacement):

Class 0: (R=0, M=0)  Not recently used, not modified
                     BEST to replace (no write needed)
                     
Class 1: (R=0, M=1)  Not recently used, but modified
                     Must write to disk before replace
                     
Class 2: (R=1, M=0)  Recently used, not modified
                     Likely to be used again soon
                     
Class 3: (R=1, M=1)  Recently used and modified
                     WORST to replace (actively used + must write)

Algorithm:
1. Scan for (0,0) - if found, replace
2. Scan for (0,1) - if found, replace (but must write)
3. Scan for (1,0) - clear R bits during scan, if found replace
4. Scan for (1,1) - clear R bits during scan, if found replace

Advantage: Prefer clean pages (no disk write needed)
```

### Comparison

```
Algorithm      Page Faults    Implementation    Overhead
---------------------------------------------------------
Optimal             7           Impossible        -
LRU                10           Complex          High
FIFO               10           Simple           Low
Second Chance      ~10          Moderate         Moderate
Enhanced 2nd       ~10          Moderate         Moderate

Optimal: Theoretical minimum
LRU: Excellent but expensive to implement perfectly
FIFO: Simple but suffers from Belady's Anomaly
Clock algorithms: Good approximation of LRU, practical
```

---

## Thrashing

Process is busy swapping pages in/out more than executing.

### Thrashing Diagram

```
CPU Utilization vs Degree of Multiprogramming:

CPU
Util
    |              ╱‾‾╲
100%|            ╱     ╲
    |          ╱        ╲___
    |        ╱               ╲___
    |      ╱                     ╲___
    |    ╱                           ╲___
    |  ╱                                 ╲
  0%|╱___________________________________ ╲____
    +------------------------------------->
    0    Good      Thrashing          Number of
         region   starts here          processes
```

### Why Thrashing Occurs

```
Process behavior:

Working Set (pages needed at this time):
+------------------+
| Page 5, 7, 12    |  Currently executing code section
| Page 20, 21      |  Data being accessed
+------------------+

If working set fits in memory: Good performance
If working set doesn't fit: Thrashing!

Example with 3 processes:

Available Memory: 10 frames
Process A needs: 5 frames (working set)
Process B needs: 4 frames (working set)
Process C needs: 3 frames (working set)
Total needed: 12 frames

Result: Not enough memory!
Process A pages out -> uses disk
Process B runs -> needs A's pages -> page fault
Process C runs -> needs B's pages -> page fault
System spends all time paging

CPU utilization drops dramatically!
```

### Solutions to Thrashing

#### 1. Working Set Model

```
Working Set Δ = set of pages referenced in last Δ time

Example:
Page reference string (time window Δ = 10):
... 2, 6, 1, 5, 7, 7, 7, 7, 5, 1, 6, 2, 3, 4 ...
                        └────────────┘
                         Last 10 refs
                         
Working Set = {1, 2, 3, 4, 5, 6, 7}  (7 pages)

Algorithm:
1. Estimate working set size for each process
2. If Σ(WSS) > total frames:
   - Suspend/swap out some processes
3. If Σ(WSS) << total frames:
   - Can admit more processes
```

#### 2. Page Fault Frequency (PFF)

```
Page Fault Rate vs Allocated Frames:

PF Rate
  |  ╲
  |   ╲  Upper threshold
  |    ╲ _______________
  |     ╲
  |      ╲
  |       ╲
  |        ╲
  |         ╲_______________ Lower threshold
  |                    ╲
  |                     ╲
  +------------------------>
                    Frames allocated

If PF rate > upper: Allocate more frames
If PF rate < lower: Remove frames
If cannot allocate: Swap out process
```

### Locality of Reference

Programs tend to reference memory in patterns.

```
Temporal Locality:
If accessed now, likely to access again soon
Example: Loop counter, frequently called functions

Time: ----1----2----3----4----5---->
Page:     A    A    A    A    A
          ↑              ↑
          └──────────────┘
          Same page accessed repeatedly

Spatial Locality:
If accessed now, likely to access nearby addresses
Example: Array access, sequential code execution

Address: [A][B][C][D][E][F][G][H]
Access:   ↑  ↑  ↑
          Sequential access pattern
          
Program execution phases:
+----------------+
| Initialization | <- One set of pages
+----------------+
| Main loop      | <- Different set of pages
+----------------+
| Cleanup        | <- Another set of pages
+----------------+

Each phase has its locality (working set)
```

---

## Memory Allocation for Kernel

### 1. Buddy System

```
Initial: 1024 KB

Request 70 KB:
Split 1024 -> 512 + 512
Split 512 -> 256 + 256
Split 256 -> 128 + 128
Allocate 128 KB for 70 KB request

+--------+--------+--------+--------+--------+--------+
| 128    | 128    | 256             | 512             |
| (used) | (free) | (free)          | (free)          |
+--------+--------+--------+--------+--------+--------+

Free List:
128: [1 block]
256: [1 block]
512: [1 block]

Advantages:
- Fast allocation/deallocation
- Easy coalescing (merge buddies)

Disadvantages:
- Internal fragmentation (power of 2 sizes)
```

### 2. Slab Allocator

```
Used by Linux kernel for object caching.

For objects of size 32 bytes:

+------------------------+
|  Slab 1 (Full)        |
|  [obj][obj][obj][obj]  |
+------------------------+
|  Slab 2 (Partial)     |
|  [obj][free][free][obj]|
+------------------------+
|  Slab 3 (Empty)       |
|  [free][free][free][free]|
+------------------------+

Advantages:
- No fragmentation for fixed-size objects
- Fast allocation (pre-allocated)
- Cache-friendly (objects reused, stay in cache)
```

---

## Summary

- **Memory Hierarchy**: Registers → Cache → RAM → Disk (speed vs. size tradeoff)
- **Address Binding**: Compile-time, Load-time, Execution-time
- **Logical vs Physical**: MMU translates logical to physical addresses
- **Contiguous Allocation**: Fixed/dynamic partitioning, fragmentation issues
- **Paging**: Fixed-size pages/frames, eliminates external fragmentation
- **Page Table**: Maps pages to frames, multi-level for large spaces
- **TLB**: Fast cache for page table entries
- **Segmentation**: Variable-size logical units, can combine with paging
- **Virtual Memory**: Separate logical from physical, demand paging
- **Page Replacement**: FIFO, Optimal, LRU, Clock algorithms
- **Thrashing**: Excessive paging, solved by working set/PFF
- **Locality**: Temporal and spatial reference patterns

---

**Next Topics:**
- File Systems
- CPU Scheduling Algorithms
- Synchronization and Deadlocks

