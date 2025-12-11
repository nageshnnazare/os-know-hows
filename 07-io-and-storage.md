# Operating Systems - I/O and Storage Systems

## Table of Contents
1. [I/O Hardware](#io-hardware)
2. [I/O Software](#io-software)
3. [I/O Performance](#io-performance)
4. [Disk Structure](#disk-structure)
5. [Disk Scheduling](#disk-scheduling)
6. [RAID](#raid)
7. [Solid State Drives (SSD)](#solid-state-drives-ssd)

---

## I/O Hardware

### I/O Devices

```
CLASSIFICATION:

1. BY SPEED:
   +----------------+
   | Very Fast      | Memory, Cache
   +----------------+
   | Fast           | Network, SSD
   +----------------+
   | Medium         | HDD, Tape
   +----------------+
   | Slow           | Keyboard, Mouse
   +----------------+

2. BY DATA RATE:
   +----------------+---------------+
   | Device         | Data Rate     |
   +----------------+---------------+
   | Keyboard       | 10 bytes/sec  |
   | Mouse          | 100 bytes/sec |
   | Scanner        | 400 KB/sec    |
   | USB 2.0        | 60 MB/sec     |
   | HDD            | 200 MB/sec    |
   | SSD            | 500 MB/sec    |
   | NVMe SSD       | 3500 MB/sec   |
   | Network (1Gb)  | 125 MB/sec    |
   | Network (10Gb) | 1250 MB/sec   |
   +----------------+---------------+

3. BY UNIT OF TRANSFER:
   - Character devices: Keyboard, mouse (byte stream)
   - Block devices: Disk, tape (blocks)
```

### I/O Port Registers

```
DEVICE CONTROLLER REGISTERS:

+------------------------+
| Status Register        | (Read-only)
| - Busy bit             |
| - Ready bit            |
| - Error bit            |
+------------------------+
| Control Register       | (Write-only)
| - Command bits         |
| - Mode bits            |
+------------------------+
| Data-In Register       | (Read)
| - Input data           |
+------------------------+
| Data-Out Register      | (Write)
| - Output data          |
+------------------------+

Example: Serial Port
Base Address: 0x3F8

0x3F8 + 0: Data Register
0x3F8 + 1: Interrupt Enable
0x3F8 + 2: Interrupt ID / FIFO Control
0x3F8 + 3: Line Control
0x3F8 + 4: Modem Control
0x3F8 + 5: Line Status
0x3F8 + 6: Modem Status
```

### I/O Communication

#### 1. Polling (Programmed I/O)

```
CPU POLLING:

CPU:                        Device:
  |                             |
  | Write command               |
  +---------------------------->|
  |                             | Processing
  | Read status                 |
  |<----------------------------+
  | Busy? Yes, loop             |
  |                             |
  | Read status                 |
  |<----------------------------+
  | Busy? Yes, loop             |
  |                             |
  | Read status                 |
  |<----------------------------+
  | Busy? No, continue          |
  |                             |
  | Read data                   |
  |<----------------------------+
  v                             v

Code:
while (true) {
  status = read_status_register();
  if (status & READY_BIT)
    break;  // Device ready
}
data = read_data_register();

Advantages:
+ Simple implementation
+ No interrupt overhead

Disadvantages:
- Busy waiting (wastes CPU)
- Inefficient for slow devices
```

#### 2. Interrupt-Driven I/O

```
CPU:                        Device:
  |                             |
  | Write command               |
  +---------------------------->|
  |                             | Processing
  | Continue other work         |
  |                             |
  | Execute other tasks         |
  |                             |
  |                   Interrupt |
  |<----------------------------+
  | Save context                |
  | Handle interrupt            |
  | Read data                   |
  |<----------------------------+
  | Restore context             |
  | Resume work                 |
  v                             v

Interrupt Handling:
1. Device raises interrupt
2. CPU finishes current instruction
3. Save PC and registers
4. Jump to interrupt handler (ISR)
5. ISR processes interrupt
6. Restore context
7. Resume interrupted process

Interrupt Vector Table:
+-----+-------------------+
| IRQ | Handler Address   |
+-----+-------------------+
|  0  | Timer ISR         |
|  1  | Keyboard ISR      |
|  2  | Cascade           |
|  3  | Serial Port ISR   |
|  4  | Serial Port ISR   |
|  5  | Sound Card ISR    |
|  ...| ...               |
+-----+-------------------+

Advantages:
+ CPU not wasted in busy waiting
+ Efficient for slow devices

Disadvantages:
- Interrupt overhead
- Still involves CPU for data transfer
```

#### 3. Direct Memory Access (DMA)

```
WITHOUT DMA:
CPU reads from device, writes to memory
(CPU involved in every byte transfer)

Disk → CPU → Memory
       ↓
   Bottleneck

WITH DMA:
CPU sets up DMA controller
DMA transfers data directly

        CPU
         ↓ (Setup)
    DMA Controller
         ↓ (Transfer)
    Disk → Memory

DMA OPERATION:

1. CPU Setup:
   +----------------+
   | DMA Controller |
   +----------------+
   | Source: 0x1000 | (Disk buffer)
   | Dest:   0x5000 | (Memory)
   | Count:  4096   | (Bytes)
   | Mode:   Read   |
   +----------------+

2. DMA Transfer:
   Disk → DMA Controller → Memory
   (No CPU involvement)

3. Completion:
   DMA sends interrupt to CPU
   CPU: "Transfer complete!"

Timeline:
CPU:  [Setup DMA]--------[Do other work]--------[Handle interrupt]
DMA:                [====Data Transfer====]
                    (CPU free to do other tasks)

Advantages:
+ Offloads CPU
+ Efficient for large transfers
+ High throughput

Disadvantages:
- More complex hardware
- Interrupt for completion

DMA MODES:

1. Burst Mode:
   DMA takes over bus
   Transfers entire block
   CPU stalled
   
   |===DMA Transfer===| (CPU waits)

2. Cycle Stealing:
   DMA steals bus cycles
   One byte at a time
   CPU can still access memory
   
   DMA: |█| |█| |█| |█|
   CPU:    |█|  |█|  |█|
   (Interleaved access)

3. Transparent Mode:
   DMA uses bus when CPU not using it
   No CPU degradation
   Slower transfer
```

---

## I/O Software

### I/O Software Layers

```
+---------------------------------------+
| User-Level I/O Software               |
| - Libraries (stdio, iostream)         |
| - Spooling (print queues)             |
+---------------------------------------+
         ↓ System Calls
+---------------------------------------+
| Device-Independent OS Software        |
| - Naming (map names to devices)       |
| - Protection (access control)         |
| - Buffering                           |
| - Error handling                      |
| - Allocating/releasing devices        |
+---------------------------------------+
         ↓ Kernel Functions
+---------------------------------------+
| Device Drivers                        |
| - Device-specific code                |
| - Initialize device                   |
| - Handle interrupts                   |
| - Manage device queue                 |
+---------------------------------------+
         ↓ Hardware Interface
+---------------------------------------+
| Interrupt Handlers                    |
| - Save context                        |
| - Minimal processing                  |
| - Signal device driver                |
+---------------------------------------+
         ↓
+---------------------------------------+
| Hardware (Controllers, Devices)       |
+---------------------------------------+
```

### Device Drivers

```
DRIVER FUNCTIONS:

1. Initialization:
   - Detect device
   - Configure registers
   - Set up interrupt handlers
   
2. Read/Write Operations:
   read_driver(device, buffer, size):
     - Check device status
     - Start I/O operation
     - Wait for completion
     - Handle errors
     - Return data

3. Interrupt Handling:
   interrupt_handler():
     - Acknowledge interrupt
     - Determine cause
     - Process data
     - Wake up waiting process

4. Device Control:
   ioctl(device, command, arg):
     - Set baud rate (serial)
     - Set screen resolution
     - Eject media (CD/DVD)

DRIVER INTERFACE:

Linux Driver:
+---------------------------+
| struct file_operations {  |
|   .open    = device_open  |
|   .read    = device_read  |
|   .write   = device_write |
|   .release = device_close |
|   .ioctl   = device_ioctl |
| }                         |
+---------------------------+

Windows Driver:
+---------------------------+
| DriverEntry()             |
| AddDevice()               |
| IRP_MJ_READ               |
| IRP_MJ_WRITE              |
| IRP_MJ_DEVICE_CONTROL     |
+---------------------------+
```

### Buffering

```
1. NO BUFFERING:
   User Process → Device (Direct)
   
   Problem: Process blocks during I/O

2. SINGLE BUFFER:
   
   User Process → [Buffer] → Device
   
   Process writes to buffer (fast)
   Device reads from buffer (slow)
   
   Timeline:
   User:   |Write|-----Wait-----|Write|
   Device:      |===Read===|===Read===|

3. DOUBLE BUFFERING:
   
   User Process → [Buffer 1]
                  [Buffer 2] → Device
   
   Ping-pong buffering:
   User writes to Buffer 1 while
   Device reads from Buffer 2
   
   Timeline:
   User:   |Write B1|Write B2|Write B1|
   Device: |Read B2 |Read B1 |Read B2 |
   
   No waiting!

4. CIRCULAR BUFFER (Ring Buffer):
   
         +---+---+---+---+---+
         | 0 | 1 | 2 | 3 | 4 |
         +---+---+---+---+---+
           ↑               ↑
         Head            Tail
      (Consumer)      (Producer)
      
   Producer adds at tail
   Consumer removes from head
   
   Advantages:
   + Multiple producers/consumers
   + Smooth out rate differences

KERNEL I/O BUFFERING:

+------------------------+
| User Space             |
| Application Buffer     |
+------------------------+
         ↓ copy
+------------------------+
| Kernel Space           |
| Kernel Buffer          |
+------------------------+
         ↓ DMA
+------------------------+
| Device Buffer          |
| (Hardware)             |
+------------------------+

Multiple copies for:
- Protection (kernel/user separation)
- Performance (async I/O)
- Device speed matching
```

### Spooling

```
SPOOLING (Simultaneous Peripheral Operations On-Line):

Example: Print Spooler

Process 1: Print Job → [Spool Queue] 
Process 2: Print Job → [Spool Queue] → Printer
Process 3: Print Job → [Spool Queue]

Spool Directory:
+----------+----------+----------+
| job001   | job002   | job003   |
| (from P1)| (from P2)| (from P3)|
+----------+----------+----------+
                ↓
           Printer Daemon
                ↓
            [Printer]

Timeline:
P1: |Print job|-----free-----|
P2:      |Print job|---free---|
P3:           |Print job|--free--|
Printer:  |===P1===|===P2===|===P3===|

Advantages:
+ Multiple processes can "print" simultaneously
+ Processes don't wait for slow device
+ Jobs queued and managed

Used for:
- Printers
- Batch processing
- Email (SMTP queue)
```

---

## I/O Performance

### Optimization Techniques

```
1. REDUCE CONTEXT SWITCHES:
   - Use DMA instead of programmed I/O
   - Batch operations
   
2. REDUCE DATA COPYING:
   - Zero-copy I/O
   - Memory-mapped I/O
   
3. INCREASE CONCURRENCY:
   - Asynchronous I/O
   - I/O threads
   
4. USE APPROPRIATE BLOCK SIZE:
   
   Small blocks:        Large blocks:
   Many I/O ops         Fewer I/O ops
   High overhead        Less overhead
   Poor throughput      Better throughput
   
   Optimal: Match device block size

5. CACHING AND BUFFERING:
   - Page cache
   - Disk cache
   - Read-ahead
   
6. I/O SCHEDULING:
   - Reorder requests
   - Merge adjacent requests
```

### I/O Modes

```
1. SYNCHRONOUS I/O (Blocking):

Process:
  fd = open("file.txt")
  read(fd, buffer, size) ← Blocks here
  [Process waits]
  [I/O completes]
  Process continues

Timeline:
|--read--|==I/O==|--continue--|

2. ASYNCHRONOUS I/O (Non-blocking):

Process:
  fd = open("file.txt")
  aio_read(fd, buffer, size) ← Returns immediately
  [Do other work]
  [Do other work]
  aio_wait() or check completion
  Process continues

Timeline:
|-aio_read-|--other work--|==wait/check==|
           |====I/O====|

Advantages:
+ Better CPU utilization
+ Overlap computation and I/O
+ Higher throughput

3. MEMORY-MAPPED I/O:

Normal I/O:
  File → read() → Buffer → Process
  
Memory-Mapped:
  File mapped to address space
  Access like memory
  
  char *p = mmap(fd, ...);
  char c = p[100]; ← Direct access
  
Advantages:
+ No read/write system calls
+ No buffer copying
+ Natural for some applications
```

---

## Disk Structure

### Hard Disk Drive (HDD) Anatomy

```
TOP VIEW:
                Spindle
                  |
     +-----------+------------+
    /            |             \
   /    Platter  |  Platter     \
  /      (Disk)  |  (Disk)       \
 +---------------+----------------+
               Read/Write Heads
                  (moves)

SIDE VIEW:

        Actuator Arm
             |
    +--------+---------+
    |   Read/Write     |
    |      Head        |
    +------------------+
         Platter
    +==================+
    |   Track 0        |
    |   Track 1        |
    |   Track 2        |
    |   ...            |
    +==================+

CYLINDER, TRACK, SECTOR:

        Cylinder (vertical)
             |||
        +----|||----+
        |    |||    | Platter 0
        +----|||----+
        |    |||    | Platter 1
        +----|||----+
        |    |||    | Platter 2
        +----|||----+

TRACK (concentric circles):
        
        +-------------------+
        |  +--------------+ |
        |  |  +---------+ | |
        |  |  |Track 0  | | | Track 2
        |  |  |Track 1  | | |
        |  |  +---------+ | |
        |  +--------------+ |
        +-------------------+

SECTOR (pizza slice):

        +-------+
       /|  S1  |\
      / | S2 S3| \
     /  |      |  \
    +---+------+---+
     \  | S4 S5|  /
      \ | S6   | /
       \|  S7  |/
        +-------+

Each sector: Typically 512 bytes or 4096 bytes
```

### Disk Addressing

```
1. CHS (Cylinder-Head-Sector):
   
   Address: (Cylinder, Head, Sector)
   Example: (100, 2, 10)
   
   Calculation:
   LBA = ((Cylinder × Heads + Head) × Sectors) + (Sector - 1)

2. LBA (Logical Block Addressing):
   
   Linear address space
   Block 0, Block 1, Block 2, ...
   
   Example:
   Block 0 → Cylinder 0, Head 0, Sector 1
   Block 1 → Cylinder 0, Head 0, Sector 2
   ...
   
   Simpler for OS (abstraction)
   Controller handles mapping

DISK PARAMETERS:

Example: 1 TB Hard Drive
- Platters: 4
- Heads: 8 (2 per platter)
- Cylinders: 500,000
- Sectors per track: 1,000 (average)
- Sector size: 512 bytes

Capacity:
= Cylinders × Heads × Sectors/Track × Sector Size
= 500,000 × 8 × 1,000 × 512
≈ 2 TB (unformatted)
≈ 1 TB (formatted)
```

### Disk Access Time

```
ACCESS TIME COMPONENTS:

1. SEEK TIME:
   Time to move head to correct track
   
   +--------+  Move head  +--------+
   |Track 0 |  ========>  |Track 50|
   +--------+             +--------+
   
   Average: 4-10 ms
   Min (adjacent): 0.5-1 ms
   Max (full stroke): 10-20 ms

2. ROTATIONAL LATENCY:
   Time for sector to rotate under head
   
        Head position
            ↓
   +--------+--------+
   |  Wait  | Target |
   |  for   | Sector |
   | Rotation|       |
   +--------+--------+
      ↓ Rotation
   
   Average: 1/2 rotation
   7200 RPM: 60s / 7200 / 2 = 4.17 ms
   10000 RPM: 3 ms
   15000 RPM: 2 ms

3. TRANSFER TIME:
   Time to read/write data
   
   Transfer rate: 100-200 MB/s
   For 4 KB block:
   4096 bytes / 100 MB/s ≈ 0.04 ms

TOTAL ACCESS TIME:

Access Time = Seek + Rotational Latency + Transfer

Example (7200 RPM drive):
= 8 ms + 4.17 ms + 0.04 ms
≈ 12.2 ms per operation

For sequential access:
First block: 12.2 ms
Next blocks: 0.04 ms each (no seek/rotation)

Sequential vs Random:
Sequential: 100 MB/s
Random: 1000 / 12.2 ≈ 82 IOPS (I/O Ops Per Second)
```

---

## Disk Scheduling

Goal: Minimize seek time by ordering disk requests.

### FCFS (First-Come-First-Served)

```
REQUEST QUEUE: 98, 183, 37, 122, 14, 124, 65, 67
HEAD START: 53

TIMELINE:
53 → 98 → 183 → 37 → 122 → 14 → 124 → 65 → 67

VISUALIZATION:
0    14   37  53 65 67  98    122 124     183    200
|----|----|---|--|--|---|-----|---|-------|-------|
     ←←←←←←←←←←          →→→→→→→

Total head movement:
|53-98| + |98-183| + |183-37| + |37-122| + 
|122-14| + |14-124| + |124-65| + |65-67|
= 45 + 85 + 146 + 85 + 108 + 110 + 59 + 2
= 640 cylinders

Advantages:
+ Fair (no starvation)
+ Simple

Disadvantages:
- No optimization
- Poor performance
```

### SSTF (Shortest Seek Time First)

```
REQUEST QUEUE: 98, 183, 37, 122, 14, 124, 65, 67
HEAD START: 53

SELECT CLOSEST REQUEST EACH TIME:

Start at 53:
  Closest: 65 (distance 12)
53 → 65

From 65:
  Closest: 67 (distance 2)
65 → 67

From 67:
  Closest: 37 (distance 30)
67 → 37

From 37:
  Closest: 14 (distance 23)
37 → 14

From 14:
  Closest: 98 (distance 84)
14 → 98

From 98:
  Closest: 122 (distance 24)
98 → 122

From 122:
  Closest: 124 (distance 2)
122 → 124

From 124:
  Closest: 183 (distance 59)
124 → 183

TIMELINE:
53 → 65 → 67 → 37 → 14 → 98 → 122 → 124 → 183

Total: 12 + 2 + 30 + 23 + 84 + 24 + 2 + 59 = 236 cylinders

Advantages:
+ Better throughput than FCFS
+ Lower average seek time

Disadvantages:
- Starvation possible (far requests)
- Not optimal (greedy algorithm)
```

### SCAN (Elevator Algorithm)

```
REQUEST QUEUE: 98, 183, 37, 122, 14, 124, 65, 67
HEAD START: 53
DIRECTION: Initially moving towards 0

Move towards 0, service requests:
53 → 37 → 14 → 0

Reverse direction, move towards 199:
0 → 65 → 67 → 98 → 122 → 124 → 183

TIMELINE:
0    14   37  53 65 67  98    122 124     183    199
|----|----|---|--|--|---|-----|---|-------|-------|
←←←←←                →→→→→→→→→→→→→→→→→→→→→→→→→→→

Total: 53 + 183 = 236 cylinders

Advantages:
+ No starvation
+ Predictable
+ Good for heavy load

Disadvantages:
- Long wait for requests just missed
```

### C-SCAN (Circular SCAN)

```
REQUEST QUEUE: 98, 183, 37, 122, 14, 124, 65, 67
HEAD START: 53
DIRECTION: Initially moving towards 199

Move towards end:
53 → 65 → 67 → 98 → 122 → 124 → 183 → 199

Jump to beginning:
199 → 0

Move from beginning:
0 → 14 → 37

TIMELINE:
0    14   37  53 65 67  98    122 124     183    199
|----|----|---|--|--|---|-----|---|-------|-------|
                 →→→→→→→→→→→→→→→→→→→→→→→→→→→→
                                                 |
                                                 ↓
←←←←←←                                          [Jump]

Total: (199-53) + (199-0) + (37-0) = 146 + 199 + 37 = 382 cylinders

Advantages:
+ More uniform wait time
+ Treats ends fairly

Disadvantages:
- More head movement than SCAN
```

### LOOK and C-LOOK

```
LOOK: Like SCAN but doesn't go to end
Only goes as far as last request

REQUEST QUEUE: 98, 183, 37, 122, 14, 124, 65, 67
HEAD START: 53

53 → 37 → 14 (reverse, don't go to 0)
14 → 65 → 67 → 98 → 122 → 124 → 183

Timeline:
14   37  53 65 67  98    122 124     183
|----|---|--|--|---|-----|---|-------|
←←←←←       →→→→→→→→→→→→→→→→→→→→→→→

Total: (53-14) + (183-14) = 39 + 169 = 208 cylinders

C-LOOK: Circular LOOK

53 → 65 → 67 → 98 → 122 → 124 → 183 (jump to 14)
183 → 14 → 37

Total: (183-53) + (183-14) + (37-14) = 130 + 169 + 23 = 322 cylinders
```

### Algorithm Comparison

```
Algorithm   Total Movement   Advantages           Disadvantages
------------------------------------------------------------------------
FCFS        640              Fair, simple         Poor performance
SSTF        236              Good throughput      Starvation possible
SCAN        236              No starvation        Bias to middle
C-SCAN      382              Uniform wait         More movement
LOOK        208              Better than SCAN     Implementation
C-LOOK      322              Uniform, efficient   Complex

Modern drives:
- NCQ (Native Command Queueing)
- Drive knows physical layout
- Can optimize internally
- OS provides multiple requests
- Drive reorders optimally
```

---

## RAID

**RAID** (Redundant Array of Independent Disks): Multiple disks for performance/reliability.

### RAID Levels

```
RAID 0 (Striping - No Redundancy):

File: [A][B][C][D][E][F][G][H]

Disk 0: [A][C][E][G]
Disk 1: [B][D][F][H]

Read A+B: Parallel from Disk 0 and Disk 1
Write C+D: Parallel to both disks

Performance: 2× (with 2 disks)
Capacity: 100% (all disks)
Reliability: WORSE (any disk fails = data loss)

Use: High performance, no fault tolerance needed


RAID 1 (Mirroring):

File: [A][B][C][D]

Disk 0: [A][B][C][D]
Disk 1: [A][B][C][D]  (Mirror)

Write A: Write to both disks
Read A: Read from either disk (2× read performance)

Performance: 2× read, 1× write
Capacity: 50% (half wasted on redundancy)
Reliability: Can lose 1 disk

Use: Critical data, high read performance


RAID 2 (Bit-Level Striping + Hamming Code):

Rarely used, requires synchronized disks
Uses Hamming code for error correction


RAID 3 (Byte-Level Striping + Parity):

File: [A][B][C][D]
Parity: A⊕B⊕C⊕D

Disk 0: [A]
Disk 1: [B]
Disk 2: [C]
Disk 3: [D]
Disk 4: [P] (Parity)

If Disk 2 fails:
C = A⊕B⊕D⊕P (reconstruct)

Performance: N× (for large transfers)
Capacity: (N-1)/N (N disks)
Reliability: Can lose 1 disk

Disadvantage: Parity disk bottleneck


RAID 4 (Block-Level Striping + Parity):

File: [A][B][C][D]

Disk 0: [A]
Disk 1: [B]
Disk 2: [C]
Disk 3: [P] (A⊕B⊕C)

Similar to RAID 3 but block-level
Still has parity disk bottleneck on writes


RAID 5 (Block-Level Striping + Distributed Parity):

File: [A1][B1][C1][A2][B2][C2]

Disk 0: [A1][B2][Pc]
Disk 1: [B1][Pc][A2]
Disk 2: [C1][Pa][B2]

Parity distributed across disks
Pa = A1⊕A2
Pb = B1⊕B2
Pc = C1⊕C2

Performance: (N-1)× read, ~(N-1)/2× write
Capacity: (N-1)/N
Reliability: Can lose 1 disk
No bottleneck!

Most popular RAID level
Good balance of performance, capacity, reliability


RAID 6 (Block-Level Striping + Double Parity):

File: [A][B][C][D]

Disk 0: [A][Q]
Disk 1: [B][Px]
Disk 2: [C][Py]
Disk 3: [D][Pz]

Two parity schemes (P and Q)
Can lose 2 disks

Capacity: (N-2)/N
Reliability: Better (2 disk failures)
Performance: Slower writes (2 parities)

Use: Critical data, large arrays


RAID 10 (1+0, Mirrored Stripes):

        Stripe
    +-----+-----+
    |     |     |
  Mirror Mirror
  +---+  +---+
  D0 D1  D2 D3

Level 1: D0↔D1 mirrored, D2↔D3 mirrored
Level 0: Stripe across the two mirrors

File: [A][B][C][D]
D0: [A][C]   D1: [A][C] (mirror)
D2: [B][D]   D3: [B][D] (mirror)

Performance: N/2× (read), N/2× (write)
Capacity: 50%
Reliability: Can lose 1 disk per mirror

Better than RAID 1 (performance)
Better than RAID 5 (write performance)
```

### RAID Comparison

```
Level  Capacity  Read Perf  Write Perf  Fault Tolerance  Use Case
------------------------------------------------------------------------
0      100%      High       High        None             Performance
1      50%       High       Medium      1 disk           Critical data
5      (N-1)/N   High       Medium      1 disk           General purpose
6      (N-2)/N   High       Low         2 disks          High reliability
10     50%       High       High        N/2 disks        High performance
                                                         + reliability
```

---

## Solid State Drives (SSD)

### SSD vs HDD

```
ARCHITECTURE:

HDD:                           SSD:
+----------------+            +----------------+
| Platters       |            | NAND Flash     |
| (magnetic)     |            | Memory Chips   |
+----------------+            +----------------+
| Actuator Arm   |            | Controller     |
| (mechanical)   |            | (no moving     |
+----------------+            |  parts)        |
                              +----------------+

COMPARISON:

Characteristic    HDD                SSD
---------------------------------------------------------
Access Time       4-10 ms            0.1 ms
Sequential Read   100-200 MB/s       500-3500 MB/s
Random IOPS       100-200            10,000-100,000
Latency           High               Low
Durability        Mechanical wear    Write cycles
Noise             Audible            Silent
Power             5-10W              2-5W
Weight            Heavy              Light
Shock Resistance  Poor               Excellent
Cost/GB           Low                Higher
```

### NAND Flash Organization

```
HIERARCHY:

+----------------------+
| SSD                  |
+----------------------+
        ↓
+----------------------+
| Die (multiple)       |
+----------------------+
        ↓
+----------------------+
| Plane (2-4)          |
+----------------------+
        ↓
+----------------------+
| Block (many)         |
| Size: 128-256 KB     |
+----------------------+
        ↓
+----------------------+
| Page (64-128)        |
| Size: 4-8 KB         |
+----------------------+
        ↓
+----------------------+
| Cells (bits)         |
+----------------------+

CONSTRAINTS:

Read:  Page-level (4 KB)
Write: Page-level (4 KB) - but only to erased page
Erase: Block-level (256 KB) - must erase before write

Example:
Block 0:
+--+--+--+--+--+--+--+--+
|P0|P1|P2|P3|P4|P5|P6|P7|
+--+--+--+--+--+--+--+--+
 ↑  ↑  ↑
Written

To rewrite P1:
1. Cannot overwrite P1 directly
2. Must erase entire block
3. Save P0, P2-P7
4. Erase block
5. Write all pages

Solution: Write to new location + garbage collection
```

### Write Amplification

```
PROBLEM:

User writes 4 KB
SSD might write 16 KB internally

Example:
1. User writes 4 KB (page 0)
2. Page 0 marked invalid
3. Data written to new location
4. Later: Garbage collection
5. Copy valid pages to new block
6. Erase old block

Write Amplification Factor (WAF):
WAF = Actual Written / User Written

Example:
User writes 1 GB
SSD writes 1.5 GB internally
WAF = 1.5

Higher WAF = More wear, lower performance

Mitigation:
- Over-provisioning
- Efficient garbage collection
- TRIM command
```

### Wear Leveling

```
PROBLEM:
Flash cells have limited write cycles
SLC: 100,000 cycles
MLC: 10,000 cycles
TLC: 3,000 cycles
QLC: 1,000 cycles

SOLUTION: Distribute writes evenly

STATIC WEAR LEVELING:
Move static (rarely changed) data
to more worn blocks

Block 0: 1000 writes (static data)
Block 1: 5000 writes (dynamic data)

Action: Move static data from Block 0 to Block 1
Now Block 0 available for new writes

DYNAMIC WEAR LEVELING:
Write new data to least worn blocks

Write Distribution:
Without Wear Leveling:
Block 0: ▓▓▓▓▓▓▓▓▓▓ (overused)
Block 1: ▓▓ (underused)
Block 2: ▓▓ (underused)

With Wear Leveling:
Block 0: ▓▓▓▓
Block 1: ▓▓▓▓
Block 2: ▓▓▓▓ (even distribution)
```

### TRIM Command

```
WITHOUT TRIM:

File deleted:
OS marks blocks as free
SSD doesn't know!
SSD keeps data (thinks it's valid)

Later write:
SSD must read-modify-write
(Performance penalty)

WITH TRIM:

File deleted:
OS sends TRIM command
SSD marks blocks as invalid
SSD can erase proactively

Later write:
SSD writes directly
(Better performance)

TRIM Timeline:

T0: File exists
    [Data in Block 5]

T1: File deleted (OS)
    OS marks blocks as free
    OS sends TRIM to SSD

T2: SSD receives TRIM
    SSD marks Block 5 as invalid
    
T3: Garbage collection
    SSD erases Block 5
    Block 5 ready for new writes

Benefits:
+ Better write performance
+ Reduced write amplification
+ Longer SSD lifetime
```

### SSD Controller

```
SSD CONTROLLER FUNCTIONS:

+---------------------------+
| Flash Translation Layer   |
| (FTL)                     |
+---------------------------+
| - Logical to Physical     |
|   address mapping         |
| - Wear leveling           |
| - Garbage collection      |
| - Bad block management    |
| - Error correction (ECC)  |
+---------------------------+

LOGICAL TO PHYSICAL MAPPING:

OS View (LBA):              SSD Physical:
LBA 0 ------------------>   Physical Block 100, Page 0
LBA 1 ------------------>   Physical Block 100, Page 1
LBA 2 ------------------>   Physical Block 205, Page 3
...

Mapping Table:
+-----+------------------+
| LBA | Physical Address |
+-----+------------------+
|  0  | Block 100, Page 0|
|  1  | Block 100, Page 1|
|  2  | Block 205, Page 3|
| ... | ...              |
+-----+------------------+

Update LBA 1:
1. Write to new physical location (Block 205, Page 4)
2. Update mapping: LBA 1 → Block 205, Page 4
3. Invalidate old location (Block 100, Page 1)
```

---

## Summary

- **I/O Hardware**: Polling, interrupts, DMA for device communication
- **I/O Software**: Layered architecture from hardware to user space
- **Device Drivers**: Interface between OS and hardware devices
- **Buffering**: Single, double, circular buffers for performance
- **Disk Structure**: Platters, tracks, sectors, cylinders
- **Disk Scheduling**: FCFS, SSTF, SCAN, LOOK algorithms
- **RAID**: Levels 0, 1, 5, 6, 10 for performance/reliability
- **SSDs**: Flash-based, no moving parts, faster but limited writes
- **SSD Techniques**: Wear leveling, TRIM, garbage collection

I/O and storage systems are critical for system performance and reliability!

---

**Next Topics:**
- Security and Protection
- Advanced Operating System Concepts

