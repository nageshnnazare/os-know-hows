# Operating Systems - System Programming and APIs

## Table of Contents
1. [POSIX API Fundamentals](#posix-api-fundamentals)
2. [Process Management APIs](#process-management-apis)
3. [File I/O and File Systems](#file-io-and-file-systems)
4. [Inter-Process Communication](#inter-process-communication)
5. [Signals and Signal Handling](#signals-and-signal-handling)
6. [Multithreading with Pthreads](#multithreading-with-pthreads)
7. [Memory Management APIs](#memory-management-apis)
8. [Network Programming](#network-programming)

---

## POSIX API Fundamentals

### System Call Interface

```c
SYSTEM CALL WRAPPER:

User Program:
    |
    | write(fd, buffer, size)
    v
C Library (libc):
    |
    | Wrapper function
    | - Setup parameters
    | - Invoke syscall instruction
    v
System Call Number (e.g., __NR_write = 1)
    |
    v
Kernel Mode:
    |
    | System call handler
    | - Validate parameters
    | - Execute operation
    | - Return result
    v
Return to User Program

EXAMPLE: write() system call

#include <unistd.h>

ssize_t write(int fd, const void *buf, size_t count);

// Returns: number of bytes written, or -1 on error

Usage:
char *message = "Hello, World!\n";
ssize_t bytes_written = write(STDOUT_FILENO, message, strlen(message));

if (bytes_written == -1) {
    perror("write");
    exit(1);
}
```

### Error Handling

```c
ERRNO: Global error variable

#include <errno.h>
#include <string.h>

int fd = open("nonexistent.txt", O_RDONLY);
if (fd == -1) {
    // Check errno to determine error
    printf("Error number: %d\n", errno);
    printf("Error message: %s\n", strerror(errno));
    
    // Or use perror
    perror("open");
    
    // Common error codes:
    // ENOENT (2): No such file or directory
    // EACCES (13): Permission denied
    // EMFILE (24): Too many open files
}

BEST PRACTICES:

1. Always check return values
2. Use perror() or strerror() for error messages
3. Handle errors appropriately (retry, fail, log)
4. Don't ignore EINTR (interrupted system call)

EXAMPLE WITH EINTR:

ssize_t safe_read(int fd, void *buf, size_t count) {
    ssize_t result;
    
    do {
        result = read(fd, buf, count);
    } while (result == -1 && errno == EINTR);
    
    return result;
}
```

---

## Process Management APIs

### Process Creation: fork()

```c
FORK SYSTEM CALL:

#include <unistd.h>
#include <sys/types.h>

pid_t fork(void);

// Returns:
// - Child PID in parent
// - 0 in child
// - -1 on error

EXAMPLE:

#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main() {
    pid_t pid;
    
    printf("Before fork (PID: %d)\n", getpid());
    
    pid = fork();
    
    if (pid < 0) {
        // Fork failed
        perror("fork");
        return 1;
    }
    else if (pid == 0) {
        // Child process
        printf("Child: PID=%d, Parent PID=%d\n", 
               getpid(), getppid());
        printf("Child: Doing child work...\n");
        sleep(2);
        printf("Child: Exiting\n");
        return 0;
    }
    else {
        // Parent process
        printf("Parent: PID=%d, Child PID=%d\n", 
               getpid(), pid);
        printf("Parent: Waiting for child...\n");
        
        int status;
        pid_t child_pid = wait(&status);
        
        if (WIFEXITED(status)) {
            printf("Parent: Child %d exited with status %d\n",
                   child_pid, WEXITSTATUS(status));
        }
    }
    
    return 0;
}

OUTPUT:
Before fork (PID: 1234)
Parent: PID=1234, Child PID=1235
Parent: Waiting for child...
Child: PID=1235, Parent PID=1234
Child: Doing child work...
Child: Exiting
Parent: Child 1235 exited with status 0
```

### Process Execution: exec family

```c
EXEC FAMILY:

#include <unistd.h>

int execl(const char *path, const char *arg, ...);
int execlp(const char *file, const char *arg, ...);
int execle(const char *path, const char *arg, ..., char *envp[]);
int execv(const char *path, char *const argv[]);
int execvp(const char *file, char *const argv[]);
int execve(const char *path, char *const argv[], char *const envp[]);

// All return -1 on error (don't return on success!)

EXAMPLE: Execute ls command

pid_t pid = fork();

if (pid == 0) {
    // Child: replace with ls program
    execl("/bin/ls", "ls", "-l", "/tmp", NULL);
    
    // Only reaches here if exec fails
    perror("execl");
    exit(1);
}
else {
    // Parent: wait for child
    wait(NULL);
    printf("ls command completed\n");
}

EXAMPLE: Execute with environment

char *envp[] = {
    "PATH=/usr/bin:/bin",
    "USER=myuser",
    NULL
};

execle("/bin/sh", "sh", "-c", "echo $USER", NULL, envp);

FORK + EXEC PATTERN:

pid_t pid = fork();

if (pid == 0) {
    // Child: setup and exec
    
    // Redirect stdout to file
    int fd = open("output.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    dup2(fd, STDOUT_FILENO);
    close(fd);
    
    // Execute program
    execl("/bin/date", "date", NULL);
    exit(1);
}
```

### Process Termination and Wait

```c
WAIT FAMILY:

#include <sys/wait.h>

pid_t wait(int *status);
pid_t waitpid(pid_t pid, int *status, int options);
int waitid(idtype_t idtype, id_t id, siginfo_t *infop, int options);

WAIT OPTIONS:

WNOHANG: Return immediately if no child has exited
WUNTRACED: Also return for stopped children
WCONTINUED: Also return for continued children

STATUS MACROS:

WIFEXITED(status): True if child terminated normally
WEXITSTATUS(status): Exit status (if WIFEXITED true)
WIFSIGNALED(status): True if killed by signal
WTERMSIG(status): Signal number (if WIFSIGNALED true)
WIFSTOPPED(status): True if child stopped
WSTOPSIG(status): Stop signal number

EXAMPLE: Wait for specific child

pid_t child_pid = fork();

if (child_pid == 0) {
    sleep(2);
    exit(42);
}

// Wait for specific child
int status;
pid_t pid = waitpid(child_pid, &status, 0);

if (pid == -1) {
    perror("waitpid");
}
else {
    if (WIFEXITED(status)) {
        printf("Child exited with status %d\n", WEXITSTATUS(status));
    }
    else if (WIFSIGNALED(status)) {
        printf("Child killed by signal %d\n", WTERMSIG(status));
    }
}

EXAMPLE: Non-blocking wait

while (1) {
    pid_t pid = waitpid(-1, NULL, WNOHANG);
    
    if (pid == -1) {
        if (errno == ECHILD) {
            // No more children
            break;
        }
        perror("waitpid");
        break;
    }
    else if (pid == 0) {
        // No child has exited yet
        printf("No child ready, doing other work...\n");
        sleep(1);
    }
    else {
        // Child pid exited
        printf("Child %d exited\n", pid);
    }
}
```

---

## File I/O and File Systems

### Low-Level File I/O

```c
FILE OPERATIONS:

#include <fcntl.h>
#include <unistd.h>

int open(const char *pathname, int flags);
int open(const char *pathname, int flags, mode_t mode);
ssize_t read(int fd, void *buf, size_t count);
ssize_t write(int fd, const void *buf, size_t count);
off_t lseek(int fd, off_t offset, int whence);
int close(int fd);

FLAGS:
O_RDONLY: Read only
O_WRONLY: Write only
O_RDWR: Read and write
O_CREAT: Create if doesn't exist
O_TRUNC: Truncate to zero length
O_APPEND: Append mode
O_EXCL: Fail if file exists (with O_CREAT)
O_NONBLOCK: Non-blocking mode

EXAMPLE: Copy file

int copy_file(const char *src, const char *dest) {
    int src_fd, dest_fd;
    ssize_t bytes_read, bytes_written;
    char buffer[4096];
    
    // Open source file
    src_fd = open(src, O_RDONLY);
    if (src_fd == -1) {
        perror("open source");
        return -1;
    }
    
    // Open/create destination file
    dest_fd = open(dest, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (dest_fd == -1) {
        perror("open dest");
        close(src_fd);
        return -1;
    }
    
    // Copy data
    while ((bytes_read = read(src_fd, buffer, sizeof(buffer))) > 0) {
        bytes_written = write(dest_fd, buffer, bytes_read);
        if (bytes_written != bytes_read) {
            perror("write");
            close(src_fd);
            close(dest_fd);
            return -1;
        }
    }
    
    if (bytes_read == -1) {
        perror("read");
        close(src_fd);
        close(dest_fd);
        return -1;
    }
    
    close(src_fd);
    close(dest_fd);
    return 0;
}

EXAMPLE: Random access

int fd = open("data.bin", O_RDWR);

// Seek to byte 1000
off_t offset = lseek(fd, 1000, SEEK_SET);

// Read 100 bytes
char buffer[100];
read(fd, buffer, 100);

// Seek to end
lseek(fd, 0, SEEK_END);

// Write at end
write(fd, "END", 3);

close(fd);
```

### Memory-Mapped Files

```c
MMAP:

#include <sys/mman.h>

void *mmap(void *addr, size_t length, int prot, int flags,
           int fd, off_t offset);
int munmap(void *addr, size_t length);

PROTECTION:
PROT_READ: Read access
PROT_WRITE: Write access
PROT_EXEC: Execute access
PROT_NONE: No access

FLAGS:
MAP_SHARED: Share mapping with other processes
MAP_PRIVATE: Private copy-on-write mapping
MAP_ANONYMOUS: Not backed by file

EXAMPLE: Memory-mapped file I/O

#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>

int main() {
    int fd;
    char *map;
    struct stat sb;
    
    // Open file
    fd = open("data.txt", O_RDWR);
    if (fd == -1) {
        perror("open");
        return 1;
    }
    
    // Get file size
    if (fstat(fd, &sb) == -1) {
        perror("fstat");
        close(fd);
        return 1;
    }
    
    // Map file into memory
    map = mmap(NULL, sb.st_size, PROT_READ | PROT_WRITE,
               MAP_SHARED, fd, 0);
    if (map == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return 1;
    }
    
    // Access file like memory
    for (off_t i = 0; i < sb.st_size; i++) {
        if (map[i] == 'a') {
            map[i] = 'A';  // Modify directly
        }
    }
    
    // Changes automatically written to file
    
    // Cleanup
    munmap(map, sb.st_size);
    close(fd);
    
    return 0;
}

EXAMPLE: Shared memory with mmap

// Create shared memory region
int fd = open("/dev/zero", O_RDWR);
void *shared = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                    MAP_SHARED, fd, 0);
close(fd);

pid_t pid = fork();

if (pid == 0) {
    // Child: write to shared memory
    strcpy(shared, "Hello from child");
    exit(0);
}
else {
    // Parent: wait and read
    wait(NULL);
    printf("Parent read: %s\n", (char *)shared);
    munmap(shared, 4096);
}
```

### File Information

```c
STAT SYSTEM CALLS:

#include <sys/stat.h>

int stat(const char *pathname, struct stat *statbuf);
int fstat(int fd, struct stat *statbuf);
int lstat(const char *pathname, struct stat *statbuf);

STRUCT STAT:

struct stat {
    dev_t     st_dev;      // Device ID
    ino_t     st_ino;      // Inode number
    mode_t    st_mode;     // File type and permissions
    nlink_t   st_nlink;    // Number of hard links
    uid_t     st_uid;      // User ID of owner
    gid_t     st_gid;      // Group ID of owner
    dev_t     st_rdev;     // Device ID (if special file)
    off_t     st_size;     // Total size in bytes
    blksize_t st_blksize;  // Block size for I/O
    blkcnt_t  st_blocks;   // Number of 512B blocks
    time_t    st_atime;    // Last access time
    time_t    st_mtime;    // Last modification time
    time_t    st_ctime;    // Last status change time
};

EXAMPLE: File information

struct stat sb;

if (stat("myfile.txt", &sb) == -1) {
    perror("stat");
    return 1;
}

printf("File size: %lld bytes\n", (long long)sb.st_size);
printf("Inode: %ld\n", (long)sb.st_ino);
printf("Mode: %o\n", sb.st_mode & 0777);

// Check file type
if (S_ISREG(sb.st_mode))  printf("Regular file\n");
if (S_ISDIR(sb.st_mode))  printf("Directory\n");
if (S_ISLNK(sb.st_mode))  printf("Symbolic link\n");
if (S_ISBLK(sb.st_mode))  printf("Block device\n");
if (S_ISCHR(sb.st_mode))  printf("Character device\n");
if (S_ISFIFO(sb.st_mode)) printf("FIFO/pipe\n");
if (S_ISSOCK(sb.st_mode)) printf("Socket\n");

// Check permissions
if (sb.st_mode & S_IRUSR) printf("Owner can read\n");
if (sb.st_mode & S_IWUSR) printf("Owner can write\n");
if (sb.st_mode & S_IXUSR) printf("Owner can execute\n");
```

---

## Inter-Process Communication

### Pipes

```c
PIPE SYSTEM CALL:

#include <unistd.h>

int pipe(int pipefd[2]);
// pipefd[0]: read end
// pipefd[1]: write end

EXAMPLE: Parent-child communication

int main() {
    int pipefd[2];
    pid_t pid;
    char buffer[100];
    
    // Create pipe
    if (pipe(pipefd) == -1) {
        perror("pipe");
        return 1;
    }
    
    pid = fork();
    
    if (pid == 0) {
        // Child: read from pipe
        close(pipefd[1]);  // Close write end
        
        ssize_t bytes = read(pipefd[0], buffer, sizeof(buffer));
        printf("Child read: %s\n", buffer);
        
        close(pipefd[0]);
        exit(0);
    }
    else {
        // Parent: write to pipe
        close(pipefd[0]);  // Close read end
        
        const char *message = "Hello from parent";
        write(pipefd[1], message, strlen(message) + 1);
        
        close(pipefd[1]);
        wait(NULL);
    }
    
    return 0;
}

EXAMPLE: Command pipeline (ls | wc -l)

int main() {
    int pipefd[2];
    
    pipe(pipefd);
    
    if (fork() == 0) {
        // First child: ls
        close(pipefd[0]);           // Close read end
        dup2(pipefd[1], STDOUT_FILENO);  // Redirect stdout to pipe
        close(pipefd[1]);
        
        execlp("ls", "ls", "/tmp", NULL);
        exit(1);
    }
    
    if (fork() == 0) {
        // Second child: wc -l
        close(pipefd[1]);           // Close write end
        dup2(pipefd[0], STDIN_FILENO);   // Redirect stdin from pipe
        close(pipefd[0]);
        
        execlp("wc", "wc", "-l", NULL);
        exit(1);
    }
    
    // Parent: close both ends and wait
    close(pipefd[0]);
    close(pipefd[1]);
    wait(NULL);
    wait(NULL);
    
    return 0;
}
```

### Named Pipes (FIFOs)

```c
NAMED PIPES:

#include <sys/stat.h>

int mkfifo(const char *pathname, mode_t mode);

EXAMPLE: Producer-Consumer with FIFO

// Producer process
int main() {
    const char *fifo = "/tmp/myfifo";
    
    // Create FIFO
    mkfifo(fifo, 0666);
    
    // Open for writing
    int fd = open(fifo, O_WRONLY);
    
    // Write data
    const char *message = "Hello via FIFO";
    write(fd, message, strlen(message) + 1);
    
    close(fd);
    return 0;
}

// Consumer process (separate program)
int main() {
    const char *fifo = "/tmp/myfifo";
    char buffer[100];
    
    // Open for reading
    int fd = open(fifo, O_RDONLY);
    
    // Read data
    read(fd, buffer, sizeof(buffer));
    printf("Received: %s\n", buffer);
    
    close(fd);
    unlink(fifo);  // Remove FIFO
    return 0;
}
```

### System V IPC: Shared Memory

```c
SYSTEM V SHARED MEMORY:

#include <sys/shm.h>

int shmget(key_t key, size_t size, int shmflg);
void *shmat(int shmid, const void *shmaddr, int shmflg);
int shmdt(const void *shmaddr);
int shmctl(int shmid, int cmd, struct shmid_ds *buf);

EXAMPLE: Shared memory communication

// Writer process
int main() {
    key_t key = ftok("myfile", 65);
    
    // Create shared memory segment
    int shmid = shmget(key, 1024, IPC_CREAT | 0666);
    
    // Attach to shared memory
    char *str = (char *)shmat(shmid, NULL, 0);
    
    // Write data
    strcpy(str, "Hello from writer");
    
    printf("Data written: %s\n", str);
    
    // Detach
    shmdt(str);
    
    return 0;
}

// Reader process
int main() {
    key_t key = ftok("myfile", 65);
    
    // Access existing shared memory
    int shmid = shmget(key, 1024, 0666);
    
    // Attach to shared memory
    char *str = (char *)shmat(shmid, NULL, 0);
    
    // Read data
    printf("Data read: %s\n", str);
    
    // Detach
    shmdt(str);
    
    // Destroy shared memory
    shmctl(shmid, IPC_RMID, NULL);
    
    return 0;
}
```

### System V IPC: Semaphores

```c
SYSTEM V SEMAPHORES:

#include <sys/sem.h>

int semget(key_t key, int nsems, int semflg);
int semop(int semid, struct sembuf *sops, size_t nsops);
int semctl(int semid, int semnum, int cmd, ...);

EXAMPLE: Mutual exclusion with semaphore

union semun {
    int val;
    struct semid_ds *buf;
    unsigned short *array;
};

// Initialize semaphore
int init_semaphore(key_t key) {
    int semid = semget(key, 1, IPC_CREAT | 0666);
    
    union semun arg;
    arg.val = 1;  // Initialize to 1 (unlocked)
    semctl(semid, 0, SETVAL, arg);
    
    return semid;
}

// P operation (wait/down)
void sem_wait(int semid) {
    struct sembuf op;
    op.sem_num = 0;
    op.sem_op = -1;  // Decrement
    op.sem_flg = 0;
    semop(semid, &op, 1);
}

// V operation (signal/up)
void sem_signal(int semid) {
    struct sembuf op;
    op.sem_num = 0;
    op.sem_op = 1;  // Increment
    op.sem_flg = 0;
    semop(semid, &op, 1);
}

int main() {
    key_t key = ftok("myfile", 65);
    int semid = init_semaphore(key);
    
    sem_wait(semid);  // Enter critical section
    
    // Critical section
    printf("In critical section\n");
    sleep(2);
    
    sem_signal(semid);  // Exit critical section
    
    return 0;
}
```

---

## Signals and Signal Handling

### Signal Basics

```c
SIGNAL HANDLING:

#include <signal.h>

typedef void (*sighandler_t)(int);
sighandler_t signal(int signum, sighandler_t handler);

COMMON SIGNALS:
SIGINT (2): Interrupt (Ctrl+C)
SIGQUIT (3): Quit (Ctrl+\)
SIGKILL (9): Kill (cannot be caught)
SIGSEGV (11): Segmentation fault
SIGTERM (15): Termination request
SIGCHLD (17): Child process terminated
SIGALRM (14): Alarm clock

EXAMPLE: Basic signal handling

#include <signal.h>
#include <stdio.h>
#include <unistd.h>

void signal_handler(int signum) {
    printf("Caught signal %d\n", signum);
    
    if (signum == SIGINT) {
        printf("Interrupt signal (Ctrl+C)\n");
        exit(0);
    }
}

int main() {
    // Install signal handler
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    printf("Process PID: %d\n", getpid());
    printf("Press Ctrl+C to interrupt\n");
    
    while (1) {
        printf("Working...\n");
        sleep(1);
    }
    
    return 0;
}
```

### Advanced Signal Handling (sigaction)

```c
SIGACTION (Preferred over signal):

#include <signal.h>

int sigaction(int signum, const struct sigaction *act,
              struct sigaction *oldact);

EXAMPLE: Robust signal handling

void handler(int sig, siginfo_t *info, void *context) {
    printf("Signal %d from PID %d\n", sig, info->si_pid);
    
    // Can access additional information
    printf("Signal code: %d\n", info->si_code);
    printf("Signal value: %d\n", info->si_value.sival_int);
}

int main() {
    struct sigaction sa;
    
    // Setup sigaction structure
    sa.sa_flags = SA_SIGINFO;  // Use sa_sigaction instead of sa_handler
    sa.sa_sigaction = handler;
    sigemptyset(&sa.sa_mask);  // Don't block additional signals
    
    // Install handler
    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    printf("PID: %d, waiting for SIGUSR1\n", getpid());
    
    while (1) {
        pause();  // Wait for signal
    }
    
    return 0;
}

// Send signal from another process:
// kill -USR1 <pid>
```

### Signal Sets and Blocking

```c
SIGNAL SETS:

#include <signal.h>

int sigemptyset(sigset_t *set);
int sigfillset(sigset_t *set);
int sigaddset(sigset_t *set, int signum);
int sigdelset(sigset_t *set, int signum);
int sigismember(const sigset_t *set, int signum);

int sigprocmask(int how, const sigset_t *set, sigset_t *oldset);

EXAMPLE: Block signals during critical section

int main() {
    sigset_t newmask, oldmask;
    
    // Initialize signal set
    sigemptyset(&newmask);
    sigaddset(&newmask, SIGINT);
    sigaddset(&newmask, SIGTERM);
    
    // Block signals
    sigprocmask(SIG_BLOCK, &newmask, &oldmask);
    
    // Critical section (signals blocked)
    printf("Signals blocked, doing critical work\n");
    sleep(5);
    
    // Restore original mask
    sigprocmask(SIG_SETMASK, &oldmask, NULL);
    
    printf("Signals unblocked\n");
    
    return 0;
}
```

---

## Multithreading with Pthreads

### Thread Creation and Joining

```c
PTHREAD API:

#include <pthread.h>

int pthread_create(pthread_t *thread, const pthread_attr_t *attr,
                   void *(*start_routine)(void *), void *arg);
int pthread_join(pthread_t thread, void **retval);
void pthread_exit(void *retval);

EXAMPLE: Basic threading

#include <pthread.h>
#include <stdio.h>

void *thread_function(void *arg) {
    int *num = (int *)arg;
    printf("Thread: received %d\n", *num);
    
    // Do work
    sleep(2);
    
    int *result = malloc(sizeof(int));
    *result = *num * 2;
    
    return result;
}

int main() {
    pthread_t thread;
    int arg = 42;
    void *retval;
    
    // Create thread
    if (pthread_create(&thread, NULL, thread_function, &arg) != 0) {
        perror("pthread_create");
        return 1;
    }
    
    printf("Main: thread created\n");
    
    // Wait for thread
    if (pthread_join(thread, &retval) != 0) {
        perror("pthread_join");
        return 1;
    }
    
    int *result = (int *)retval;
    printf("Main: thread returned %d\n", *result);
    free(result);
    
    return 0;
}

// Compile: gcc -pthread program.c
```

### Mutexes

```c
MUTEX (Mutual Exclusion):

#include <pthread.h>

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

int pthread_mutex_init(pthread_mutex_t *mutex,
                       const pthread_mutexattr_t *attr);
int pthread_mutex_lock(pthread_mutex_t *mutex);
int pthread_mutex_trylock(pthread_mutex_t *mutex);
int pthread_mutex_unlock(pthread_mutex_t *mutex);
int pthread_mutex_destroy(pthread_mutex_t *mutex);

EXAMPLE: Shared counter with mutex

#include <pthread.h>
#include <stdio.h>

int counter = 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void *increment_thread(void *arg) {
    for (int i = 0; i < 100000; i++) {
        pthread_mutex_lock(&mutex);
        counter++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

int main() {
    pthread_t threads[10];
    
    // Create threads
    for (int i = 0; i < 10; i++) {
        pthread_create(&threads[i], NULL, increment_thread, NULL);
    }
    
    // Wait for all threads
    for (int i = 0; i < 10; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("Final counter: %d\n", counter);  // Should be 1000000
    
    pthread_mutex_destroy(&mutex);
    return 0;
}
```

### Condition Variables

```c
CONDITION VARIABLES:

pthread_cond_t cond = PTHREAD_COND_INITIALIZER;

int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mutex);
int pthread_cond_signal(pthread_cond_t *cond);
int pthread_cond_broadcast(pthread_cond_t *cond);

EXAMPLE: Producer-Consumer

#include <pthread.h>
#include <stdio.h>

#define BUFFER_SIZE 10

int buffer[BUFFER_SIZE];
int count = 0;
int in = 0, out = 0;

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t not_full = PTHREAD_COND_INITIALIZER;
pthread_cond_t not_empty = PTHREAD_COND_INITIALIZER;

void *producer(void *arg) {
    for (int i = 0; i < 20; i++) {
        pthread_mutex_lock(&mutex);
        
        // Wait while buffer full
        while (count == BUFFER_SIZE) {
            pthread_cond_wait(&not_full, &mutex);
        }
        
        // Produce item
        buffer[in] = i;
        in = (in + 1) % BUFFER_SIZE;
        count++;
        printf("Produced: %d (count=%d)\n", i, count);
        
        // Signal consumer
        pthread_cond_signal(&not_empty);
        
        pthread_mutex_unlock(&mutex);
        usleep(100000);  // Simulate work
    }
    return NULL;
}

void *consumer(void *arg) {
    for (int i = 0; i < 20; i++) {
        pthread_mutex_lock(&mutex);
        
        // Wait while buffer empty
        while (count == 0) {
            pthread_cond_wait(&not_empty, &mutex);
        }
        
        // Consume item
        int item = buffer[out];
        out = (out + 1) % BUFFER_SIZE;
        count--;
        printf("Consumed: %d (count=%d)\n", item, count);
        
        // Signal producer
        pthread_cond_signal(&not_full);
        
        pthread_mutex_unlock(&mutex);
        usleep(150000);  // Simulate work
    }
    return NULL;
}

int main() {
    pthread_t prod, cons;
    
    pthread_create(&prod, NULL, producer, NULL);
    pthread_create(&cons, NULL, consumer, NULL);
    
    pthread_join(prod, NULL);
    pthread_join(cons, NULL);
    
    return 0;
}
```

---

## Memory Management APIs

### Dynamic Memory Allocation

```c
STANDARD ALLOCATION:

#include <stdlib.h>

void *malloc(size_t size);
void *calloc(size_t nmemb, size_t size);
void *realloc(void *ptr, size_t size);
void free(void *ptr);

EXAMPLE: Dynamic array

int *create_array(size_t n) {
    int *arr = malloc(n * sizeof(int));
    if (arr == NULL) {
        return NULL;  // Allocation failed
    }
    
    for (size_t i = 0; i < n; i++) {
        arr[i] = i;
    }
    
    return arr;
}

void resize_array(int **arr, size_t old_size, size_t new_size) {
    int *new_arr = realloc(*arr, new_size * sizeof(int));
    if (new_arr == NULL) {
        // Keep old array, realloc failed
        return;
    }
    
    *arr = new_arr;
    
    // Initialize new elements
    for (size_t i = old_size; i < new_size; i++) {
        (*arr)[i] = 0;
    }
}

int main() {
    size_t size = 10;
    int *arr = create_array(size);
    
    // Use array
    for (size_t i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
    
    // Resize
    resize_array(&arr, size, 20);
    size = 20;
    
    // Free memory
    free(arr);
    
    return 0;
}
```

### Memory Mapping

```c
MMAP FOR ALLOCATION:

// Allocate large chunk
void *mem = mmap(NULL, 1024*1024, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

if (mem == MAP_FAILED) {
    perror("mmap");
    return NULL;
}

// Use memory
memset(mem, 0, 1024*1024);

// Free memory
munmap(mem, 1024*1024);

MEMORY PROTECTION:

// Allocate memory
void *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

// Use memory
strcpy(mem, "Hello");

// Make read-only
mprotect(mem, 4096, PROT_READ);

// This will cause SIGSEGV:
// strcpy(mem, "World");

munmap(mem, 4096);
```

---

## Network Programming

### Socket Basics

```c
SOCKET API:

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int socket(int domain, int type, int protocol);
int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
int listen(int sockfd, int backlog);
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);
int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen);

EXAMPLE: TCP Server

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT 8080
#define BACKLOG 5

int main() {
    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len;
    char buffer[1024];
    
    // Create socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("socket");
        return 1;
    }
    
    // Allow reuse of address
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    // Bind to address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(server_fd, (struct sockaddr *)&server_addr,
             sizeof(server_addr)) == -1) {
        perror("bind");
        close(server_fd);
        return 1;
    }
    
    // Listen for connections
    if (listen(server_fd, BACKLOG) == -1) {
        perror("listen");
        close(server_fd);
        return 1;
    }
    
    printf("Server listening on port %d\n", PORT);
    
    while (1) {
        // Accept connection
        client_len = sizeof(client_addr);
        client_fd = accept(server_fd, (struct sockaddr *)&client_addr,
                          &client_len);
        if (client_fd == -1) {
            perror("accept");
            continue;
        }
        
        printf("Client connected\n");
        
        // Read from client
        ssize_t bytes = read(client_fd, buffer, sizeof(buffer) - 1);
        if (bytes > 0) {
            buffer[bytes] = '\0';
            printf("Received: %s\n", buffer);
            
            // Echo back
            write(client_fd, buffer, bytes);
        }
        
        close(client_fd);
    }
    
    close(server_fd);
    return 0;
}

EXAMPLE: TCP Client

int main() {
    int sockfd;
    struct sockaddr_in server_addr;
    char *message = "Hello, Server!";
    char buffer[1024];
    
    // Create socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd == -1) {
        perror("socket");
        return 1;
    }
    
    // Connect to server
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);
    
    if (connect(sockfd, (struct sockaddr *)&server_addr,
                sizeof(server_addr)) == -1) {
        perror("connect");
        close(sockfd);
        return 1;
    }
    
    printf("Connected to server\n");
    
    // Send data
    write(sockfd, message, strlen(message));
    
    // Receive response
    ssize_t bytes = read(sockfd, buffer, sizeof(buffer) - 1);
    if (bytes > 0) {
        buffer[bytes] = '\0';
        printf("Server response: %s\n", buffer);
    }
    
    close(sockfd);
    return 0;
}
```

---

## Summary

- **POSIX API**: Standard interface for system programming
- **Process APIs**: fork, exec, wait for process management
- **File I/O**: Low-level file operations, memory-mapped files
- **IPC**: Pipes, FIFOs, shared memory, semaphores
- **Signals**: Asynchronous event handling
- **Pthreads**: Multithreading with mutexes and condition variables
- **Memory**: Dynamic allocation, memory mapping
- **Networking**: Socket programming for client-server applications

System programming requires careful error handling and understanding of underlying OS concepts!

---

**Next Topics:**
- Performance Tuning and Monitoring
- Debugging and Troubleshooting
- Network Stack Deep Dive

