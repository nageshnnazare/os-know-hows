# Operating Systems - Introduction and Fundamentals

## Table of Contents
1. [What is an Operating System?](#what-is-an-operating-system)
2. [Goals and Functions](#goals-and-functions)
3. [Types of Operating Systems](#types-of-operating-systems)
4. [Operating System Structure](#operating-system-structure)
5. [System Calls](#system-calls)
6. [Operating System Services](#operating-system-services)

---

## What is an Operating System?

An **Operating System (OS)** is system software that acts as an intermediary between computer hardware and the computer user. It manages hardware resources and provides services for application software.

### ASCII Diagram: OS Position in Computer System

```
+----------------------------------------------------------+
|                     USER APPLICATIONS                    |
|    (Web Browser, Text Editor, Games, Database, etc.)     |
+----------------------------------------------------------+
|                   APPLICATION PROGRAMS                   |
|           (Compilers, Assemblers, Text Editors)          |
+----------------------------------------------------------+
|                    OPERATING SYSTEM                      |
|  +----------------------------------------------------+  |
|  | System Calls Interface                             |  |
|  +----------------------------------------------------+  |
|  | Kernel                                             |  |
|  | - Process Management  - Memory Management          |  |
|  | - File System        - I/O Management              |  |
|  | - Security           - Networking                  |  |
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
|                    COMPUTER HARDWARE                     |
|    CPU  |  Memory  |  Disks  |  I/O Devices  |  etc.     |
+----------------------------------------------------------+
```

---

## Goals and Functions

### Primary Goals

1. **Convenience**: Make the computer system convenient to use
2. **Efficiency**: Use hardware resources efficiently
3. **Ability to Evolve**: Permit effective development, testing, and introduction of new system functions

### Core Functions

#### 1. Resource Management
- **CPU Management**: Allocate processor time to processes
- **Memory Management**: Manage RAM allocation
- **Device Management**: Control I/O devices
- **File Management**: Organize and access files

#### 2. Process Management
- Process creation and deletion
- Process scheduling
- Process synchronization
- Process communication
- Deadlock handling

#### 3. Memory Management
- Keep track of memory usage
- Allocate and deallocate memory
- Decide which processes to load into memory

#### 4. File System Management
- File creation and deletion
- Directory creation and deletion
- Support for file manipulation
- Mapping files to secondary storage
- Backup files

#### 5. I/O System Management
- Memory management for I/O (buffering, caching, spooling)
- General device-driver interface
- Drivers for specific hardware devices

---

## Types of Operating Systems

### 1. Batch Operating Systems

**Characteristics:**
- Jobs are batched together and processed sequentially
- No direct interaction between user and computer
- Used in mainframe systems

```
Job Queue:
+-------+     +-------+     +-------+     +-------+
| Job 1 | --> | Job 2 | --> | Job 3 | --> | Job 4 |
+-------+     +-------+     +-------+     +-------+
    |
    v
+------------------+
| Batch Processor  |
+------------------+
    |
    v
+------------------+
|  Output Queue    |
+------------------+
```

**Advantages:**
- Efficient processing of large volumes of data
- Reduced idle time

**Disadvantages:**
- Lack of user interaction
- Difficult to debug

### 2. Time-Sharing Operating Systems (Multitasking)

**Characteristics:**
- CPU time is shared among multiple users/processes
- Each user gets a small time slice (quantum)
- Creates illusion of dedicated system for each user

```
Time Quantum = 100ms

Time:  0      100    200    300    400    500    600
       |------|------|------|------|------|------|
CPU:   | P1   | P2   | P3   | P1   | P2   | P3   |
       |------|------|------|------|------|------|

Legend: P1, P2, P3 = Different Processes
```

**Examples:** UNIX, Linux, Windows

**Advantages:**
- Quick response time
- Reduces CPU idle time
- Multiple users can work simultaneously

**Disadvantages:**
- Security and integrity issues
- Higher overhead

### 3. Real-Time Operating Systems (RTOS)

**Characteristics:**
- Time constraints are critical
- Must respond to inputs within guaranteed time limits
- Used in time-critical systems

**Types:**

**a) Hard Real-Time Systems**
- Strict time constraints
- Missing deadline is system failure
- Examples: Air traffic control, Medical systems, Nuclear reactors

**b) Soft Real-Time Systems**
- Less strict time constraints
- Missing occasional deadline is tolerable
- Examples: Multimedia systems, Video streaming

```
Hard Real-Time:
Event -----> |Response| <-- Must complete within deadline
             +---------+
             | Process |
             +---------+
                 |
                 v
            [DEADLINE] <-- MUST meet this
                 |
                 X (Failure if missed)

Soft Real-Time:
Event -----> |Response| <-- Should complete soon
             +---------+
             | Process |
             +---------+
                 |
                 v
            [DEADLINE] <-- SHOULD meet this
                 |
                 ~ (Degraded performance if missed)
```

### 4. Distributed Operating Systems

**Characteristics:**
- Multiple CPUs connected through network
- Resources are shared
- Appears as single system to users

```
Site A                  Site B                  Site C
+-------+              +-------+              +-------+
| CPU   |              | CPU   |              | CPU   |
| Mem   |              | Mem   |              | Mem   |
| Disk  |              | Disk  |              | Disk  |
+-------+              +-------+              +-------+
    |                      |                      |
    +----------------------+----------------------+
                    NETWORK
              (High-Speed Communication)
```

**Advantages:**
- Resource sharing
- Computation speedup
- Reliability and fault tolerance
- Communication

### 5. Network Operating Systems

**Characteristics:**
- Computers connected through network
- Each computer aware of other computers
- Users explicitly access remote resources

```
Server                          Clients
+----------+                +----------+  +----------+
| Network  |                | Local OS |  | Local OS |
| Services |                | + Network|  | + Network|
| - Files  |<-------------->| Client   |  | Client   |
| - Print  |    Network     +----------+  +----------+
| - Auth   |                
+----------+               +----------+  +----------+
                           | Local OS |  | Local OS |
                           | + Network|  | + Network|
                           | Client   |  | Client   |
                           +----------+  +----------+
```

### 6. Mobile Operating Systems

**Characteristics:**
- Designed for mobile devices
- Touch-based interfaces
- Power management is critical
- App-based architecture

**Examples:** Android, iOS, HarmonyOS

---

## Operating System Structure

### 1. Simple Structure (MS-DOS)

MS-DOS was written to provide the most functionality in the least space.

```
+------------------------+
|   Application Program  |
+------------------------+
| Resident System Program|
+------------------------+
|    MS-DOS Drivers      |
+------------------------+
|    ROM BIOS Drivers    |
+------------------------+
```

**Characteristics:**
- No clear separation between interfaces and levels
- Vulnerable to malicious programs
- Limited functionality

### 2. Monolithic Structure (Traditional UNIX)

Everything runs in kernel mode with full access to hardware.

```
                 User Mode
+--------------------------------------------------+
|  Users  |  Shells  |  Applications  |  Compilers |
+--------------------------------------------------+
              System Call Interface
+--------------------------------------------------+
|               KERNEL MODE                        |
|  +--------------------------------------------+  |
|  |  File System  |  CPU Scheduling            |  |
|  |  Memory Mgmt  |  Signal Handler            |  |
|  |  Networking   |  Device Drivers            |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
|            Hardware Abstraction Layer           |
+--------------------------------------------------+
|                   HARDWARE                       |
+--------------------------------------------------+
```

**Advantages:**
- Fast execution (no message passing overhead)
- Direct access to hardware

**Disadvantages:**
- Difficult to maintain and debug
- Poor isolation between components
- Kernel crash affects entire system

### 3. Layered Approach

OS is divided into layers, each built on top of lower layers.

```
Layer N:  User Programs
          +----------------------------------+
Layer 5:  User Programs Interface
          +----------------------------------+
Layer 4:  I/O Buffering
          +----------------------------------+
Layer 3:  Operator-Console Device Driver
          +----------------------------------+
Layer 2:  Memory Management
          +----------------------------------+
Layer 1:  CPU Scheduling
          +----------------------------------+
Layer 0:  Hardware
          +----------------------------------+
```

**Advantages:**
- Simplicity of construction and debugging
- Each layer uses functions of lower layers only
- Easy to enhance

**Disadvantages:**
- Careful planning required
- Performance overhead

### 4. Microkernel Structure

Moves as much functionality as possible from kernel to user space.

```
                    USER SPACE
+--------------------------------------------------+
|  File    |  Device  |  Window  |  Application    |
|  Server  |  Driver  |  System  |  Programs       |
+--------------------------------------------------+
           ^    ^    ^    ^    ^    ^
           |    |    |    |    |    |
    Message Passing (IPC - Inter-Process Comm.)
           |    |    |    |    |    |
           v    v    v    v    v    v
+--------------------------------------------------+
|              MICROKERNEL                         |
|  +--------------------------------------------+  |
|  | - Basic Process Management                 |  |
|  | - Low-level Memory Management              |  |
|  | - Inter-Process Communication (IPC)        |  |
|  | - Basic Scheduling                         |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
|                  HARDWARE                        |
+--------------------------------------------------+
```

**Examples:** Mach, QNX, Minix

**Advantages:**
- Easy to extend
- More secure and reliable
- Easier to port to new architectures

**Disadvantages:**
- Performance overhead due to message passing
- More complex implementation

### 5. Modular Structure (Modern Approach)

Kernel has core components, and other services are loaded dynamically.

```
+--------------------------------------------------+
|                 KERNEL CORE                      |
|    - Process Management                          |
|    - Memory Management                           |
|    - IPC                                         |
+--------------------------------------------------+
           ^              ^              ^
           |              |              |
    [Module Loader/Interface]
           |              |              |
           v              v              v
+-------------+  +-------------+  +-------------+
| File System |  |   Device    |  |  Network    |
|   Module    |  |   Drivers   |  |   Stack     |
+-------------+  +-------------+  +-------------+
        Loadable Kernel Modules (LKMs)
```

**Examples:** Linux, Modern Solaris

**Advantages:**
- Flexibility (modules can be loaded/unloaded)
- Similar performance to monolithic
- Better organized than pure monolithic

---

## System Calls

System calls provide an interface between a process and the operating system. They are the only means by which a user program can access kernel services.

### System Call Mechanism

```
         USER MODE
+---------------------------+
|   User Application        |
|   printf("Hello");        |
+---------------------------+
          |
          | (1) Library Call
          v
+---------------------------+
|   C Library (libc)        |
|   Prepare system call     |
+---------------------------+
          |
          | (2) Trap/Software Interrupt
          v
====================== MODE SWITCH ========================
          |
          v
        KERNEL MODE
+---------------------------+
|   System Call Handler     |
|   (Dispatcher)            |
+---------------------------+
          |
          | (3) Call appropriate service
          v
+---------------------------+
|   Kernel Service Routine  |
|   (e.g., write())         |
+---------------------------+
          |
          | (4) Return result
          v
====================== MODE SWITCH ========================
          |
          v
        USER MODE
+---------------------------+
|   User Application        |
|   (continues execution)   |
+---------------------------+
```

### Types of System Calls

#### 1. Process Control
- `fork()` - Create a child process
- `exit()` - Terminate process
- `wait()` - Wait for child process
- `exec()` - Execute a program
- `kill()` - Send signal to process

#### 2. File Management
- `open()` - Open a file
- `close()` - Close a file
- `read()` - Read from file
- `write()` - Write to file
- `lseek()` - Reposition file pointer

#### 3. Device Management
- `ioctl()` - Control device
- `read()` - Read from device
- `write()` - Write to device

#### 4. Information Maintenance
- `getpid()` - Get process ID
- `time()` - Get system time
- `getuid()` - Get user ID

#### 5. Communication
- `pipe()` - Create pipe for IPC
- `socket()` - Create communication endpoint
- `send()`, `recv()` - Send/receive messages
- `shmget()` - Get shared memory segment

#### 6. Protection
- `chmod()` - Change file permissions
- `chown()` - Change file owner
- `setuid()` - Set user ID

### Example: Process Creation via System Calls

```
Parent Process                 Child Process
+-------------+
|   fork()    |
+-------------+
      |
      | System call
      v
  [KERNEL]
      |
      +--------> Creates copy
      |                |
      v                v
+-------------+  +-------------+
| Parent      |  | Child       |
| (fork()>0)  |  | (fork()=0)  |
+-------------+  +-------------+
      |                |
      v                v
  Continue          Execute
  execution         new task
```

---

## Operating System Services

### User-Oriented Services

```
                    USER
                      |
                      v
+--------------------------------------------------+
|  1. User Interface (UI)                          |
|     - CLI (Command Line Interface)               |
|     - GUI (Graphical User Interface)             |
|     - Batch Interface                            |
+--------------------------------------------------+
|  2. Program Execution                            |
|     - Load program into memory                   |
|     - Run the program                            |
|     - End execution (normal or abnormal)         |
+--------------------------------------------------+
|  3. I/O Operations                               |
|     - File I/O                                   |
|     - Device I/O                                 |
+--------------------------------------------------+
|  4. File System Manipulation                     |
|     - Read, write, create, delete files          |
|     - Search files and directories               |
|     - Permission management                      |
+--------------------------------------------------+
|  5. Communications                               |
|     - Inter-process communication (IPC)          |
|     - Network communication                      |
+--------------------------------------------------+
|  6. Error Detection                              |
|     - Hardware errors (CPU, memory, I/O)         |
|     - Software errors (overflow, illegal access) |
+--------------------------------------------------+
```

### System-Oriented Services

```
+--------------------------------------------------+
|  1. Resource Allocation                          |
|     - CPU scheduling                             |
|     - Memory allocation                          |
|     - Device allocation                          |
+--------------------------------------------------+
|  2. Accounting                                   |
|     - Track resource usage per user/process      |
|     - Usage statistics                           |
+--------------------------------------------------+
|  3. Protection and Security                      |
|     - Access control                             |
|     - User authentication                        |
|     - Defend against internal/external attacks   |
+--------------------------------------------------+
```

---

## OS Kernel

The **kernel** is the core component of an OS that has complete control over everything in the system.

### Kernel Types

```
1. MONOLITHIC KERNEL              2. MICROKERNEL
+-------------------+             +-------------------+
|                   |             | Minimal Kernel    |
|   All Services    |             +-------------------+
|   in Kernel       |                     |
|   - File System   |             User Space Services
|   - Drivers       |             +-------------------+
|   - Networking    |             | File    | Device  |
|   - Memory Mgmt   |             | System  | Drivers |
|   - IPC           |             +-------------------+
|                   |             | Network | Window  |
+-------------------+             | Stack   | System  |
                                  +-------------------+

3. HYBRID KERNEL                  4. EXOKERNEL
+-------------------+             +-------------------+
| Microkernel Core  |             | Minimal Resource  |
| + Some Services   |             | Multiplexing      |
| in Kernel         |             +-------------------+
|                   |                     |
| User Space        |             Application-Level
| +---------------+ |             Resource Management
| | Some Services | |             +-------------------+
| +---------------+ |             | App-specific      |
+-------------------+             | Optimizations     |
                                  +-------------------+
```

### Kernel Mode vs User Mode

```
CPU Privilege Levels:

Ring 0 (Kernel Mode)
+--------------------------------+
| - Full hardware access         |
| - Execute privileged           |
|   instructions                 |
| - Direct memory access         |
| - Control I/O                  |
+--------------------------------+
         ^         |
         |         | System Calls
         |         | (Mode Switch)
         |         v
Ring 3 (User Mode)
+--------------------------------+
| - Limited access               |
| - Cannot execute privileged    |
|   instructions                 |
| - Restricted memory access     |
| - Request services via         |
|   system calls                 |
+--------------------------------+
```

---

## Boot Process

The sequence of events that occurs when a computer is powered on:

```
Step 1: Power On
   |
   v
+------------------+
| BIOS/UEFI        |
| - POST (Power On |
|   Self Test)     |
+------------------+
   |
   v
Step 2: Boot Loader Location
+------------------+
| Find Boot Device |
| (Hard Disk, USB, |
| Network)         |
+------------------+
   |
   v
Step 3: Boot Loader
+------------------+
| GRUB/LILO        |
| - Display menu   |
| - Load kernel    |
+------------------+
   |
   v
Step 4: Kernel Loading
+------------------+
| Load Kernel into |
| Memory           |
| Initialize       |
| Hardware         |
+------------------+
   |
   v
Step 5: Init Process
+------------------+
| Start init/      |
| systemd (PID=1)  |
+------------------+
   |
   v
Step 6: User Space
+------------------+
| Start System     |
| Services         |
| Login Prompt     |
+------------------+
```

---

## Interrupts and Traps

### Interrupt Mechanism

```
CPU Executing Program A
        |
        | (1) Interrupt occurs (e.g., I/O completion)
        v
+------------------+
| Save state of    |
| Program A        |
| (PC, registers)  |
+------------------+
        |
        | (2) Transfer control
        v
+------------------+
| Interrupt Vector |
| Table            |
+------------------+
        |
        | (3) Jump to ISR
        v
+------------------+
| Interrupt Service|
| Routine (ISR)    |
| Handler          |
+------------------+
        |
        | (4) Handle interrupt
        v
+------------------+
| Restore state of |
| Program A        |
+------------------+
        |
        | (5) Resume
        v
CPU Resumes Program A
```

### Types of Interrupts

1. **Hardware Interrupts**
   - Generated by hardware devices
   - Examples: Keyboard input, timer tick, disk I/O completion

2. **Software Interrupts (Traps)**
   - Generated by software
   - System calls
   - Exceptions (division by zero, page fault)

```
Interrupt Priority:
High  ┌─────────────────┐
      │ Machine Check   │
      ├─────────────────┤
      │ Clock/Timer     │
      ├─────────────────┤
      │ Disk I/O        │
      ├─────────────────┤
      │ Network         │
      ├─────────────────┤
      │ Keyboard        │
      ├─────────────────┤
      │ Software Int    │
Low   └─────────────────┘
```

---

## Summary

- Operating systems act as intermediaries between hardware and users
- Core functions: Process management, memory management, file systems, I/O
- Various types: Batch, Time-sharing, Real-time, Distributed, Network, Mobile
- Structures: Monolithic, Layered, Microkernel, Modular
- System calls provide interface for user programs to access kernel services
- Kernel operates in privileged mode with full hardware access
- Boot process initializes hardware and starts OS
- Interrupts allow hardware and software to signal the CPU for attention

---

**Next Topics:**
- Process Management
- Memory Management
- CPU Scheduling
- File Systems

