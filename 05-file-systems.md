# Operating Systems - File Systems

## Table of Contents
1. [File Concept](#file-concept)
2. [File Operations](#file-operations)
3. [Directory Structure](#directory-structure)
4. [File System Implementation](#file-system-implementation)
5. [Allocation Methods](#allocation-methods)
6. [Free Space Management](#free-space-management)
7. [Directory Implementation](#directory-implementation)
8. [File System Performance](#file-system-performance)
9. [Recovery and Consistency](#recovery-and-consistency)

---

## File Concept

A **file** is a named collection of related information stored on secondary storage.

### File Attributes

```
+--------------------------------------------------+
| FILE ATTRIBUTES (Metadata)                       |
+--------------------------------------------------+
| Name:             document.txt                   |
| Identifier:       inode #45678 (unique ID)       |
| Type:             Text file (.txt)               |
| Location:         /home/user/docs/               |
| Size:             2048 bytes                     |
| Protection:       rw-r--r-- (644)                |
| Time/Date:        Created: 2024-01-15 10:30      |
|                   Modified: 2024-01-20 14:45     |
|                   Accessed: 2024-01-21 09:15     |
| Owner:            user_id=1000, group_id=1000    |
+--------------------------------------------------+
```

### File Types

```
REGULAR FILES:
+----------------+
| Text files     | ASCII, UTF-8 text
| Binary files   | Executable, images, archives
| Data files     | Database, structured data
+----------------+

DIRECTORIES:
+----------------+
| Special files  | Contains file entries
| (Folders)      | Organize file system
+----------------+

SPECIAL FILES:
+----------------+
| Character      | Terminal, serial port (/dev/tty)
| device files   | 
+----------------+
| Block device   | Disk, USB (/dev/sda)
| files          |
+----------------+
| Pipes          | IPC mechanism
| (FIFO)         |
+----------------+
| Sockets        | Network communication
+----------------+
| Symbolic links | Pointer to another file
+----------------+
```

### File Structure

```
1. UNSTRUCTURED (Byte Sequence):
+---+---+---+---+---+---+---+---+
| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | ...
+---+---+---+---+---+---+---+---+

Applications impose structure
OS sees as stream of bytes
Most flexible (UNIX, Windows)

2. SIMPLE RECORD STRUCTURE:
+--------+--------+--------+
|Record 1|Record 2|Record 3|
+--------+--------+--------+
| Name   | Name   | Name   |
| Age    | Age    | Age    |
| ID     | ID     | ID     |
+--------+--------+--------+

Fixed or variable length records
Used in older systems (mainframes)

3. COMPLEX STRUCTURE:
+-------------------------+
| Document with:          |
| - Formatted pages       |
| - Index                 |
| - Metadata              |
+-------------------------+

OS understands file structure
Less flexible but feature-rich
```

---

## File Operations

### Basic Operations

```
1. CREATE
   +----------------+
   | Allocate space |
   | Create entry   | → New file
   | in directory   |
   +----------------+

2. OPEN
   File Name → Search directory → Get metadata
                                → File descriptor/handle
   
   File Descriptor Table:
   +----+----------------+
   | FD |  File Pointer  |
   +----+----------------+
   | 3  | → file1.txt    |
   | 4  | → file2.dat    |
   | 5  | → file3.log    |
   +----+----------------+

3. READ
   +--------+         +--------+
   | File   | ------> | Buffer |
   | (Disk) |  Read   | (Memory|
   +--------+         +--------+
   
   read(fd, buffer, count)

4. WRITE
   +--------+         +--------+
   | Buffer | ------> | File   |
   | (Memory)  Write  | (Disk) |
   +--------+         +--------+
   
   write(fd, buffer, count)

5. SEEK
   Change file pointer position
   +---+---+---+---+---+---+
   |   |   |   | ^ |   |   |
   +---+---+---+---+---+---+
               File pointer
               
   lseek(fd, offset, whence)

6. DELETE
   +----------------+
   | Release space  |
   | Remove entry   | → File gone
   | from directory |
   +----------------+

7. TRUNCATE
   +---+---+---+---+---+
   |   |   |   |   |   | ----+
   +---+---+---+---+---+     |
                             | Truncate
   +---+---+---+             |
   |   |   |   | <-----------+
   +---+---+---+
   
   ftruncate(fd, length)

8. CLOSE
   Release file descriptor
   Flush buffers to disk
   Update metadata
```

### File Descriptor and File Table

```
PROCESS A                    PROCESS B
+-----------+                +-----------+
| FD Table  |                | FD Table  |
+-----------+                +-----------+
| 0: stdin  |                | 0: stdin  |
| 1: stdout |                | 1: stdout |
| 2: stderr |                | 2: stderr |
| 3: -------|--+             | 3: -------|--+
| 4: -------|--|--+          +-----------+  |
+-----------+  |  |                         |
               |  |                         |
               v  v                         v
         +-------------------+    +-------------------+
         | System-Wide       |    | System-Wide       |
         | Open File Table   |    | Open File Table   |
         +-------------------+    +-------------------+
         | - File position   |    | - File position   |
         | - Access mode     |    | - Access mode     |
         | - Reference count |    | - Reference count |
         | - inode pointer --|--+ | - inode pointer --|--+
         +-------------------+  |  +-------------------+  |
                                |                         |
                                v                         v
                          +-------------+           +-------------+
                          | inode for   |           | inode for   |
                          | file1.txt   |           | file2.txt   |
                          +-------------+           +-------------+
                          | File attrs  |           | File attrs  |
                          | Data blocks |           | Data blocks |
                          +-------------+           +-------------+

Multiple processes can open same file
Each has its own file position
```

---

## Directory Structure

### Single-Level Directory

```
ROOT DIRECTORY:
+--------+--------+--------+--------+--------+
| file1  | file2  | file3  | file4  | file5  |
+--------+--------+--------+--------+--------+

All files in one directory

Advantages:
+ Simple implementation
+ Fast lookup

Disadvantages:
- Naming collisions
- No organization
- Not scalable

Used in: Early systems, simple embedded systems
```

### Two-Level Directory

```
ROOT:
+--------+--------+--------+
| User A | User B | User C |
+--------+--------+--------+
    |        |        |
    v        v        v
+------+ +------+ +------+
|file1 | |file1 | |file1 | Different users can have
|file2 | |file2 | |file2 | same filename
|file3 | |file3 | |file3 |
+------+ +------+ +------+

Advantages:
+ User isolation
+ Same names for different users

Disadvantages:
- No grouping within user
- Limited structure

Path: /userA/file1
```

### Tree-Structured Directory

```
ROOT (/)
  |
  +-- home/
  |     |
  |     +-- user1/
  |     |    |
  |     |    +-- documents/
  |     |    |     |
  |     |    |     +-- report.txt
  |     |    |     +-- notes.txt
  |     |    |
  |     |    +-- downloads/
  |     |         +-- file.zip
  |     |
  |     +-- user2/
  |          +-- data.csv
  |
  +-- etc/
  |     |
  |     +-- config.conf
  |
  +-- var/
        |
        +-- log/
             +-- system.log

Absolute Path: /home/user1/documents/report.txt
Relative Path: documents/report.txt (from /home/user1/)

Advantages:
+ Hierarchical organization
+ Efficient searching
+ Flexible grouping

Current working directory concept:
User at /home/user1/ can use relative paths
```

### Acyclic Graph Directory

Allow sharing of files/directories (links).

```
ROOT
  |
  +-- home/
  |     |
  |     +-- alice/
  |     |    |
  |     |    +-- project/
  |     |         |
  |     |         +-- shared.txt
  |     |
  |     +-- bob/
  |          |
  |          +-- link_to_shared -> /home/alice/project/shared.txt
  |
  
Two types of links:

HARD LINK:
  Multiple directory entries point to same inode
  
  alice/shared.txt ----+
                       |---> inode #1234 (link count=2)
  bob/shared.txt  -----+
  
  Deleting one doesn't delete file (until count=0)
  Cannot span file systems
  Cannot link directories (prevents cycles)

SYMBOLIC LINK (Soft Link):
  Directory entry contains path to target
  
  bob/link_to_shared --> Contains: "/home/alice/project/shared.txt"
                     |
                     +----> resolve path --> inode #1234
  
  If target deleted, link becomes dangling
  Can span file systems
  Can link directories
  Slower (extra lookup)
```

### General Graph Directory

Allow cycles (created by links to directories).

```
Problem: Cycles

ROOT
  |
  +-- dir1/
       |
       +-- dir2/
       |    |
       |    +-- link_to_dir1 -> /dir1/
       |
       +-- file.txt

Traversing:
/dir1/dir2/link_to_dir1/dir2/link_to_dir1/... (infinite)

Solutions:
1. Prohibit directory links (most systems)
2. Garbage collection
3. Limit traversal depth
4. Mark visited directories

Most modern systems:
- Allow symbolic links to directories
- Use cycle detection algorithms
```

---

## File System Implementation

### Layered File System

```
+-----------------------------------------------+
| User Programs                                 |
+-----------------------------------------------+
| Logical File System                           |
| - Manages metadata (FCB, inodes)              |
| - Directory management                        |
| - Protection                                  |
+-----------------------------------------------+
| File Organization Module                      |
| - Logical blocks to physical blocks           |
| - Free space management                       |
+-----------------------------------------------+
| Basic File System                             |
| - Generic commands to device driver           |
| - Buffer/cache management                     |
+-----------------------------------------------+
| I/O Control (Device Drivers)                  |
| - Interrupt handlers                          |
| - Low-level device access                     |
+-----------------------------------------------+
| Hardware (Disks, Controllers)                 |
+-----------------------------------------------+
```

### On-Disk Structures

```
DISK LAYOUT:

+------------------+ 0
| Boot Block       | (Boot loader)
+------------------+
| Superblock       | (File system metadata)
|                  | - Block size
|                  | - Number of blocks
|                  | - Number of inodes
|                  | - Free block info
+------------------+
| Inode Table      | (File metadata)
|                  | - inode 0
|                  | - inode 1
|                  | - ...
|                  | - inode N
+------------------+
| Data Blocks      | (File contents)
|                  |
|                  | (Directories, regular files)
|                  |
|                  |
+------------------+ End
```

### File Control Block (FCB) / Inode

```
UNIX INODE STRUCTURE:

+----------------------------------+
| File mode (type & permissions)   | 16 bits
+----------------------------------+
| Link count                       | Number of hard links
+----------------------------------+
| Owner UID                        | User ID
+----------------------------------+
| Group GID                        | Group ID
+----------------------------------+
| File size                        | In bytes
+----------------------------------+
| Timestamps                       |
| - Access time (atime)            |
| - Modification time (mtime)      |
| - Change time (ctime)            |
+----------------------------------+
| Direct pointers (12)             | → Data blocks
| [0]  → Block 1000                |
| [1]  → Block 1001                |
| ...                              |
| [11] → Block 1011                |
+----------------------------------+
| Single indirect pointer          | → Block of pointers
| → Block 2000                     |   +---+---+---+
|   [0][1][2]... (256 pointers)    |   | → | → | → |
|                                  |   +---+---+---+
+----------------------------------+
| Double indirect pointer          | → Indirect block
| → Block 3000                     |   of indirect blocks
|   [0] → Block                    |
|     [0][1][2]... (256)           |
|   [1] → Block                    |
|     [0][1][2]... (256)           |
+----------------------------------+
| Triple indirect pointer          | 3 levels of indirection
+----------------------------------+

Block size: 4 KB
Pointer size: 4 bytes
Pointers per block: 4096/4 = 1024

Maximum file size:
Direct: 12 × 4KB = 48 KB
Single indirect: 1024 × 4KB = 4 MB
Double indirect: 1024 × 1024 × 4KB = 4 GB
Triple indirect: 1024 × 1024 × 1024 × 4KB = 4 TB
Total: ~4 TB
```

---

## Allocation Methods

### 1. Contiguous Allocation

Each file occupies contiguous blocks on disk.

```
DISK:
+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|  OS |file1|file1|file1|file2|file2|file3|file3|file3|
+-----+-----+-----+-----+-----+-----+-----+-----+-----+
   0     1     2     3     4     5     6     7     8

Directory:
+------+-------+--------+
| Name | Start | Length |
+------+-------+--------+
|file1 |   1   |   3    |
|file2 |   4   |   2    |
|file3 |   6   |   3    |
+------+-------+--------+

Accessing file1, block 2:
Address = Start + Block = 1 + 2 = 3

Advantages:
+ Simple implementation
+ Fast sequential access
+ Fast random access (simple calculation)
+ Minimal seek time

Disadvantages:
- External fragmentation
- File size must be known in advance
- Difficult to grow files

After deleting file2:
+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|  OS |file1|file1|file1| HOLE|HOLE|file3|file3|file3|
+-----+-----+-----+-----+-----+-----+-----+-----+-----+

Need compaction (expensive)
```

### 2. Linked Allocation

Each file is a linked list of disk blocks.

```
DISK BLOCKS:

Block 1:     Block 5:     Block 9:     Block 3:
+------+     +------+     +------+     +------+
| Data |     | Data |     | Data |     | Data |
| Next:| --> | Next:| --> | Next:| --> | Next:|
|  5   |     |  9   |     |  3   |     | NULL |
+------+     +------+     +------+     +------+
  file1       file1        file1        file1

Directory:
+------+-------+--------+
| Name | Start | End    |
+------+-------+--------+
|file1 |   1   |   3    |
+------+-------+--------+

Advantages:
+ No external fragmentation
+ Files can grow easily
+ No need to know size in advance

Disadvantages:
- Sequential access only (slow random access)
- Overhead of pointers
- Reliability (broken link = lost data)

Random access to block N:
Must traverse N blocks from start
```

### 3. Indexed Allocation

Each file has an index block containing pointers to data blocks.

```
INDEX BLOCK:
+--------+
|   0    | → Data Block 4
|   1    | → Data Block 7
|   2    | → Data Block 2
|   3    | → Data Block 10
|  ...   |
| NULL   |
| NULL   |
+--------+
    ↑
    |
Directory points to index block

Directory:
+------+-------------+
| Name | Index Block |
+------+-------------+
|file1 |      1      |
+------+-------------+

DISK:
+------+------+------+------+------+------+------+------+
|Index |      | Data | Data |      | Data |      | Data |
|Block | ...  | Blk 2| Blk 4| ...  | Blk 7| ...  |Blk 10|
+------+------+------+------+------+------+------+------+
   1                                                     

Advantages:
+ Fast random access
+ No external fragmentation
+ Dynamic file growth

Disadvantages:
- Overhead of index block
- Size limited by index block

Variations:

LINKED SCHEME:
Index block has pointer to next index block
+--------+     +--------+
|   0    | --> |  256   | --> ...
|  ...   |     |  ...   |
|  255   |     |  511   |
| Next --|-+   | Next --|
+--------+ |   +--------+
           |
           +-->

MULTILEVEL INDEX:
Like multilevel page tables
+--------+
| First  | → Points to index blocks
| Level  |   +--------+
| Index  |   | Second | → Points to data
+--------+   | Level  |   blocks
             +--------+

COMBINED SCHEME (UNIX):
Direct + Indirect (see inode structure above)
```

---

## Free Space Management

### 1. Bit Vector (Bitmap)

One bit per block (0=free, 1=allocated).

```
BITMAP:
Block: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
Bit:   1  1  1  1  0  0  1  1  1  0  0  0  1  1  1  0
       ↑                                                ↑
    Allocated                                        Free

Disk:
+-----+-----+-----+-----+-----+-----+-----+-----+-----+
|  OS |file1|file1|file1| FREE| FREE|file2|file2|file2|
+-----+-----+-----+-----+-----+-----+-----+-----+-----+
   0     1     2     3     4     5     6     7     8

Finding first free block:
Scan bitmap for first 0
Block 4 is free

Advantages:
+ Simple and efficient
+ Easy to find contiguous blocks
+ Compact representation

Disadvantages:
- Requires keeping entire bitmap in memory
  (1 GB disk, 4KB blocks = 262,144 blocks = 32 KB bitmap)
```

### 2. Linked List

Link free blocks together.

```
FREE LIST HEAD → Block 4
                    ↓
Block 4:         Block 5:         Block 9:
+------+         +------+         +------+
| Next:| ------> | Next:| ------> | Next:| ------> NULL
|  5   |         |  9   |         | NULL |
+------+         +------+         +------+

Advantages:
+ No wasted space
+ Easy to allocate single block

Disadvantages:
- Difficult to find contiguous blocks
- Traversal overhead
- Not efficient for allocation of multiple blocks
```

### 3. Grouping

Store addresses of free blocks in first free block.

```
FREE BLOCK LIST HEAD → Block 100

Block 100:
+--------+
|  101   | → Free block addresses
|  102   |
|  105   |
|  ...   |
|  200   | → Pointer to next group block
+--------+
              ↓
Block 200:
+--------+
|  201   | → More free block addresses
|  205   |
|  ...   |
|  NULL  | → Last group
+--------+

Advantages:
+ Can quickly find large number of free blocks
+ Better than simple linked list

Disadvantages:
- More complex implementation
```

### 4. Counting

Store (start block, count) for contiguous free blocks.

```
FREE SPACE LIST:
+-------+-------+
| Start | Count |
+-------+-------+
|   4   |   2   | → Blocks 4, 5 are free
|   9   |   3   | → Blocks 9, 10, 11 are free
|  15   |   1   | → Block 15 is free
+-------+-------+

Advantages:
+ Compact for contiguous free space
+ Works well with contiguous allocation

Disadvantages:
- Fragmentation reduces efficiency
```

---

## Directory Implementation

### 1. Linear List

Simple list of (file name, inode pointer) pairs.

```
DIRECTORY:
+----------------+--------+
| File Name      | Inode# |
+----------------+--------+
| file1.txt      | 1234   |
| file2.dat      | 1235   |
| document.pdf   | 1236   |
| image.jpg      | 1237   |
| ...            | ...    |
+----------------+--------+

Searching for "document.pdf":
Linear search through list
O(n) time complexity

Advantages:
+ Simple to implement
+ Easy to add/remove entries

Disadvantages:
- Slow search (linear time)
- Inefficient for large directories
```

### 2. Hash Table

Hash file name to get location.

```
HASH FUNCTION:
hash("file1.txt") = 0
hash("file2.dat") = 2
hash("file3.jpg") = 0  (collision!)

HASH TABLE:
+---+------------------+
| 0 | file1.txt → 1234 | → file3.jpg → 1237 (collision chain)
+---+------------------+
| 1 | (empty)          |
+---+------------------+
| 2 | file2.dat → 1235 |
+---+------------------+
| 3 | (empty)          |
+---+------------------+

Advantages:
+ Fast lookup (O(1) average)
+ Efficient for large directories

Disadvantages:
- Fixed size (or need rehashing)
- Collisions
- Cannot efficiently list in sorted order
```

### 3. B-Tree / B+ Tree

Balanced tree structure for directories.

```
B+ TREE DIRECTORY:

                [  m  ]
                /      \
               /        \
         [d,g,j]      [p,s,v]
         / | | \      / | | \
        /  | |  \    /  | |  \
    [a,b] [d,e] [g,h] [j,k] [p,q] [s,t] [v,w]
      ↓     ↓     ↓     ↓     ↓     ↓     ↓
    Inodes                                 

Advantages:
+ Fast search (O(log n))
+ Supports range queries
+ Efficient insertion/deletion
+ Scalable to very large directories

Disadvantages:
- More complex implementation
- More overhead for small directories

Used in: NTFS, HFS+, ext4 (for large directories)
```

---

## File System Performance

### Caching

```
FILE SYSTEM CACHE ARCHITECTURE:

User Process
     |
     | read()
     v
+--------------------+
| Buffer Cache       |
| (Page Cache)       |
|                    |
| +------+  +------+ |
| |Block1|  |Block2| | ← In memory (fast)
| +------+  +------+ |
+--------------------+
     | Cache miss
     v
+--------------------+
| Disk I/O           |
|                    |
| [===============]  | ← On disk (slow)
+--------------------+

Cache Hit:
User → Cache → Return data (fast, ~100 ns)

Cache Miss:
User → Cache → Disk → Cache → Return data (slow, ~10 ms)

Replacement Policies:
- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- Clock algorithm

Write Strategies:
1. Write-Through: Write to cache and disk immediately
   + Data consistency
   - Slower writes

2. Write-Back: Write to cache, sync to disk later
   + Faster writes
   - Risk of data loss on crash
```

### Read-Ahead (Prefetching)

```
Sequential Access Detection:

User reads:    Block 100
Detect pattern → Prefetch blocks 101, 102, 103

Timeline:
+------+------+------+------+
| Read | Read | Read | Read |
| 100  | 101  | 102  | 103  |
+------+------+------+------+
  ↓      ↑      ↑      ↑
  |      Already in cache!
  Actual request

Advantages:
+ Improves sequential read performance
+ Utilizes disk sequential speed
+ Reduces I/O wait time

Implementation:
Detect sequential pattern (2-3 sequential accesses)
Prefetch next N blocks
Evict prefetched blocks if not used (avoid pollution)
```

### Disk Scheduling

```
REQUEST QUEUE:
Cylinder #: 98, 183, 37, 122, 14, 124, 65, 67
Current: 53

FCFS (First-Come-First-Served):
53 → 98 → 183 → 37 → 122 → 14 → 124 → 65 → 67
Total head movement: 45+85+146+85+108+110+59+2 = 640 cylinders

SSTF (Shortest Seek Time First):
53 → 65 → 67 → 37 → 14 → 98 → 122 → 124 → 183
Total head movement: 12+2+30+23+84+24+2+59 = 236 cylinders

SCAN (Elevator Algorithm):
53 → 37 → 14 → 0 → 65 → 67 → 98 → 122 → 124 → 183
     ←←←←←←   →→→→→→→→→→→→→→→→→→→→→→→→→
Total head movement: 16+23+14+65+2+31+24+2+59 = 236 cylinders

Disk arm moves in one direction, servicing requests,
then reverses direction (like elevator)
```

---

## Recovery and Consistency

### File System Consistency

```
CONSISTENCY CHECKING (fsck, chkdsk):

1. Block Consistency:
   Count block references:
   - In files (via inodes)
   - In free list
   
   Each block should be in exactly one list
   
   +-------+-------+
   | File  | Free  | Status
   +-------+-------+-------
   |   1   |   0   | OK (in use)
   |   0   |   1   | OK (free)
   |   0   |   0   | ERROR: Lost block
   |   1   |   1   | ERROR: Duplicate (serious!)
   +-------+-------+

2. Inode Consistency:
   - Check inode link count vs. actual directory entries
   - Verify all inodes are either allocated or free
   
3. Directory Consistency:
   - Check directory structure
   - Verify parent links (..)
   - Detect cycles
```

### Journaling File Systems

Log-based recovery for crash consistency.

```
JOURNALING:

Without Journal:        With Journal:
                        +----------+
User: Write data        | Journal  |
  ↓                     | (Log)    |
Update structures       +----------+
  ↓                          ↓
                        1. Write intent to journal
                        2. Commit journal entry
                        3. Perform actual operation
                        4. Update structures
                        5. Clear journal entry

CRASH SCENARIO:

Without Journal:
+--------+--------+--------+
| Update | Update | CRASH! |
| inode  | bitmap |        |
+--------+--------+--------+
         ↑
    Inconsistent state!

With Journal:
+--------+--------+--------+--------+
| Log    | Commit | Update | CRASH! |
| Intent | Entry  | Struct |        |
+--------+--------+--------+--------+
             ↑
        On reboot: Replay journal
        System recovers automatically
```

### Types of Journaling

```
1. METADATA JOURNALING:
   Only log metadata changes
   
   Write: Data → Disk (no log)
          Metadata → Journal → Disk
   
   Faster, but data may be lost

2. FULL JOURNALING (DATA + METADATA):
   Log everything
   
   Write: Data → Journal
          Metadata → Journal
          Then: Journal → Disk
   
   Slower, but safer

3. ORDERED JOURNALING:
   Write data first, then journal metadata
   
   Write: Data → Disk
          Wait for data commit
          Metadata → Journal → Disk
   
   Good compromise (most common)

JOURNAL STRUCTURE:

+----------+----------+----------+----------+
| Txn      | Metadata | Metadata | Txn      |
| Begin    | Update 1 | Update 2 | Commit   |
+----------+----------+----------+----------+

Transaction:
- Atomic unit of updates
- Either all or nothing
- Commit record indicates completion
```

### Snapshots

Point-in-time copy of file system.

```
COPY-ON-WRITE SNAPSHOTS:

Original:               After Snapshot:
+-------+               +-------+
| Block |               | Block | (Original)
|   A   |               |   A   |
+-------+               +-------+
                            ↑
                            | Both point to same block
                            |
Snapshot created ───────────+
                            |
User modifies block:        |
                            v
                        +-------+     +-------+
                        | Block |     | Block |
                        |   A'  |     |   A   |
                        +-------+     +-------+
                        ↑             ↑
                        |             |
                    Current       Snapshot
                   (new copy)     (original)

Only modified blocks are duplicated
Efficient: No full copy needed

Uses:
- Backup without downtime
- Quick recovery
- Testing (revert to snapshot)

Examples: ZFS, Btrfs, APFS, LVM snapshots
```

---

## Modern File Systems

### ext4 (Linux)

```
Features:
- Journaling
- Extents (contiguous blocks)
- Delayed allocation
- Multiblock allocation
- Fast fsck
- Online defragmentation

Extent:
Instead of: Block 100, 101, 102, 103, 104
Store as: (Start: 100, Length: 5)

+--------+---------------+
| Start  | Length        |
+--------+---------------+
| 100    | 5             | → Blocks 100-104
| 200    | 10            | → Blocks 200-209
+--------+---------------+

Reduces metadata overhead for large files
```

### NTFS (Windows)

```
Features:
- Everything is a file (including metadata)
- Master File Table (MFT)
- Journaling
- Compression
- Encryption (EFS)
- Access Control Lists (ACL)
- Alternate Data Streams

MFT:
Record 0: MFT itself
Record 1: MFT mirror (backup)
Record 2: Log file (journal)
Record 3: Volume
...
Record N: User file

Each MFT record describes a file
```

### ZFS (Solaris, FreeBSD)

```
Features:
- Copy-on-write
- Built-in RAID (no separate controller)
- Compression
- Deduplication
- Snapshots
- Data integrity (checksums)
- Pooled storage

Storage Pool:
+-------+-------+-------+
| Disk1 | Disk2 | Disk3 |
+-------+-------+-------+
          ↓
    +-------------+
    | Storage Pool|
    +-------------+
          ↓
+-------------+-------------+
| Dataset 1   | Dataset 2   |
+-------------+-------------+

Checksums on all data:
Data → Checksum stored in parent block
On read: Verify checksum
If corrupt: Use redundancy to repair
```

---

## Summary

- **Files**: Named collections with attributes (metadata)
- **Operations**: Create, open, read, write, seek, close, delete
- **Directories**: Organize files hierarchically
- **Allocation Methods**:
  - Contiguous: Fast but fragmentation
  - Linked: Flexible but slow random access
  - Indexed: Fast random access, used most commonly
- **Free Space**: Bitmap (most common), linked list, grouping, counting
- **Performance**: Caching, prefetching, disk scheduling
- **Consistency**: fsck, journaling, snapshots
- **Modern FS**: ext4, NTFS, ZFS, Btrfs with advanced features

File systems are critical for persistent storage and continue to evolve with new storage technologies (SSDs, NVMe).

---

**Next Topics:**
- Synchronization and Deadlocks
- I/O Systems
- Security and Protection

