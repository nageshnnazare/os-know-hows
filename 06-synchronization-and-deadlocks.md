# Operating Systems - Synchronization and Deadlocks

## Table of Contents
1. [Process Synchronization](#process-synchronization)
2. [Critical Section Problem](#critical-section-problem)
3. [Synchronization Hardware](#synchronization-hardware)
4. [Semaphores](#semaphores)
5. [Classic Synchronization Problems](#classic-synchronization-problems)
6. [Monitors](#monitors)
7. [Deadlocks](#deadlocks)
8. [Deadlock Handling](#deadlock-handling)

---

## Process Synchronization

When multiple processes access shared data concurrently, data inconsistency may occur.

### Race Condition Example

```
SHARED VARIABLE: count = 5

Process P1:             Process P2:
count = count + 1       count = count - 1

MACHINE CODE:

P1:                     P2:
load R1, count          load R2, count
add R1, 1               sub R2, 1
store R1, count         store R2, count

EXECUTION SCENARIOS:

Scenario 1 (Sequential - Correct):
P1: load R1, count      (R1 = 5)
P1: add R1, 1           (R1 = 6)
P1: store R1, count     (count = 6)
P2: load R2, count      (R2 = 6)
P2: sub R2, 1           (R2 = 5)
P2: store R2, count     (count = 5)
Result: count = 5 ✓

Scenario 2 (Interleaved - INCORRECT):
P1: load R1, count      (R1 = 5)
P2: load R2, count      (R2 = 5)  ← Race!
P1: add R1, 1           (R1 = 6)
P2: sub R2, 1           (R2 = 4)
P1: store R1, count     (count = 6)
P2: store R2, count     (count = 4)  ← Wrong!
Result: count = 4 ✗ (Should be 5)

P1's update is lost!
```

### Producer-Consumer Problem

```
SHARED BUFFER:
+---+---+---+---+---+
|   |   |   |   |   |  (size = 5)
+---+---+---+---+---+
 0   1   2   3   4

shared int count = 0;  // Number of items in buffer

PRODUCER:                   CONSUMER:
while (true) {              while (true) {
  produce item                while (count == 0)
                                ; // wait
  while (count == 5)         count--;  ← Race!
    ; // wait                consume item
  count++;  ← Race!
  add item to buffer         remove item from buffer
}                           }

RACE CONDITION:
Producer:  load R1, count  (R1 = 5)
           add R1, 1       (R1 = 6)
Consumer:  load R2, count  (R2 = 5)  ← Interleaved!
           sub R2, 1       (R2 = 4)
Producer:  store R1, count (count = 6)  ← Overflow!
Consumer:  store R2, count (count = 4)

Buffer overflow or underflow!
```

---

## Critical Section Problem

**Critical Section**: Code segment where shared data is accessed.

### Requirements for Solution

```
PROCESS STRUCTURE:

do {
  +------------------------+
  | Entry Section          |  ← Request permission
  +------------------------+
  |                        |
  | CRITICAL SECTION       |  ← Accessing shared data
  |                        |
  +------------------------+
  | Exit Section           |  ← Release permission
  +------------------------+
  |                        |
  | Remainder Section      |  ← Other work
  |                        |
  +------------------------+
} while (true);
```

### Solution Requirements

```
1. MUTUAL EXCLUSION:
   Only one process in critical section at a time
   
   Time:  t0    t1    t2    t3    t4
   P1:    [ENTER CS......EXIT]
   P2:          [WAIT.........ENTER CS...
   
   At most one process in CS

2. PROGRESS:
   If no process in CS, selection cannot be postponed indefinitely
   Only processes not in remainder section can participate
   
   Not allowed:
   P1 in remainder, P2 wants CS → P2 waits forever

3. BOUNDED WAITING:
   Bound on number of times others enter CS after process requests
   
   P1 requests CS
   P2 enters CS (1st time)
   P2 enters CS (2nd time)
   ...
   P2 enters CS (Nth time)
   P1 enters CS
   
   N must be bounded (prevent starvation)
```

### Peterson's Solution (2 Process)

```c
// Shared variables
bool flag[2] = {false, false};  // Intent to enter CS
int turn = 0;                   // Whose turn it is

// Process Pi (i = 0 or 1, j = 1-i)
do {
  flag[i] = true;        // I want to enter
  turn = j;              // But you can go first
  
  while (flag[j] && turn == j)
    ; // Wait
    
  // CRITICAL SECTION
  
  flag[i] = false;       // I'm done
  
  // REMAINDER SECTION
} while (true);
```

**Example Execution:**

```
Initial: flag[0]=F, flag[1]=F, turn=0

P0 wants CS:
  flag[0] = true      State: flag[0]=T, flag[1]=F, turn=1
  turn = 1
  Check: flag[1]=F → Enter CS!

P1 wants CS (while P0 in CS):
  flag[1] = true      State: flag[0]=T, flag[1]=T, turn=0
  turn = 0
  Check: flag[0]=T and turn=0 → Wait!

P0 exits CS:
  flag[0] = false     State: flag[0]=F, flag[1]=T, turn=0

P1's loop:
  Check: flag[0]=F → Enter CS!

Mutual Exclusion: ✓
Progress: ✓
Bounded Waiting: ✓ (at most 1 time)
```

---

## Synchronization Hardware

### Test-and-Set Instruction

```c
// Atomic hardware instruction
bool test_and_set(bool *target) {
  bool rv = *target;
  *target = true;
  return rv;
}

// Using test_and_set for mutual exclusion
bool lock = false;  // Shared

// Process
do {
  while (test_and_set(&lock))
    ; // Wait (busy waiting)
    
  // CRITICAL SECTION
  
  lock = false;  // Release lock
  
  // REMAINDER SECTION
} while (true);
```

**Execution:**

```
Initial: lock = false

P1: test_and_set(&lock)
    Returns false, sets lock=true → P1 enters CS

P2: test_and_set(&lock)
    Returns true, lock stays true → P2 waits

Timeline:
Time:  0    1    2    3    4    5    6
P1:    [TS][CRITICAL SECTION...][Release]
P2:         [TS][TS][TS][TS][TS][Enter CS]
             ↑   Busy waiting (spinlock)

Advantages:
+ Simple
+ Works for any number of processes

Disadvantages:
- Busy waiting (wastes CPU)
- No bounded waiting guarantee
```

### Compare-and-Swap (CAS)

```c
// Atomic hardware instruction
int compare_and_swap(int *value, int expected, int new_value) {
  int temp = *value;
  if (*value == expected)
    *value = new_value;
  return temp;
}

// Using CAS for mutual exclusion
int lock = 0;  // Shared

// Process
do {
  while (compare_and_swap(&lock, 0, 1) != 0)
    ; // Wait
    
  // CRITICAL SECTION
  
  lock = 0;  // Release lock
  
  // REMAINDER SECTION
} while (true);
```

**With Bounded Waiting:**

```c
bool waiting[n] = {false, ...};
int lock = 0;

// Process i
do {
  waiting[i] = true;
  int key = 1;
  
  while (waiting[i] && key == 1)
    key = compare_and_swap(&lock, 0, 1);
  waiting[i] = false;
  
  // CRITICAL SECTION
  
  // Find next waiting process
  j = (i + 1) % n;
  while ((j != i) && !waiting[j])
    j = (j + 1) % n;
    
  if (j == i)
    lock = 0;  // No one waiting
  else
    waiting[j] = false;  // Pass to next
    
  // REMAINDER SECTION
} while (true);

Bounded waiting: O(n-1)
```

---

## Semaphores

Abstract data type for synchronization.

### Semaphore Operations

```
SEMAPHORE S:
- Integer variable
- Accessed only through atomic operations

wait(S) [P operation, down]:
  S--;
  if (S < 0) {
    block this process
    add to S's waiting queue
  }

signal(S) [V operation, up]:
  S++;
  if (S <= 0) {
    remove process P from S's queue
    wakeup(P)
  }
```

### Binary Semaphore (Mutex)

```
semaphore mutex = 1;  // Initially unlocked

Process:
  wait(mutex);      // Lock
  
  // CRITICAL SECTION
  
  signal(mutex);    // Unlock

Timeline:
S=1  S=0         S=1
↓    ↓           ↓
P1:  [wait][CS...][signal]
P2:       [wait-blocked..][CS...

Value:  1 → 0 → 1 → 0
```

### Counting Semaphore

```
RESOURCE ALLOCATION:
Resources: 5 identical printers

semaphore printers = 5;

Process:
  wait(printers);     // Acquire printer
  
  // Use printer
  
  signal(printers);   // Release printer

States:
printers = 5  (5 available)
P1: wait → printers = 4
P2: wait → printers = 3
P3: wait → printers = 2
P4: wait → printers = 1
P5: wait → printers = 0
P6: wait → printers = -1 (P6 blocks!)
      ↓
P1: signal → printers = 0 (P6 wakes up!)
```

### Implementation

```c
typedef struct {
  int value;
  struct process *list;  // Waiting queue
} semaphore;

void wait(semaphore *S) {
  S->value--;
  if (S->value < 0) {
    add this process to S->list;
    block();  // Context switch
  }
}

void signal(semaphore *S) {
  S->value++;
  if (S->value <= 0) {
    remove process P from S->list;
    wakeup(P);  // Make ready
  }
}

No busy waiting! (except in wait/signal themselves)
Use spinlock for short wait/signal code
```

### Deadlock with Semaphores

```
semaphore S = 1, Q = 1;

P0:                     P1:
wait(S);                wait(Q);
wait(Q);                wait(S);
  ...                     ...
signal(S);              signal(Q);
signal(Q);              signal(S);

DEADLOCK SCENARIO:
T0: P0 executes wait(S)  → S = 0, P0 has S
T1: P1 executes wait(Q)  → Q = 0, P1 has Q
T2: P0 executes wait(Q)  → Q = -1, P0 blocks (waiting for P1)
T3: P1 executes wait(S)  → S = -1, P1 blocks (waiting for P0)

P0 waiting for Q (held by P1)
P1 waiting for S (held by P0)
DEADLOCK!

Solution: Impose ordering
Both processes acquire in same order:
wait(S); wait(Q);
```

---

## Classic Synchronization Problems

### 1. Bounded Buffer (Producer-Consumer)

```c
#define N 10  // Buffer size

semaphore mutex = 1;    // Mutual exclusion for buffer
semaphore empty = N;    // Count of empty slots
semaphore full = 0;     // Count of full slots

PRODUCER:
do {
  // Produce item
  
  wait(empty);     // Wait for empty slot
  wait(mutex);     // Lock buffer
  
  // Add item to buffer
  
  signal(mutex);   // Unlock buffer
  signal(full);    // Increment full count
} while (true);

CONSUMER:
do {
  wait(full);      // Wait for full slot
  wait(mutex);     // Lock buffer
  
  // Remove item from buffer
  
  signal(mutex);   // Unlock buffer
  signal(empty);   // Increment empty count
  
  // Consume item
} while (true);

Timeline:
empty=5, full=0, mutex=1

Producer:
  wait(empty) → empty=4
  wait(mutex) → mutex=0
  [add item]
  signal(mutex) → mutex=1
  signal(full) → full=1

Consumer:
  wait(full) → full=0
  wait(mutex) → mutex=0
  [remove item]
  signal(mutex) → mutex=1
  signal(empty) → empty=5
```

### 2. Readers-Writers Problem

Multiple readers can read simultaneously, but writers need exclusive access.

```c
semaphore rw_mutex = 1;    // Writer lock
semaphore mutex = 1;       // Protect read_count
int read_count = 0;        // Number of readers

WRITER:
do {
  wait(rw_mutex);   // Exclusive access
  
  // WRITING
  
  signal(rw_mutex);
} while (true);

READER:
do {
  wait(mutex);
  read_count++;
  if (read_count == 1)
    wait(rw_mutex);  // First reader locks out writers
  signal(mutex);
  
  // READING
  
  wait(mutex);
  read_count--;
  if (read_count == 0)
    signal(rw_mutex);  // Last reader unlocks
  signal(mutex);
} while (true);

Scenario:
R1 enters:
  read_count=1, locks rw_mutex
  
R2 enters:
  read_count=2, rw_mutex already locked
  Both reading simultaneously ✓

W1 tries to enter:
  Waits on rw_mutex (blocked by readers)

R1 exits:
  read_count=1

R2 exits:
  read_count=0, unlocks rw_mutex

W1 enters:
  Acquires rw_mutex, writes exclusively

Problem: Writer starvation (if readers keep coming)

Solution: Writer preference
Use additional semaphores to give writers priority
```

### 3. Dining Philosophers

```
SETUP:
      Philosopher 0
           🍴
    Philosopher 4  Philosopher 1
         🍴           🍴
    Philosopher 3  Philosopher 2
           🍴

5 philosophers, 5 chopsticks
Philosopher i needs chopsticks i and (i+1)%5

semaphore chopstick[5] = {1, 1, 1, 1, 1};

PROBLEMATIC SOLUTION:
do {
  wait(chopstick[i]);
  wait(chopstick[(i+1) % 5]);
  
  // EAT
  
  signal(chopstick[i]);
  signal(chopstick[(i+1) % 5]);
  
  // THINK
} while (true);

DEADLOCK:
T0: All philosophers pick up left chopstick
  P0 has chopstick[0]
  P1 has chopstick[1]
  P2 has chopstick[2]
  P3 has chopstick[3]
  P4 has chopstick[4]

T1: All philosophers try to pick up right chopstick
  P0 waits for chopstick[1] (held by P1)
  P1 waits for chopstick[2] (held by P2)
  P2 waits for chopstick[3] (held by P3)
  P3 waits for chopstick[4] (held by P4)
  P4 waits for chopstick[0] (held by P0)
  
CIRCULAR WAIT → DEADLOCK!

SOLUTIONS:

1. Allow at most 4 philosophers at table:
   semaphore room = 4;
   wait(room);
   [pick chopsticks, eat]
   signal(room);

2. Asymmetric solution:
   Odd philosophers: left then right
   Even philosophers: right then left
   
   Breaks circular wait!

3. Pick both chopsticks atomically:
   semaphore mutex = 1;
   wait(mutex);
   wait(chopstick[i]);
   wait(chopstick[(i+1) % 5]);
   signal(mutex);
   [eat]
   signal(chopstick[i]);
   signal(chopstick[(i+1) % 5]);
```

---

## Monitors

High-level synchronization construct (programming language construct).

### Monitor Structure

```
MONITOR:
+----------------------------------+
| Shared Data                      |
|   int count;                     |
|   int buffer[N];                 |
+----------------------------------+
| Initialization Code              |
|   count = 0;                     |
+----------------------------------+
| Operations (Procedures)          |
|   procedure insert(item) {       |
|     // Insert item               |
|   }                              |
|   procedure remove() {           |
|     // Remove and return item    |
|   }                              |
+----------------------------------+

Key Properties:
- Only ONE process can be active inside monitor at a time
- Mutual exclusion is automatic
- Shared data accessible only through monitor procedures
```

### Condition Variables

```
CONDITION VARIABLES:
condition x, y;

Operations:
  x.wait()   - Suspend process on condition x
  x.signal() - Resume one process waiting on x

BOUNDED BUFFER MONITOR:

monitor BoundedBuffer {
  int buffer[N];
  int count = 0;
  condition not_full, not_empty;
  
  procedure insert(int item) {
    while (count == N)
      not_full.wait();  // Wait until space available
      
    buffer[count++] = item;
    not_empty.signal(); // Wake up waiting consumer
  }
  
  procedure remove() : int {
    while (count == 0)
      not_empty.wait(); // Wait until item available
      
    int item = buffer[--count];
    not_full.signal();  // Wake up waiting producer
    return item;
  }
}

EXECUTION:
Producer:                 Consumer:
  monitor.insert(item)      monitor.remove()
    ↓                         ↓
  [ONE AT A TIME IN MONITOR]
  
Timeline:
T0: Producer enters insert()
T1: Consumer tries to enter remove() → WAITS (monitor busy)
T2: Producer exits insert()
T3: Consumer enters remove()
```

### Monitor Implementation

```
Implemented using semaphores:

semaphore mutex = 1;        // Mutual exclusion
semaphore next = 0;         // For signaling process
int next_count = 0;         // Count waiting in next

Each condition x has:
  semaphore x_sem = 0;      // Process waiting on x
  int x_count = 0;          // Count of waiting

Monitor procedure P:
  wait(mutex);
  ... body of P ...
  if (next_count > 0)
    signal(next);
  else
    signal(mutex);

x.wait():
  x_count++;
  if (next_count > 0)
    signal(next);
  else
    signal(mutex);
  wait(x_sem);
  x_count--;

x.signal():
  if (x_count > 0) {
    next_count++;
    signal(x_sem);
    wait(next);
    next_count--;
  }
```

---

## Deadlocks

A set of processes is deadlocked if each process is waiting for an event that can only be caused by another process in the set.

### Deadlock Example

```
SYSTEM RESOURCES:
Tape Drive: T1, T2
Plotter: P1

Process A:             Process B:
Allocate T1            Allocate T2
Allocate T2 (wait)     Allocate T1 (wait)
Use T1, T2             Use T2, T1
Release T1, T2         Release T2, T1

EXECUTION:
T0: A gets T1          B gets T2
T1: A requests T2      B requests T1
    (held by B)        (held by A)
    A waits            B waits
    
DEADLOCK!

Resource Allocation Graph:
    T1 -----> A -----> T2
    ^                   |
    |                   v
    B <------ T2        
    
Cycle in graph → Deadlock
```

### Necessary Conditions for Deadlock

All four must hold simultaneously:

```
1. MUTUAL EXCLUSION:
   At least one resource must be non-sharable
   
   [Resource R]
        ↓
    [Process P] (Exclusive access)
   
   Example: Printer (can't be shared)

2. HOLD AND WAIT:
   Process holding resources can request more
   
   Process A:
   Has: R1
   Wants: R2 (waiting)

3. NO PREEMPTION:
   Resources cannot be forcibly taken away
   
   Process A has R1
   OS cannot take R1 from A
   A must release R1 voluntarily

4. CIRCULAR WAIT:
   P1 → P2 → P3 → ... → Pn → P1
   (Each waiting for next)
   
   P1 waits for P2
   P2 waits for P3
   ...
   Pn waits for P1
```

### Resource Allocation Graph

```
NOTATION:
  ○ Process
  □ Resource (with dots = instances)
  → Request edge (process requests resource)
  ← Assignment edge (resource allocated to process)

EXAMPLE 1 (No Deadlock):

    □ R1        □ R2
    ●●          ●●
     ↓           ↓
    P1          P2
     ↓           ↓
    □ R3        □ R4
    ●           ●

No cycle → No deadlock

EXAMPLE 2 (Deadlock):

    □ R1
    ●
   ↙ ↓
  P1 P2
   ↓ ↑
  □ R2
   ●

Cycle: P1 → R2 → P2 → R1 → P1
Deadlock!

EXAMPLE 3 (Cycle but No Deadlock):

    □ R1
    ●●
   ↙ ↓ ↘
  P1 P2 P3
   ↓
  □ R2
   ●

Cycle: P1 → R1 → P2 → R2 → P1
But R1 has 2 instances
P3 can finish, release R1
Then P2 can get R1
No deadlock (despite cycle)

Rule:
- If no cycle → No deadlock
- If cycle → Maybe deadlock
  (Deadlock if single-instance resources)
```

---

## Deadlock Handling

### 1. Deadlock Prevention

Ensure at least one necessary condition cannot hold.

```
BREAK MUTUAL EXCLUSION:
  Make resources sharable
  
  Example: Read-only files
  Multiple processes can read simultaneously
  
  Problem: Not always possible
  (Can't share printer, tape drive)

BREAK HOLD AND WAIT:
  Process must request all resources at once
  
  Process A:
    Request R1, R2, R3 simultaneously
    Either gets all or none
    
  Protocol 1:
    request_resources(R1, R2, R3);
    if (all granted)
      use_resources();
      release_all();
  
  Protocol 2:
    Release all resources before requesting new ones
  
  Problems:
  - Low resource utilization
  - Starvation possible

BREAK NO PREEMPTION:
  Preempt resources
  
  Process A has R1, R2
  Requests R3 (not available)
  → Preempt R1, R2 from A
  → Give to waiting processes
  → A waits until can get R1, R2, R3
  
  Applicable to:
  + CPU, memory (save/restore state)
  - Printers, tape drives (can't save state)

BREAK CIRCULAR WAIT:
  Impose ordering on resource types
  
  Resources: R1, R2, R3, R4, R5
  Order: R1 < R2 < R3 < R4 < R5
  
  Rule: Request in increasing order
  
  Process A:
    Request R1 (OK)
    Request R3 (OK, 3 > 1)
    Request R2 (NOT OK, 2 < 3)
  
  Why it works:
  P1 has Ri, requests Rj (j > i)
  P2 has Rj, requests Rk (k > j)
  ...
  Cannot form cycle!
  (Always moving to higher numbered resources)
  
  Dining Philosophers Solution:
  Chopsticks: C0, C1, C2, C3, C4
  Each philosopher requests lower numbered first:
  
  P0: Request C0, then C1
  P1: Request C1, then C2
  P2: Request C2, then C3
  P3: Request C3, then C4
  P4: Request C0, then C4  (4 > 0, violates!)
  
  Fix: P4 requests C4 first, then C0
  No circular wait possible!
```

### 2. Deadlock Avoidance

Use additional information about resource requests.

#### Safe State

```
SAFE STATE:
System can allocate resources to each process
in some order and avoid deadlock

Example:
Processes: P0, P1, P2
Resource type: 12 instances

         Allocation  Max  Available
P0          0         10      3
P1          2          4
P2          3          9

Safe sequence: <P1, P0, P2>

Step 1: P1 runs
  P1 has 2, needs 4
  Available: 3
  Can allocate 2 more → P1 finishes
  P1 releases 4
  Available: 3 + 4 = 7

Step 2: P0 runs
  P0 has 0, needs 10
  Available: 7
  Can allocate 7, but still needs 3
  (After P1, more available)
  P0 gets 10 → P0 finishes
  P0 releases 10
  Available: 7 + 10 = 17

Step 3: P2 runs
  P2 has 3, needs 9
  Available: 17
  Can allocate 6 more → P2 finishes

Safe sequence exists → Safe state

UNSAFE STATE:
No safe sequence exists
(Doesn't mean deadlock will occur,
 but deadlock is possible)

Example:
         Allocation  Max  Available
P0          5         10      2
P1          2          4
P2          2          9

Try P1: Has 2, needs 4, available 2
        Can get 2 more → P1 finishes
        Available: 2 + 4 = 6

Try P0: Has 5, needs 10, available 6
        Can get 5, needs 5 more (not enough!)
        
Try P2: Has 2, needs 9, available 6
        Can get 4, needs 5 more (not enough!)

No safe sequence → Unsafe state
```

#### Banker's Algorithm

```
DATA STRUCTURES:
n = number of processes
m = number of resource types

Available[m]:    Available resources
Max[n][m]:       Maximum demand
Allocation[n][m]: Current allocation
Need[n][m]:      Remaining need
                 Need = Max - Allocation

SAFETY ALGORITHM:

1. Work = Available
   Finish[i] = false for all i

2. Find i such that:
   - Finish[i] == false
   - Need[i] <= Work
   
   If no such i exists, go to step 4

3. Work = Work + Allocation[i]
   Finish[i] = true
   Go to step 2

4. If Finish[i] == true for all i
   → System is safe

EXAMPLE:
5 processes (P0-P4)
3 resource types (A=10, B=5, C=7)

     Allocation  Max      Need
     A  B  C    A  B  C   A  B  C
P0   0  1  0    7  5  3   7  4  3
P1   2  0  0    3  2  2   1  2  2
P2   3  0  2    9  0  2   6  0  0
P3   2  1  1    2  2  2   0  1  1
P4   0  0  2    4  3  3   4  3  1

Available: A=3, B=3, C=2

Check P1:
  Need[1] = (1,2,2)
  Available = (3,3,2)
  1<=3, 2<=3, 2<=2 ✓
  Allocate to P1
  P1 finishes, releases (2,0,0)
  Available = (5,3,2)

Check P3:
  Need[3] = (0,1,1)
  Available = (5,3,2)
  0<=5, 1<=3, 1<=2 ✓
  P3 finishes, releases (2,1,1)
  Available = (7,4,3)

Check P4:
  Need[4] = (4,3,1)
  Available = (7,4,3)
  4<=7, 3<=4, 1<=3 ✓
  P4 finishes, releases (0,0,2)
  Available = (7,4,5)

Check P0:
  Need[0] = (7,4,3)
  Available = (7,4,5)
  7<=7, 4<=4, 3<=5 ✓
  P0 finishes, releases (0,1,0)
  Available = (7,5,5)

Check P2:
  Need[2] = (6,0,0)
  Available = (7,5,5)
  6<=7, 0<=5, 0<=5 ✓
  P2 finishes

Safe sequence: <P1, P3, P4, P0, P2>
System is SAFE!

RESOURCE REQUEST ALGORITHM:

Request[i] = request by process Pi

1. If Request[i] <= Need[i], go to step 2
   Otherwise, error (exceeds maximum claim)

2. If Request[i] <= Available, go to step 3
   Otherwise, Pi must wait

3. Pretend to allocate:
   Available = Available - Request[i]
   Allocation[i] = Allocation[i] + Request[i]
   Need[i] = Need[i] - Request[i]

4. Run safety algorithm
   If safe → Grant request
   If unsafe → Deny request, restore state
```

### 3. Deadlock Detection

Allow deadlocks, but detect and recover.

```
SINGLE INSTANCE RESOURCES:

Wait-for Graph:
(Remove resource nodes from allocation graph)

Resource Allocation Graph:
  P1 → R1 → P2 → R2 → P3
  
Wait-for Graph:
  P1 → P2 → P3
  
Deadlock if cycle in wait-for graph

Algorithm: O(n²) cycle detection

MULTIPLE INSTANCE RESOURCES:

Similar to Banker's Algorithm
But use current allocation (no max)

DATA STRUCTURES:
Available[m]
Allocation[n][m]
Request[n][m]: Current request

DETECTION ALGORITHM:

1. Work = Available
   Finish[i] = false if Allocation[i] != 0
   Finish[i] = true if Allocation[i] == 0

2. Find i such that:
   Finish[i] == false
   Request[i] <= Work
   
   If no such i, go to step 4

3. Work = Work + Allocation[i]
   Finish[i] = true
   Go to step 2

4. If Finish[i] == false for some i
   → Pi is deadlocked

When to invoke?
- Every time a request cannot be granted
- At regular intervals
- When CPU utilization drops

EXAMPLE:
     Allocation  Request  Available
     A  B  C    A  B  C    A  B  C
P0   0  1  0    0  0  0    0  0  0
P1   2  0  0    2  0  2
P2   3  0  3    0  0  0
P3   2  1  1    1  0  0
P4   0  0  2    0  0  2

Work = (0,0,0)

Check P0: Request = (0,0,0) <= (0,0,0) ✓
  Work = (0,0,0) + (0,1,0) = (0,1,0)
  Finish[0] = true

Check P2: Request = (0,0,0) <= (0,1,0) ✓
  Work = (0,1,0) + (3,0,3) = (3,1,3)
  Finish[2] = true

Check P3: Request = (1,0,0) <= (3,1,3) ✓
  Work = (3,1,3) + (2,1,1) = (5,2,4)
  Finish[3] = true

Check P1: Request = (2,0,2) <= (5,2,4) ✓
  Work = (5,2,4) + (2,0,0) = (7,2,4)
  Finish[1] = true

Check P4: Request = (0,0,2) <= (7,2,4) ✓
  Work = (7,2,4) + (0,0,2) = (7,2,6)
  Finish[4] = true

All Finish[i] = true → No deadlock
```

### 4. Deadlock Recovery

Once deadlock detected, recover.

```
RECOVERY METHODS:

1. PROCESS TERMINATION:

   a) Abort all deadlocked processes
      +---+---+---+
      | P1| P2| P3|  (All in deadlock)
      +---+---+---+
           ↓
      TERMINATE ALL
      
      Simple but expensive

   b) Abort one process at a time
      +---+---+---+
      | P1| P2| P3|
      +---+---+---+
           ↓
      Terminate P1
      Check deadlock
      If still deadlocked, terminate P2
      Repeat...
      
      Overhead of detection after each abort
   
   Choosing victim:
   - Priority
   - Computation time
   - Resources held
   - Resources needed
   - Number of processes affected
   - Interactive vs. batch

2. RESOURCE PREEMPTION:

   Select victim:
   Rollback to safe state
   (Need checkpointing)
   
   Timeline:
   P1: [Checkpoint1]-[Progress]-[Deadlock]
                   ↑             |
                   +-------------+ Rollback
       
   Restart from checkpoint
   
   Issues:
   - Overhead of checkpointing
   - Starvation (same process always victim)
     Solution: Include rollback count in cost
```

---

## Livelock

Processes continuously change state but make no progress.

```
EXAMPLE:
Two people in narrow hallway

T0: Person A moves right, Person B moves right (block)
T1: Person A moves left, Person B moves left (block)
T2: Person A moves right, Person B moves right (block)
...

Both are "active" but not progressing

Code Example:
Process P1:              Process P2:
while (true) {           while (true) {
  if (conflict())          if (conflict())
    yield_to_other();        yield_to_other();
}                        }

Both keep yielding to each other!

Solution:
- Random backoff
- Priority (one always yields)
```

---

## Starvation

Process never gets resources it needs.

```
Example with Priority Scheduling:

High priority processes: P1, P2, P3 (keep arriving)
Low priority process: P4

Ready Queue:
Time 0:  [P1 (high), P4 (low)]
Time 1:  [P2 (high), P4 (low)]  (P1 done, P2 arrives)
Time 2:  [P3 (high), P4 (low)]  (P2 done, P3 arrives)
...

P4 never runs! (Starvation)

Solution: Aging
Time 0:  P4 priority = 10
Time 1:  P4 priority = 9
Time 2:  P4 priority = 8
...
Eventually P4 gets high enough priority
```

---

## Summary

- **Synchronization**: Needed for shared data access
- **Critical Section**: Must satisfy mutual exclusion, progress, bounded waiting
- **Hardware Support**: Test-and-set, Compare-and-swap
- **Semaphores**: wait()/signal() for synchronization
- **Classic Problems**: Producer-Consumer, Readers-Writers, Dining Philosophers
- **Monitors**: High-level synchronization with condition variables
- **Deadlock Conditions**: Mutual exclusion, Hold & wait, No preemption, Circular wait
- **Deadlock Handling**:
  - Prevention: Break one of four conditions
  - Avoidance: Banker's algorithm, safe states
  - Detection: Wait-for graphs, detection algorithm
  - Recovery: Process termination, resource preemption
- **Related Issues**: Livelock, starvation

Synchronization and deadlock handling are critical for reliable multi-process systems!

---

**Next Topics:**
- I/O Systems
- Storage Management
- Security and Protection

