# Operating Systems - Boot Process and System Initialization

## Table of Contents
1. [Boot Sequence Overview](#boot-sequence-overview)
2. [BIOS vs UEFI](#bios-vs-uefi)
3. [Boot Loaders](#boot-loaders)
4. [Kernel Initialization](#kernel-initialization)
5. [Init Systems](#init-systems)
6. [Service Management](#service-management)
7. [Boot Troubleshooting](#boot-troubleshooting)

---

## Boot Sequence Overview

### Complete Boot Process

```
BOOT SEQUENCE:

Power On
    ↓
+------------------+
| 1. Firmware      |
|    (BIOS/UEFI)   |
|    - POST        |
|    - Find boot   |
|      device      |
+------------------+
    ↓
+------------------+
| 2. Boot Loader   |
|    (GRUB/LILO)   |
|    - Load kernel |
|    - Load initrd |
+------------------+
    ↓
+------------------+
| 3. Kernel        |
|    - Initialize  |
|    - Mount root  |
|    - Start init  |
+------------------+
    ↓
+------------------+
| 4. Init Process  |
|    (systemd/     |
|     SysVinit)    |
|    - Mount fs    |
|    - Start svcs  |
+------------------+
    ↓
+------------------+
| 5. User Space    |
|    - Login       |
|    - Desktop     |
+------------------+

Timeline (typical):
0-1s:   Firmware (BIOS/UEFI)
1-2s:   Boot loader (GRUB)
2-5s:   Kernel initialization
5-10s:  Init system (systemd)
10-15s: Services start
15s+:   Login prompt/Desktop
```

---

## BIOS vs UEFI

### BIOS (Basic Input/Output System)

```
BIOS ARCHITECTURE:

+------------------+
| ROM Chip         |
| (on motherboard) |
| - Boot code      |
| - Setup utility  |
| - Hardware tests |
+------------------+

BOOT PROCESS:

1. Power On Self Test (POST):
   - Test RAM
   - Detect hardware
   - Initialize devices

2. Read Master Boot Record (MBR):
   Location: First 512 bytes of disk
   
   MBR Structure:
   +------------------+  0-445:  Boot code
   | Boot Code        |  446-509: Partition table (4 entries)
   | (446 bytes)      |  510-511: Magic number (0x55AA)
   +------------------+
   | Partition Table  |
   | (64 bytes)       |
   +------------------+
   | Magic Number     |
   | (2 bytes: 0x55AA)|
   +------------------+

3. Execute boot code
4. Boot code loads boot loader

LIMITATIONS:

- 16-bit real mode
- 1 MB addressable memory
- MBR limited to 2 TB disks
- Only 4 primary partitions
- Slow initialization
- No secure boot

PARTITION TABLE:

Entry 1: Type=0x83 (Linux), Start=2048, Size=1048576
Entry 2: Type=0x82 (Swap), Start=1050624, Size=4194304
Entry 3: Empty
Entry 4: Empty

$ sudo fdisk -l /dev/sda

Device     Boot  Start      End     Sectors Size Id Type
/dev/sda1        2048   1050623    1048576 512M 83 Linux
/dev/sda2     1050624   5244927    4194304   2G 82 Linux swap
```

### UEFI (Unified Extensible Firmware Interface)

```
UEFI ARCHITECTURE:

+------------------+
| UEFI Firmware    |
| - Boot Manager   |
| - Drivers        |
| - Shell          |
| - Secure Boot    |
+------------------+

FEATURES:

- 32-bit or 64-bit
- GPT partition scheme
- Support > 2 TB disks
- Secure Boot
- Network boot
- Graphical interface
- Faster boot
- Mouse support

GPT (GUID Partition Table):

+------------------+  Sector 0: Protective MBR
| Protective MBR   |  Sector 1: Primary GPT header
+------------------+  Sectors 2-33: Partition entries
| Primary GPT      |  
| Header           |  (128 partitions possible)
+------------------+
| Partition Entry  |  At end: Backup GPT
| Array            |  (for redundancy)
+------------------+
| Partitions       |
|                  |
+------------------+
| Backup GPT       |
| Entry Array      |
+------------------+
| Backup GPT       |
| Header           |
+------------------+

$ sudo gdisk -l /dev/sda

Number  Start      End        Size    Code  Name
1       2048       1050623    512M    EF00  EFI System
2       1050624    5244927    2G      8300  Linux filesystem
3       5244928    9439231    2G      8200  Linux swap

UEFI BOOT PROCESS:

1. UEFI firmware initializes
2. Read GPT
3. Find EFI System Partition (ESP)
   - FAT32 partition
   - Contains boot loaders
   
   ESP Layout:
   /boot/efi/
   ├── EFI/
   │   ├── BOOT/
   │   │   └── BOOTX64.EFI  (fallback)
   │   ├── ubuntu/
   │   │   └── grubx64.efi  (GRUB)
   │   └── Microsoft/
   │       └── Boot/
   │           └── bootmgfw.efi  (Windows)

4. Execute boot loader from ESP
5. Boot loader loads kernel

SECURE BOOT:

Only signed boot loaders can execute

1. UEFI has certificate database
2. Boot loader must be signed
3. Signature verified before execution
4. If invalid → Boot blocked

$ mokutil --sb-state
SecureBoot enabled

$ mokutil --list-enrolled
Certificate details...
```

---

## Boot Loaders

### GRUB 2 (GRand Unified Bootloader)

```
GRUB STRUCTURE:

Stage 1: Boot sector (MBR or GPT)
    ↓
Stage 1.5: Core image
    ↓
Stage 2: /boot/grub/ (full GRUB)

GRUB FILES:

/boot/grub/
├── grub.cfg          # Main configuration
├── grubenv           # Environment variables
├── i386-pc/          # BIOS modules
├── x86_64-efi/       # UEFI modules
└── fonts/            # Fonts

GRUB CONFIGURATION:

/etc/default/grub:

GRUB_TIMEOUT=5
GRUB_DEFAULT=0
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""

Generate config:
$ sudo update-grub
or
$ sudo grub-mkconfig -o /boot/grub/grub.cfg

/boot/grub/grub.cfg (generated):

menuentry 'Ubuntu' {
    insmod gzio
    insmod part_gpt
    insmod ext2
    set root='hd0,gpt2'
    linux /boot/vmlinuz-5.15.0 root=/dev/sda2 ro quiet splash
    initrd /boot/initrd.img-5.15.0
}

menuentry 'Ubuntu (recovery mode)' {
    linux /boot/vmlinuz-5.15.0 root=/dev/sda2 ro single
    initrd /boot/initrd.img-5.15.0
}

KERNEL PARAMETERS:

Common parameters:
- root=/dev/sda2       : Root filesystem
- ro                   : Mount root read-only initially
- quiet                : Less verbose output
- splash               : Show splash screen
- single               : Boot to single-user mode
- init=/bin/bash       : Use alternate init
- nomodeset            : Disable kernel mode setting
- acpi=off             : Disable ACPI
- mem=4G               : Limit memory

Edit at boot:
1. Select entry in GRUB menu
2. Press 'e' to edit
3. Modify linux line
4. Ctrl+X to boot

GRUB RESCUE:

If GRUB config broken:

grub> ls
(hd0) (hd0,gpt1) (hd0,gpt2)

grub> set root=(hd0,gpt2)
grub> linux /boot/vmlinuz-5.15.0 root=/dev/sda2
grub> initrd /boot/initrd.img-5.15.0
grub> boot

After boot:
$ sudo update-grub
$ sudo grub-install /dev/sda
```

### initrd/initramfs

```
INITIAL RAM DISK:

Purpose:
- Temporary root filesystem
- Contains drivers needed to mount real root
- Handles early boot tasks

Why needed:
- Root filesystem may be on:
  - RAID
  - LVM
  - Encrypted partition
  - Network (NFS)
- Kernel can't include all drivers
- initrd has necessary drivers

Contents:
$ lsinitramfs /boot/initrd.img-5.15.0

bin/
├── busybox
├── mount
└── sh
etc/
├── fstab
└── modules/
lib/
├── modules/
│   └── 5.15.0/
│       ├── kernel/
│       │   ├── drivers/
│       │   └── fs/
scripts/
├── init-top/
├── init-premount/
└── local-top/

BOOT PROCESS WITH INITRD:

1. GRUB loads kernel + initrd into memory
2. Kernel initializes
3. Kernel extracts initrd to RAM
4. Kernel executes /init in initrd
5. initrd /init:
   - Load necessary drivers
   - Assemble RAID/LVM
   - Mount encrypted partition
   - Find real root filesystem
   - Switch root to real filesystem
6. Execute real init (/sbin/init)

Switch root:
# In initrd
mount /dev/sda2 /root
exec switch_root /root /sbin/init

CREATE CUSTOM INITRD:

Ubuntu/Debian:
$ sudo update-initramfs -u

RHEL/CentOS:
$ sudo dracut --force

Add module:
$ echo "dm-crypt" >> /etc/initramfs-tools/modules
$ sudo update-initramfs -u
```

---

## Kernel Initialization

### Kernel Boot Process

```
KERNEL INITIALIZATION SEQUENCE:

1. Kernel loaded into memory by boot loader
2. Decompress kernel (if compressed)
3. Start_kernel() function:

start_kernel() {
    setup_arch();           // Architecture-specific setup
    setup_per_cpu_areas();  // Per-CPU data
    sched_init();           // Scheduler
    console_init();         // Console
    mem_init();             // Memory management
    kmem_cache_init();      // Slab allocator
    fork_init();            // Process management
    vfs_caches_init();      // VFS
    ...
}

4. Initialize devices
5. Mount initramfs
6. Execute /init
7. Switch to real root
8. Execute /sbin/init (PID 1)

KERNEL MESSAGES:

$ dmesg

[    0.000000] Linux version 5.15.0 (gcc version 11.2.0)
[    0.000000] Command line: root=/dev/sda2 ro quiet splash
[    0.000000] x86/fpu: x87 FPU will use FXSAVE
[    0.000000] BIOS-provided physical RAM map:
[    0.000000] BIOS-e820: [mem 0x0000000000000000-0x000000000009fbff] usable
[    0.001000] setup_percpu: NR_CPUS:8192 nr_cpumask_bits:4
[    0.001234] Built 1 zonelists, mobility grouping on
[    0.002345] Kernel command line: root=/dev/sda2 ro quiet splash
[    0.010000] Dentry cache hash table entries: 262144
[    0.015000] Inode-cache hash table entries: 131072
[    0.020000] Memory: 4039548K/4194304K available
[    0.100000] NR_IRQS: 524544, nr_irqs: 1024
[    0.150000] Console: colour VGA+ 80x25
[    0.200000] smpboot: Allowing 4 CPUs, 0 hotplug CPUs
[    0.300000] PCI: Using configuration type 1
[    0.400000] clocksource: tsc: mask: 0xffffffffffffffff
[    1.000000] Freeing unused kernel memory: 2048K
[    1.234567] systemd[1]: systemd 245 running

Timestamps: Seconds since boot
```

### Device Discovery

```
DEVICE INITIALIZATION:

1. PCI Bus Scan:
   - Enumerate PCI devices
   - Load drivers

$ lspci
00:00.0 Host bridge: Intel Corporation Device
00:02.0 VGA compatible controller: Intel Corporation
00:14.0 USB controller: Intel Corporation
00:1f.0 ISA bridge: Intel Corporation
00:1f.2 SATA controller: Intel Corporation
00:1f.3 SMBus: Intel Corporation

2. USB Scan:
   - Detect USB devices
   - Load drivers

$ lsusb
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation USB 2.0
Bus 001 Device 002: ID 8087:0024 Intel Corp. USB Hub
Bus 001 Device 003: ID 046d:c52b Logitech Mouse

3. Storage Devices:
   - Detect disks
   - Create /dev entries

$ ls /dev/sd*
/dev/sda  /dev/sda1  /dev/sda2  /dev/sdb

4. Network Interfaces:
   - Initialize NICs
   - Assign names

$ ip link
1: lo: <LOOPBACK,UP> mtu 65536
2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500

UDEV (Device Manager):

Rules: /etc/udev/rules.d/
Example: 70-persistent-net.rules

SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", 
ATTR{address}=="00:1a:2b:3c:4d:5e", NAME="eth0"

Device naming:
- eth0, eth1: Ethernet (old style)
- enp3s0: Ethernet, PCI bus 3, slot 0 (new predictable names)
- wlp2s0: Wireless, PCI bus 2, slot 0
```

---

## Init Systems

### SysV Init

```
SYSV INIT (Traditional):

Runlevels:
0: Halt
1: Single-user mode (maintenance)
2: Multi-user without networking
3: Multi-user with networking
4: Unused
5: Multi-user with GUI
6: Reboot

Runlevel directories:
/etc/rc0.d/  (halt)
/etc/rc1.d/  (single-user)
...
/etc/rc5.d/  (GUI)
/etc/rc6.d/  (reboot)

Scripts:
/etc/rc3.d/
├── S01networking  → /etc/init.d/networking
├── S02ssh         → /etc/init.d/ssh
├── S03apache2     → /etc/init.d/apache2
└── K01apache2     → /etc/init.d/apache2

S##name: Start script (## = order)
K##name: Kill script

Current runlevel:
$ runlevel
N 3

Change runlevel:
$ sudo init 5

INIT SCRIPT EXAMPLE:

/etc/init.d/myservice:

#!/bin/bash
### BEGIN INIT INFO
# Provides:          myservice
# Required-Start:    $network
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

case "$1" in
  start)
    echo "Starting myservice"
    /usr/bin/myservice &
    ;;
  stop)
    echo "Stopping myservice"
    pkill myservice
    ;;
  restart)
    $0 stop
    $0 start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
    ;;
esac

Enable:
$ sudo update-rc.d myservice defaults

Disadvantages:
- Sequential startup (slow)
- Scripts can be complex
- No dependency management
- No automatic restart
```

### systemd

```
SYSTEMD (Modern):

Units instead of scripts:
- .service: Service units
- .socket: Socket units
- .device: Device units
- .mount: Mount points
- .target: Groups of units

Unit files:
/lib/systemd/system/      (system units)
/etc/systemd/system/      (admin units, override)
~/.config/systemd/user/   (user units)

SERVICE UNIT EXAMPLE:

/etc/systemd/system/myapp.service:

[Unit]
Description=My Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=myuser
Group=mygroup
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Type:
- simple: Main process (default)
- forking: Daemonizes
- oneshot: Exits after completion
- notify: Uses sd_notify()

COMMANDS:

# Start service
$ sudo systemctl start myapp.service

# Stop service
$ sudo systemctl stop myapp.service

# Restart service
$ sudo systemctl restart myapp.service

# Reload config
$ sudo systemctl reload myapp.service

# Enable (start at boot)
$ sudo systemctl enable myapp.service

# Disable
$ sudo systemctl disable myapp.service

# Status
$ sudo systemctl status myapp.service

● myapp.service - My Application
   Loaded: loaded (/etc/systemd/system/myapp.service; enabled)
   Active: active (running) since Wed 2024-01-15 10:00:00
 Main PID: 1234 (myapp)
   CGroup: /system.slice/myapp.service
           └─1234 /opt/myapp/bin/myapp

# View logs
$ journalctl -u myapp.service
$ journalctl -u myapp.service -f  (follow)

# List all services
$ systemctl list-units --type=service

# List failed services
$ systemctl --failed

TARGETS (like runlevels):

poweroff.target     (runlevel 0)
rescue.target       (runlevel 1)
multi-user.target   (runlevel 3)
graphical.target    (runlevel 5)
reboot.target       (runlevel 6)

# Change target
$ sudo systemctl isolate multi-user.target

# Set default target
$ sudo systemctl set-default graphical.target

DEPENDENCIES:

After=network.target
Requires=postgresql.service
Wants=redis.service

Ordering:
- Before: Start before
- After: Start after

Dependencies:
- Requires: Hard dependency (fails if dep fails)
- Wants: Soft dependency (starts anyway)
- Conflicts: Cannot run together

SOCKET ACTIVATION:

myapp.socket:
[Socket]
ListenStream=8080

myapp.service:
[Service]
ExecStart=/opt/myapp/bin/myapp

Benefit: Service starts only when connection arrives
```

---

## Service Management

### Managing Services

```bash
SYSTEMCTL COMMANDS:

# Service control
$ sudo systemctl start nginx
$ sudo systemctl stop nginx
$ sudo systemctl restart nginx
$ sudo systemctl reload nginx  (reload config without restart)

# Enable/disable at boot
$ sudo systemctl enable nginx
Created symlink /etc/systemd/system/multi-user.target.wants/nginx.service

$ sudo systemctl disable nginx

# Check status
$ systemctl status nginx
$ systemctl is-active nginx
$ systemctl is-enabled nginx
$ systemctl is-failed nginx

# View dependencies
$ systemctl list-dependencies nginx

# Mask (prevent from starting)
$ sudo systemctl mask nginx
$ sudo systemctl unmask nginx

# Edit unit file
$ sudo systemctl edit nginx  (creates override)
$ sudo systemctl edit --full nginx  (edits actual file)

# Reload systemd
$ sudo systemctl daemon-reload

SERVICE LOGS:

# View logs
$ journalctl -u nginx
$ journalctl -u nginx -f  (follow)
$ journalctl -u nginx --since today
$ journalctl -u nginx --since "2024-01-15 10:00"
$ journalctl -u nginx -n 50  (last 50 lines)
$ journalctl -u nginx -p err  (errors only)

# All services
$ journalctl -b  (this boot)
$ journalctl -b -1  (previous boot)
$ journalctl --list-boots
```

---

## Boot Troubleshooting

### Common Boot Problems

```
GRUB NOT FOUND:

Error: "No bootable device"

Fix:
1. Boot from live USB
2. Mount root partition:
   $ sudo mount /dev/sda2 /mnt
   $ sudo mount /dev/sda1 /mnt/boot/efi  (if UEFI)

3. Chroot:
   $ sudo mount --bind /dev /mnt/dev
   $ sudo mount --bind /proc /mnt/proc
   $ sudo mount --bind /sys /mnt/sys
   $ sudo chroot /mnt

4. Reinstall GRUB:
   $ grub-install /dev/sda  (BIOS)
   $ grub-install --target=x86_64-efi --efi-directory=/boot/efi  (UEFI)
   $ update-grub

5. Reboot

KERNEL PANIC:

Error: "Kernel panic - not syncing: VFS: Unable to mount root fs"

Causes:
- Wrong root= parameter
- Missing drivers in initrd
- Corrupted filesystem

Fix:
1. Boot with recovery kernel
2. Or edit GRUB entry:
   Change: root=/dev/sda2
   To: root=/dev/sdb2  (if disk changed)

3. Rebuild initrd:
   $ sudo update-initramfs -u -k all

INIT SYSTEM FAILURE:

Error: Service fails to start

Debug:
$ systemctl status myservice
$ journalctl -u myservice
$ journalctl -xe  (recent errors)

Common issues:
- Missing dependencies
- Permission problems
- Configuration errors

EMERGENCY MODE:

Add to kernel parameters:
systemd.unit=emergency.target

Or:
systemd.unit=rescue.target

Single-user mode (root shell):
Add: single
Or: init=/bin/bash

FILESYSTEM CHECK:

Force fsck on next boot:
$ sudo touch /forcefsck
$ sudo reboot

Or specify in fstab:
/dev/sda2 / ext4 defaults 0 1
                              ↑
                         Pass number (1 or 2 = check)
```

---

## Summary

- **Boot sequence**: Firmware → Boot loader → Kernel → Init → Services
- **BIOS**: Legacy, MBR, limited features
- **UEFI**: Modern, GPT, secure boot, faster
- **GRUB**: Flexible boot loader, supports multiple OSes
- **initrd**: Temporary root FS for early boot
- **Kernel**: Initializes hardware, mounts root, starts init
- **systemd**: Modern init system with parallel startup
- **Services**: Managed via systemctl, logged via journalctl
- **Troubleshooting**: GRUB rescue, kernel parameters, emergency mode

Understanding boot process essential for system administration!

---

## Complete Operating Systems Tutorial Finished!

Congratulations! You now have comprehensive documentation covering all aspects of operating systems from fundamentals to advanced topics, with practical examples and detailed diagrams.

