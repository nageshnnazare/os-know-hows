# Operating Systems - Case Studies

## Table of Contents
1. [Linux Internals](#linux-internals)
2. [Windows NT Architecture](#windows-nt-architecture)
3. [macOS and Darwin](#macos-and-darwin)
4. [Android Operating System](#android-operating-system)
5. [Comparative Analysis](#comparative-analysis)

---

## Linux Internals

### Linux Architecture

```
+---------------------------------------------------+
|               USER SPACE                          |
|                                                   |
|  +---------+  +---------+  +---------+           |
|  |  Shell  |  |  Apps   |  | Desktop |           |
|  | (bash)  |  | (gcc)   |  | (GNOME) |           |
|  +---------+  +---------+  +---------+           |
|                                                   |
|  +-----------------------------------------+     |
|  | System Libraries                        |     |
|  | - glibc (C library)                     |     |
|  | - libpthread (threading)                |     |
|  | - libm (math)                           |     |
|  +-----------------------------------------+     |
+---------------------------------------------------+
           System Call Interface (syscall)
+---------------------------------------------------+
|               KERNEL SPACE                        |
|                                                   |
|  +-------------------------------------------+   |
|  | Process Management                        |   |
|  | - Task scheduler (CFS)                    |   |
|  | - Process creation/termination            |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Memory Management                         |   |
|  | - Virtual memory                          |   |
|  | - Page allocation                         |   |
|  | - Slab allocator                          |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Virtual File System (VFS)                 |   |
|  | - ext4, XFS, Btrfs                        |   |
|  | - NFS, FUSE                               |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Network Stack                             |   |
|  | - TCP/IP                                  |   |
|  | - Netfilter (iptables)                    |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Device Drivers                            |   |
|  | - Block devices                           |   |
|  | - Character devices                       |   |
|  | - Network devices                         |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Architecture-Dependent Code               |   |
|  | - x86, ARM, RISC-V                        |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               HARDWARE                            |
+---------------------------------------------------+
```

### Linux Process Model

```
TASK STRUCT (Process Descriptor):

struct task_struct {
    // Process State
    volatile long state;        // TASK_RUNNING, TASK_INTERRUPTIBLE, etc.
    void *stack;                // Kernel stack
    
    // Scheduling Information
    int prio;                   // Priority
    int static_prio;            // Static priority
    int normal_prio;            // Normal priority
    unsigned int policy;        // Scheduling policy
    
    // Process Identifiers
    pid_t pid;                  // Process ID
    pid_t tgid;                 // Thread group ID
    
    // Process Relationships
    struct task_struct *parent; // Parent process
    struct list_head children;  // Child processes
    struct list_head sibling;   // Sibling processes
    
    // Memory Management
    struct mm_struct *mm;       // Memory descriptor
    
    // File System
    struct fs_struct *fs;       // File system info
    struct files_struct *files; // Open files
    
    // Signal Handling
    struct signal_struct *signal;
    
    // CPU Time
    u64 utime;                  // User time
    u64 stime;                  // System time
};

Process Creation (fork):

User space:          Kernel space:
    |                     |
    | fork()              |
    +------------------->|
                         | do_fork()
                         |   ↓
                         | copy_process()
                         |   - Allocate new task_struct
                         |   - Copy parent's context
                         |   - Allocate PID
                         |   - Copy/share memory (COW)
                         |   - Setup files, signals
                         |   ↓
                         | wake_up_new_task()
                         |   - Add to run queue
                         |   ↓
                         | Return child PID
    |<-------------------+
    |
Both processes continue...
```

### Linux Scheduler: Completely Fair Scheduler (CFS)

```
CFS OVERVIEW:

Key Idea: Give each process fair share of CPU time

Virtual Runtime (vruntime):
- Tracks how long process has run
- Weighted by priority
- Lower vruntime = higher priority to run

Data Structure: Red-Black Tree

              [vruntime=50]
             /              \
    [vruntime=30]        [vruntime=70]
       /      \              /      \
  [vr=20]  [vr=40]     [vr=60]  [vr=80]

Left-most node: Process with minimum vruntime (runs next)

ALGORITHM:

1. Select task with minimum vruntime
2. Run task for time slice
3. Update vruntime
4. Re-insert into tree
5. Repeat

vruntime calculation:
vruntime += delta_exec * (NICE_0_LOAD / task_weight)

Where:
- delta_exec = actual runtime
- task_weight = based on nice value

Nice values: -20 (highest priority) to +19 (lowest)

Example:
Task A (nice 0): Runs 10ms → vruntime += 10
Task B (nice 5): Runs 10ms → vruntime += 15 (runs less often)
Task C (nice -5): Runs 10ms → vruntime += 7 (runs more often)

LOAD BALANCING:

Across CPUs:
CPU 0: 4 tasks (high load)
CPU 1: 1 task (low load)

Periodic check:
- Calculate load per CPU
- Migrate tasks from busy to idle CPUs
- Respect cache affinity

REAL-TIME TASKS:

Linux supports POSIX real-time scheduling:
- SCHED_FIFO: First-in-first-out
- SCHED_RR: Round-robin with time slice
- SCHED_DEADLINE: Earliest deadline first

Priority:
RT tasks (0-99) > Normal tasks (100-139)
```

### Linux Memory Management

```
MEMORY ZONES:

+---------------------------+
| ZONE_DMA                  | 0-16 MB (ISA devices)
+---------------------------+
| ZONE_DMA32                | 16 MB - 4 GB (32-bit DMA)
+---------------------------+
| ZONE_NORMAL               | Direct kernel mapping
+---------------------------+
| ZONE_HIGHMEM              | > 896 MB (32-bit only)
+---------------------------+
| ZONE_MOVABLE              | For memory hotplug
+---------------------------+

PAGE ALLOCATOR:

Buddy System:
Order 0: 4 KB (1 page)
Order 1: 8 KB (2 pages)
Order 2: 16 KB (4 pages)
...
Order 10: 4 MB (1024 pages)

Example allocation (order 2 = 16 KB):

Free list:
Order 0: [empty]
Order 1: [empty]
Order 2: [empty]
Order 3: [Block A]  ← Split this

Split Block A (32 KB):
→ Two 16 KB blocks
→ Allocate one, keep one in Order 2 free list

SLAB ALLOCATOR:

For frequently used objects (inodes, dentries, etc.)

Cache: inode_cache
+---------+---------+---------+---------+
| Slab 1  | Slab 2  | Slab 3  | Slab 4  |
+---------+---------+---------+---------+
    |
    v
+----+----+----+----+----+----+----+----+
|inode|inode|inode|inode|inode|inode|inode|inode|
+----+----+----+----+----+----+----+----+
 used used free free used used free used

Benefits:
- Fast allocation (pre-allocated objects)
- Cache-friendly (objects stay in cache)
- No fragmentation (fixed-size objects)

VIRTUAL MEMORY:

4-Level Page Tables (x86-64):

Virtual Address (48 bits):
+-----+-----+-----+-----+--------+
| PGD | PUD | PMD | PTE | Offset |
+-----+-----+-----+-----+--------+
  9bit  9bit  9bit  9bit   12bit

Translation:
1. CR3 → PGD base
2. PGD[index] → PUD base
3. PUD[index] → PMD base
4. PMD[index] → PTE base
5. PTE[index] → Physical page
6. Add offset → Physical address

PAGE FAULT HANDLING:

1. Page fault exception
2. do_page_fault()
3. Check if valid address
   - Invalid → SIGSEGV
   - Valid → handle
4. Check if page present
   - Not present → load from disk
   - Present but read-only → COW
5. Allocate physical page
6. Update page table
7. Return to user space
```

### Linux File System (ext4)

```
EXT4 STRUCTURE:

Disk Layout:
+-------------+-------------+-------------+-------------+
| Boot Block  | Block Group 0| Block Group 1| ...        |
+-------------+-------------+-------------+-------------+

Block Group:
+----------------+
| Superblock     | (backup in some groups)
+----------------+
| Group Desc.    | Metadata about this group
+----------------+
| Data Block     | Bitmap of used/free blocks
| Bitmap         |
+----------------+
| Inode Bitmap   | Bitmap of used/free inodes
+----------------+
| Inode Table    | Array of inodes
+----------------+
| Data Blocks    | Actual file data
+----------------+

INODE STRUCTURE:

struct ext4_inode {
    __le16  i_mode;         // File type and permissions
    __le16  i_uid;          // Owner user ID
    __le32  i_size_lo;      // Size (lower 32 bits)
    __le32  i_atime;        // Access time
    __le32  i_ctime;        // Change time
    __le32  i_mtime;        // Modification time
    __le32  i_dtime;        // Deletion time
    __le16  i_gid;          // Group ID
    __le16  i_links_count;  // Hard links count
    __le32  i_blocks_lo;    // Blocks count
    __le32  i_flags;        // File flags
    __le32  i_block[15];    // Pointers to blocks
    ...
};

i_block[15] Layout:
[0-11]: Direct blocks (12 × 4KB = 48 KB)
[12]: Single indirect (1024 × 4KB = 4 MB)
[13]: Double indirect (1024² × 4KB = 4 GB)
[14]: Triple indirect (1024³ × 4KB = 4 TB)

EXTENTS (Improvement over blocks):

Instead of: Block 100, 101, 102, 103, ...
Store as: (Start: 100, Length: 100)

struct ext4_extent {
    __le32  ee_block;       // First logical block
    __le16  ee_len;         // Number of blocks
    __le16  ee_start_hi;    // High 16 bits of physical block
    __le32  ee_start_lo;    // Low 32 bits of physical block
};

Benefits:
- Fewer metadata entries
- Faster lookups
- Better for large files

JOURNALING:

Journal modes:
1. Journal: Log metadata + data
2. Ordered: Log metadata, data written before
3. Writeback: Log metadata only

Transaction:
Begin → [Changes] → Commit → Checkpoint

Crash recovery:
1. Read journal
2. Find uncommitted transactions → Discard
3. Find committed but not checkpointed → Replay
4. Mark journal clean
```

---

## Windows NT Architecture

### Windows NT Structure

```
+---------------------------------------------------+
|               USER MODE                           |
|                                                   |
|  +-------------------------------------------+   |
|  | System Processes                          |   |
|  | - Session Manager (smss.exe)              |   |
|  | - Client/Server Runtime (csrss.exe)       |   |
|  | - Local Security Authority (lsass.exe)    |   |
|  | - Service Control Manager (services.exe)  |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Service Processes                         |   |
|  | - Windows services                        |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | User Applications                         |   |
|  | - Win32 apps                              |   |
|  | - UWP apps                                |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Subsystem DLLs                            |   |
|  | - kernel32.dll, user32.dll, ntdll.dll     |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
         System Call Interface (ntdll.dll)
+---------------------------------------------------+
|               KERNEL MODE                         |
|                                                   |
|  +-------------------------------------------+   |
|  | Executive                                 |   |
|  | - I/O Manager                             |   |
|  | - Object Manager                          |   |
|  | - Security Reference Monitor              |   |
|  | - Process Manager                         |   |
|  | - Memory Manager                          |   |
|  | - Cache Manager                           |   |
|  | - Plug and Play Manager                   |   |
|  | - Power Manager                           |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Kernel                                    |   |
|  | - Thread scheduling                       |   |
|  | - Interrupt/exception dispatching         |   |
|  | - Synchronization                         |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Device Drivers                            |   |
|  | - File system drivers                     |   |
|  | - Hardware drivers                        |   |
|  +-------------------------------------------+   |
|                                                   |
|  +-------------------------------------------+   |
|  | Hardware Abstraction Layer (HAL)          |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               HARDWARE                            |
+---------------------------------------------------+
```

### Windows Object Manager

```
EVERYTHING IS AN OBJECT:

Files, processes, threads, semaphores, events, etc.

Object Structure:
+-----------------------+
| Object Header         |
| - Type                |
| - Name                |
| - Reference count     |
| - Handle count        |
| - Security descriptor |
+-----------------------+
| Object Body           |
| (Type-specific data)  |
+-----------------------+

Object Namespace:
Root (\)
  |
  +-- Device
  |     +-- HarddiskVolume1
  |     +-- CdRom0
  |
  +-- Driver
  |     +-- Disk
  |     +-- Null
  |
  +-- ObjectTypes
  |     +-- Type
  |     +-- Directory
  |
  +-- GLOBAL??
        +-- C: → \Device\HarddiskVolume1
        +-- D: → \Device\CdRom0

Handles:
User space uses handles (32-bit integers)
Kernel maintains handle table per process

Process Handle Table:
+--------+------------------+
| Handle | Object Pointer   |
+--------+------------------+
|   0x4  | → File Object    |
|   0x8  | → Thread Object  |
|   0xC  | → Event Object   |
+--------+------------------+
```

### Windows Scheduler

```
PRIORITY-BASED PREEMPTIVE SCHEDULING:

Priority Levels: 0-31
- 0: Zero page thread (special)
- 1-15: Dynamic (variable priority)
- 16-31: Real-time (fixed priority)

Priority Classes (User view):
Realtime: Base 24
High: Base 13
Above Normal: Base 10
Normal: Base 8
Below Normal: Base 6
Idle: Base 4

Priority Boost:
- I/O completion: +1 to +3
- Window foreground: +2
- Wait completion: varies

Example:
Thread A: Base priority 8 (Normal)
- Waiting on I/O → Priority 8
- I/O completes → Priority 11 (boost +3)
- Runs and uses quantum → Priority 10 (decay)
- Next quantum → Priority 9 (decay)
- ... → Priority 8 (back to base)

Quantum:
Client Windows: Short quantum (2 clock ticks = ~20ms)
Server Windows: Long quantum (12 clock ticks = ~120ms)

DISPATCHER:
Ready Queue per Priority Level:
Priority 31: [Thread X]
Priority 30: []
...
Priority 10: [Thread A, Thread B]
...
Priority 0: []

Algorithm:
1. Find highest non-empty queue
2. Select thread (round-robin within priority)
3. Run for quantum
4. Update priority (if dynamic)
5. Repeat

NUMA Awareness:
Prefer scheduling threads on same NUMA node
Migrate only when load imbalance significant
```

### Windows Memory Manager

```
VIRTUAL ADDRESS SPACE (64-bit):

User space:    0x000000000000 - 0x00007FFFFFFFFFFF (128 TB)
Kernel space:  0xFFFF800000000000 - 0xFFFFFFFFFFFFFFFF (128 TB)

Virtual Address Descriptor (VAD):
Tree structure describing allocated regions

Example VAD Tree:
          [0x1000-0x2000]
         /               \
[0x100-0x500]         [0x3000-0x4000]

Each VAD node:
- Start address
- End address
- Protection (RWX)
- Type (private, mapped, image)

PAGE TABLES:

4-Level Paging (x86-64):
PML4 → PDPT → PD → PT → Page

Each entry:
- Present bit
- Write bit
- User/Supervisor
- Accessed/Dirty
- Physical address

PAGE FAULT HANDLING:

Soft Fault:
Page not in working set but in memory
→ Add to working set
→ Update PTE

Hard Fault:
Page not in memory
→ Read from pagefile or mapped file
→ Allocate physical page
→ Update PTE

WORKING SET:

Each process has working set:
- Minimum size
- Maximum size
- Current size

Working Set Manager:
Periodically trims working sets
Moves pages to standby list (cache)

Page States:
Active → Modified → Standby → Free → Zeroed

MEMORY MAPPED FILES:

CreateFileMapping() + MapViewOfFile()

Multiple processes can map same file:
Process A: 0x10000 ─┐
                     ├─→ [Physical Memory] ←─ [File on Disk]
Process B: 0x20000 ─┘

Changes visible to all mappers
Lazy write-back to disk
```

### Windows Registry

```
HIERARCHICAL DATABASE:

Root Keys:
HKEY_LOCAL_MACHINE (HKLM) - System-wide settings
HKEY_CURRENT_USER (HKCU) - Per-user settings
HKEY_CLASSES_ROOT (HKCR) - File associations
HKEY_USERS (HKU) - All user profiles
HKEY_CURRENT_CONFIG (HKCC) - Hardware profile

Structure:
HKLM
  |
  +-- SOFTWARE
  |     +-- Microsoft
  |           +-- Windows
  |                 +-- CurrentVersion
  |                       +-- Run (Value: startup programs)
  |
  +-- SYSTEM
        +-- CurrentControlSet
              +-- Services
                    +-- ServiceName
                          +-- Start (Value: 2 = Automatic)

Hives (Files on Disk):
HKLM\SYSTEM    → \Windows\System32\config\SYSTEM
HKLM\SOFTWARE  → \Windows\System32\config\SOFTWARE
HKLM\SAM       → \Windows\System32\config\SAM
HKCU           → \Users\Username\NTUSER.DAT

Transaction Support:
- Atomic updates
- Logged changes
- Rollback on failure

Registry Access:
RegOpenKeyEx() → Handle
RegQueryValueEx() → Read
RegSetValueEx() → Write
RegCloseKey() → Release
```

---

## macOS and Darwin

### macOS Architecture

```
+---------------------------------------------------+
|               USER EXPERIENCE                     |
|  +-------------------------------------------+   |
|  | Aqua (GUI)                                |   |
|  | - Window Manager                          |   |
|  | - Dock, Menu Bar                          |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               APPLICATION FRAMEWORKS              |
|  +-------------------------------------------+   |
|  | Cocoa (Objective-C/Swift)                 |   |
|  | - AppKit (desktop apps)                   |   |
|  | - UIKit (iOS apps on macOS)               |   |
|  +-------------------------------------------+   |
|  | Core Services                             |   |
|  | - Core Foundation                         |   |
|  | - Core Data                               |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               CORE OS (Darwin)                    |
|  +-------------------------------------------+   |
|  | BSD Layer                                 |   |
|  | - POSIX APIs                              |   |
|  | - Network stack                           |   |
|  | - File systems                            |   |
|  +-------------------------------------------+   |
|  | XNU Kernel                                |   |
|  | - Mach (microkernel core)                 |   |
|  | - BSD (Unix functionality)                |   |
|  | - IOKit (drivers)                         |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               HARDWARE                            |
+---------------------------------------------------+
```

### XNU Kernel (Hybrid Architecture)

```
XNU = X is Not Unix

MACH MICROKERNEL:

Core functionality:
- Tasks and threads
- IPC (Mach messages)
- Virtual memory
- Scheduling

Task Structure:
+------------------+
| Task (Process)   |
+------------------+
| - Address space  |
| - Mach ports     |
| - Threads        |
+------------------+
       |
       +-- Thread 1
       +-- Thread 2
       +-- Thread 3

Mach Messages:
Port-based IPC

Port: Communication channel
+--------+     Message     +--------+
| Task A | -------------> | Task B |
+--------+     (Port)      +--------+

Message:
+------------------+
| Header           |
| - Port           |
| - Size           |
+------------------+
| Data             |
+------------------+

BSD LAYER:

Built on top of Mach:
- POSIX system calls
- Process model (fork, exec)
- Signals
- File systems (VFS)
- Network stack (TCP/IP)

Integration:
BSD Process ←→ Mach Task
BSD Thread ←→ Mach Thread

I/O KIT:

Object-oriented driver framework (C++)

Driver Hierarchy:
IOService (base class)
    |
    +-- IOBlockStorageDevice
    |      |
    |      +-- IOMediaBSDClient
    |
    +-- IONetworkController
           |
           +-- IOEthernetController

Driver Matching:
1. Device detected
2. IOKit searches for matching driver
3. Driver loads
4. Driver::probe()
5. Driver::start()
```

### macOS File System (APFS)

```
APPLE FILE SYSTEM (APFS):

Optimized for Flash/SSD

Features:
- Copy-on-write
- Space sharing
- Snapshots
- Cloning
- Encryption
- Crash protection

STRUCTURE:

Container:
+---------------------------+
| Container Superblock      |
+---------------------------+
| Checkpoint Descriptor     |
+---------------------------+
| Volumes                   |
| - Volume 1 (macOS)        |
| - Volume 2 (Data)         |
| - Volume 3 (Time Machine) |
+---------------------------+
| Extents (data blocks)     |
+---------------------------+

Space Sharing:
All volumes share same container space

Volume 1: 50 GB used
Volume 2: 30 GB used
Volume 3: 20 GB used
Total: 100 GB used, not 100 GB reserved per volume

COPY-ON-WRITE:

Original:
File A → Block 100

Copy:
cp file_a file_b

file_a → Block 100
file_b → Block 100 (same block!)

Modify file_b:
file_a → Block 100 (original)
file_b → Block 200 (new copy)

Only modified blocks duplicated

SNAPSHOTS:

Point-in-time view:
Snapshot 1 (10:00 AM): File system state
Snapshot 2 (2:00 PM): File system state

Time Machine uses snapshots:
- Frequent local snapshots
- Incremental backups
- Space-efficient

CLONING:

Instant file copy:
Original file: 1 GB
Clone: Instant (no data copied)

Only metadata duplicated
Blocks shared until modified
```

### macOS Security

```
SYSTEM INTEGRITY PROTECTION (SIP):

Protects system files even from root

Protected locations:
- /System
- /usr (except /usr/local)
- /bin, /sbin
- Preinstalled apps

Cannot modify even with sudo!

Disable only from Recovery Mode:
csrutil disable

GATEKEEPER:

Code signing verification

App Download:
Internet → App → Gatekeeper → Verify signature → Run

Developer ID:
Apps must be signed by Apple-issued certificate

Notarization:
Apps scanned by Apple before distribution

SANDBOXING:

App Sandbox:
Limits app access to resources

Example permissions:
+------------------------+
| App                    |
+------------------------+
| Allowed:               |
| - Own container        |
| - User-selected files  |
| - Network (if granted) |
+------------------------+
| Denied:                |
| - Other apps' data     |
| - System files         |
| - Camera (unless grant)|
+------------------------+

Entitlements:
com.apple.security.network.client
com.apple.security.files.user-selected.read-write

SECURE ENCLAVE:

Dedicated secure processor

Features:
- Touch ID/Face ID data
- Encryption keys
- Secure boot

Isolated from main CPU
Cannot be directly accessed
```

---

## Android Operating System

### Android Architecture

```
+---------------------------------------------------+
|               APPS LAYER                          |
|  +-------------------------------------------+   |
|  | System Apps                               |   |
|  | - Phone, Contacts, Browser                |   |
|  +-------------------------------------------+   |
|  | Third-Party Apps                          |   |
|  | - Games, Productivity, etc.               |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               JAVA API FRAMEWORK                  |
|  +-------------------------------------------+   |
|  | Activity Manager   | Content Providers    |   |
|  | Window Manager     | View System          |   |
|  | Telephony Manager  | Package Manager      |   |
|  | Location Manager   | Notification Mgr     |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               NATIVE LIBRARIES                    |
|  +-------------------------------------------+   |
|  | Android Runtime (ART)                     |   |
|  | - Core libraries                          |   |
|  | - Dalvik Executable (DEX)                 |   |
|  +-------------------------------------------+   |
|  | Native C/C++ Libraries                    |   |
|  | - libc, SSL, SQLite, OpenGL, Media        |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               HAL (Hardware Abstraction)          |
|  +-------------------------------------------+   |
|  | Camera HAL  | Audio HAL  | Sensors HAL    |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
|               LINUX KERNEL                        |
|  +-------------------------------------------+   |
|  | Binder IPC | Power Mgmt | Memory Mgmt     |   |
|  | Display    | Camera     | Audio Drivers   |   |
|  +-------------------------------------------+   |
+---------------------------------------------------+
```

### Android Process Model

```
APP ISOLATION:

Each app:
- Separate Linux user ID (UID)
- Separate process
- Separate VM instance
- Own private data directory

Example:
App A: UID 10001, Process PID 1234
App B: UID 10002, Process PID 1235
App C: UID 10003, Process PID 1236

App A cannot access App B's memory or files!

APP COMPONENTS:

1. ACTIVITY:
   Single screen with UI
   
   MainActivity → DetailActivity → ResultActivity

2. SERVICE:
   Background operation
   
   Music Player Service (plays in background)

3. BROADCAST RECEIVER:
   Responds to system-wide announcements
   
   Battery low → BroadcastReceiver → Notify user

4. CONTENT PROVIDER:
   Manages shared app data
   
   Contacts → ContentProvider → Other apps can query

PROCESS IMPORTANCE:

Hierarchy (highest to lowest):
1. Foreground Process
   - User interacting
   - Cannot be killed

2. Visible Process
   - On screen but not foreground
   - Rarely killed

3. Service Process
   - Background service running
   - Killed if memory low

4. Cached Process
   - Not currently needed
   - Killed first when memory low

Low Memory Killer (LMK):
Monitors memory
Kills processes based on importance
```

### Binder IPC

```
ANDROID'S PRIMARY IPC MECHANISM:

Client-Server model with kernel driver

Architecture:
+----------+        +----------+        +----------+
| Client   | -----> | Binder   | -----> | Server   |
| Process  |        | Driver   |        | Process  |
+----------+        +----------+        +----------+
                    (Kernel)

Example: Activity Manager

App wants to start activity:
1. App calls startActivity()
2. Request serialized
3. Sent to Binder driver
4. Driver routes to Activity Manager Service
5. AMS processes request
6. Response sent back through Binder

AIDL (Android Interface Definition Language):

Define interface:
// ICalculator.aidl
interface ICalculator {
    int add(int a, int b);
}

Generated proxy/stub:
Client → Proxy → Binder → Stub → Server

Message:
+------------------+
| Transaction Code | (which method)
| Data             | (parameters)
| Reply            | (return value)
+------------------+

PARCELING:

Serialize data for IPC:
Parcel parcel = Parcel.obtain();
parcel.writeInt(42);
parcel.writeString("Hello");

Efficient flat binary format
```

### Android Runtime (ART)

```
COMPILATION:

AOT (Ahead-of-Time) Compilation:

App Installation:
.apk → .dex bytecode → native code (during install)

Advantages:
+ Faster app startup
+ Better performance

Disadvantages:
- Longer installation time
- More storage space

JIT + AOT Hybrid (Android 7+):

Install: Keep bytecode
First run: Interpret + JIT compile hot code
Background: Profile-guided AOT compilation

Timeline:
Install → Interpret → JIT hot code → Profile → AOT compile

Balance:
- Fast installation
- Good startup time
- Optimized code for frequently used paths

MEMORY MANAGEMENT:

Dalvik/ART Heap:
+-------------------+
| Young Generation  | (new objects)
+-------------------+
| Old Generation    | (long-lived objects)
+-------------------+
| Large Objects     | (separate space)
+-------------------+

Garbage Collection:
- Concurrent mark-sweep
- Generational
- Compacting (ART)

GC Triggers:
1. Heap almost full
2. Explicit GC request
3. Allocation failure
```

### Android Power Management

```
WAKE LOCKS:

Keep device awake:
PowerManager pm = getSystemService(POWER_SERVICE);
WakeLock wl = pm.newWakeLock(PARTIAL_WAKE_LOCK, "MyWakeLock");
wl.acquire(); // Keep CPU on
// Do work
wl.release(); // Allow sleep

Types:
- PARTIAL_WAKE_LOCK: CPU on, screen can be off
- SCREEN_DIM_WAKE_LOCK: CPU + dim screen on
- SCREEN_BRIGHT_WAKE_LOCK: CPU + bright screen on
- FULL_WAKE_LOCK: CPU + screen + keyboard on

DOZE MODE:

Idle device optimization:

Timeline:
Screen off → Wait (minutes) → Doze mode

Doze restrictions:
- Network access suspended
- Wake locks ignored
- Alarms deferred
- WiFi scans disabled
- JobScheduler/SyncAdapter delayed

Maintenance windows:
Brief periods to sync/run tasks

APP STANDBY:

Per-app idle state:

App not used → Standby → Restrictions

Restrictions:
- Network access limited
- Background jobs restricted

BATTERY OPTIMIZATION:

User can exempt apps:
Settings → Battery → Battery Optimization

Exempted apps:
- No Doze restrictions
- Can use full wake locks

Guidelines:
- Release wake locks promptly
- Use JobScheduler for deferrable tasks
- Batch network requests
- Monitor battery level
```

---

## Comparative Analysis

### Kernel Architecture Comparison

```
+-------------------+-------------------+-------------------+
| Feature           | Linux             | Windows           |
+-------------------+-------------------+-------------------+
| Kernel Type       | Monolithic        | Hybrid            |
| Portability       | Excellent         | Limited           |
| Source Code       | Open Source       | Closed Source     |
| File Systems      | ext4, XFS, Btrfs  | NTFS, ReFS        |
| Package Mgmt      | Various (apt,yum) | Windows Store     |
| Shell             | bash, zsh         | PowerShell, cmd   |
| Multi-user        | Native            | Added later       |
+-------------------+-------------------+-------------------+

+-------------------+-------------------+-------------------+
| Feature           | macOS             | Android           |
+-------------------+-------------------+-------------------+
| Kernel Type       | Hybrid (XNU)      | Monolithic (Linux)|
| Portability       | Apple Hardware    | Various devices   |
| Source Code       | Partially Open    | Open (AOSP)       |
| File Systems      | APFS              | ext4, F2FS        |
| Package Mgmt      | App Store         | Play Store        |
| Shell             | zsh (default)     | Minimal (toybox)  |
| Multi-user        | Native            | Sandboxed apps    |
+-------------------+-------------------+-------------------+
```

### Process/Thread Model

```
LINUX:
- Threads are processes (clone with shared address space)
- task_struct for all
- No distinction at kernel level

WINDOWS:
- Clear process/thread separation
- Process is container
- Threads are execution units

macOS:
- Mach tasks (processes)
- Mach threads (threads)
- BSD process wrapper

ANDROID:
- Linux-based
- Each app = separate process
- Binder for IPC
```

### Scheduling Comparison

```
LINUX CFS:
Algorithm: Fair scheduling based on vruntime
Structure: Red-black tree
Priorities: Nice values (-20 to +19)
Context: General purpose

WINDOWS:
Algorithm: Priority-based preemptive
Structure: Priority queues (32 levels)
Priorities: Base + dynamic boost
Context: Desktop/server

macOS:
Algorithm: Mach scheduling (priority)
Structure: Priority queues
Priorities: 0-127 (including realtime)
Context: Desktop focused

ANDROID:
Algorithm: CFS (Linux-based)
+ OOM killer adjustments
+ Cgroup resource limits
Context: Mobile focused
```

### Memory Management

```
VIRTUAL MEMORY:

Linux:
- 4-level page tables
- Buddy allocator + Slab
- OOM killer
- Swap

Windows:
- 4-level page tables
- Working sets
- Modified page writer
- Pagefile

macOS:
- 4-level page tables
- VM compression
- Memory pressure events
- Swap

Android:
- Linux-based
- Low Memory Killer (LMK)
- zRAM (compressed swap)
- Aggressive app killing

OPTIMIZATION:

Linux: Transparent Huge Pages, NUMA
Windows: SuperFetch, ReadyBoost
macOS: Memory compression
Android: zRAM, LMK
```

### Security Model

```
+------------------+------------------+------------------+
| Feature          | Linux            | Windows          |
+------------------+------------------+------------------+
| User/Permission  | DAC (rwx)        | ACL              |
| Mandatory Access | SELinux/AppArmor | Mandatory Level  |
| Encryption       | LUKS, dm-crypt   | BitLocker        |
| Firewall         | iptables/nftables| Windows Firewall |
| Sandboxing       | Containers, VMs  | App Container    |
+------------------+------------------+------------------+

+------------------+------------------+------------------+
| Feature          | macOS            | Android          |
+------------------+------------------+------------------+
| User/Permission  | POSIX + ACL      | UID per app      |
| Mandatory Access | SIP              | SELinux          |
| Encryption       | FileVault (APFS) | File-based       |
| Firewall         | pf (BSD)         | iptables         |
| Sandboxing       | App Sandbox      | App isolation    |
+------------------+------------------+------------------+
```

### File System Performance

```
BENCHMARK (Relative performance):

Sequential Read:
ext4:   ████████████ 100%
NTFS:   ██████████   85%
APFS:   ███████████  95%
F2FS:   █████████████ 105% (SSD optimized)

Random Read:
ext4:   ████████     80%
NTFS:   ██████████   100%
APFS:   ███████████  110%
F2FS:   ████████████ 120%

Metadata Operations:
ext4:   ████████     80%
NTFS:   ██████       60%
APFS:   ████████████ 120% (Copy-on-write advantage)
F2FS:   ██████████   100%

Features:
ext4:   Mature, stable, journaling
NTFS:   Compression, encryption, journaling
APFS:   Copy-on-write, snapshots, cloning
F2FS:   Flash-optimized, wear leveling
```

### Design Philosophy

```
LINUX:
Philosophy: "Everything is a file"
Focus: Flexibility, customization
Strength: Server environments
Development: Community-driven

WINDOWS:
Philosophy: "Backwards compatibility"
Focus: User-friendly, enterprise
Strength: Desktop applications, enterprise
Development: Microsoft-driven

macOS:
Philosophy: "It just works"
Focus: User experience, integration
Strength: Creative professionals
Development: Apple-controlled

ANDROID:
Philosophy: "Open but controlled"
Focus: Mobile, touch, power efficiency
Strength: Mobile devices, IoT
Development: Google-led, OEM customized
```

---

## Summary

### Key Takeaways

**Linux:**
- Monolithic kernel, highly customizable
- CFS for fair scheduling
- Powerful for servers and embedded
- Open source, community-driven

**Windows:**
- Hybrid kernel, backward compatibility focus
- Priority-based scheduling
- Dominant in desktop/enterprise
- Closed source, Microsoft-developed

**macOS:**
- Hybrid XNU kernel (Mach + BSD)
- Premium user experience
- Tightly integrated hardware/software
- Partially open (Darwin)

**Android:**
- Linux kernel + custom userspace
- App isolation via UID
- Binder IPC, ART runtime
- Optimized for mobile/power

Each OS makes different trade-offs based on target use case!

---

**Next Topics:**
- System Programming and APIs
- Performance Tuning
- Debugging Techniques

