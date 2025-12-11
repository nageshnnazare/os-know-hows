# Operating Systems - Network Stack Deep Dive

## Table of Contents
1. [Network Stack Architecture](#network-stack-architecture)
2. [Network Layers](#network-layers)
3. [Socket Layer](#socket-layer)
4. [TCP Implementation](#tcp-implementation)
5. [IP Layer](#ip-layer)
6. [Network Device Drivers](#network-device-drivers)
7. [Network Performance](#network-performance)

---

## Network Stack Architecture

### Linux Network Stack

```
APPLICATION LAYER
+----------------------------------+
| User Space Applications          |
| (Web browser, SSH, etc.)         |
+----------------------------------+
       ↓ System calls (socket API)
+----------------------------------+
| Socket Layer                     |
| - Socket buffers                 |
| - Socket options                 |
+----------------------------------+
       ↓
+----------------------------------+
| Transport Layer                  |
| - TCP (connection-oriented)      |
| - UDP (connectionless)           |
+----------------------------------+
       ↓
+----------------------------------+
| Network Layer                    |
| - IP (routing, fragmentation)    |
| - ICMP (error reporting)         |
+----------------------------------+
       ↓
+----------------------------------+
| Data Link Layer                  |
| - Ethernet, WiFi drivers         |
| - ARP (address resolution)       |
+----------------------------------+
       ↓
+----------------------------------+
| Physical Layer                   |
| - Network Interface Card (NIC)   |
+----------------------------------+
```

### Packet Flow

```
SENDING PACKET:

Application
    ↓ write()/send()
Socket Buffer
    ↓
TCP Layer
    ↓ Add TCP header
IP Layer
    ↓ Add IP header
Ethernet Layer
    ↓ Add Ethernet header
NIC Driver
    ↓ DMA transfer
Network Interface Card
    ↓
Wire


RECEIVING PACKET:

Wire
    ↓
Network Interface Card
    ↓ Interrupt
NIC Driver
    ↓ DMA transfer
Receive Ring Buffer
    ↓ Software interrupt (NAPI)
Ethernet Layer
    ↓ Remove Ethernet header
IP Layer
    ↓ Remove IP header, routing
TCP Layer
    ↓ Remove TCP header, reassembly
Socket Buffer
    ↓
Application
    ↓ read()/recv()


PACKET STRUCTURE:

+------------------+
| Ethernet Header  | 14 bytes
|  - Dest MAC      | 6 bytes
|  - Source MAC    | 6 bytes
|  - Type          | 2 bytes
+------------------+
| IP Header        | 20+ bytes
|  - Version       |
|  - Length        |
|  - TTL           |
|  - Protocol      |
|  - Addresses     |
+------------------+
| TCP Header       | 20+ bytes
|  - Source Port   | 2 bytes
|  - Dest Port     | 2 bytes
|  - Seq Number    | 4 bytes
|  - Ack Number    | 4 bytes
|  - Flags         |
|  - Window Size   |
+------------------+
| Data (Payload)   | Up to 1460 bytes (typical)
+------------------+
| Ethernet FCS     | 4 bytes (Frame Check Sequence)
+------------------+

Total: ~1518 bytes max (standard Ethernet frame)
```

---

## Network Layers

### Layer 2: Data Link (Ethernet)

```
ETHERNET FRAME:

Preamble (7 bytes) + SFD (1 byte)
+--------+--------+------+------+-----+-----+
|Dest MAC|Src MAC |Type  | Data | ... | FCS |
+--------+--------+------+------+-----+-----+
 6 bytes  6 bytes 2 bytes         4 bytes

MAC ADDRESS: 48-bit (6 bytes)
Example: 00:1A:2B:3C:4D:5E

Types:
- 0x0800: IPv4
- 0x0806: ARP
- 0x86DD: IPv6

ARP (Address Resolution Protocol):

Who has IP 192.168.1.1? Tell 192.168.1.100

ARP Request (broadcast):
Dest MAC: FF:FF:FF:FF:FF:FF (broadcast)
Src MAC: AA:BB:CC:DD:EE:FF
Type: ARP
Data: Who has 192.168.1.1?

ARP Reply (unicast):
Dest MAC: AA:BB:CC:DD:EE:FF
Src MAC: 11:22:33:44:55:66
Type: ARP
Data: 192.168.1.1 is at 11:22:33:44:55:66

ARP CACHE:

$ arp -n
Address          HWtype  HWaddress           Flags Mask  Iface
192.168.1.1      ether   11:22:33:44:55:66   C           eth0
192.168.1.100    ether   AA:BB:CC:DD:EE:FF   C           eth0

Timeout: Usually 60-120 seconds
```

### Layer 3: Network (IP)

```
IP HEADER (IPv4):

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Key fields:
- Version: 4 (IPv4)
- Protocol: 6 (TCP), 17 (UDP), 1 (ICMP)
- TTL: Hop limit (decremented at each router)
- Source/Dest Address: 32-bit IP addresses

ROUTING:

Routing Table:
$ ip route show
default via 192.168.1.1 dev eth0
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
10.0.0.0/8 via 192.168.1.254 dev eth0

Routing decision:
Packet to 192.168.1.50:
  → Matches 192.168.1.0/24
  → Send directly on eth0

Packet to 10.1.2.3:
  → Matches 10.0.0.0/8
  → Send via gateway 192.168.1.254

Packet to 8.8.8.8:
  → Matches default
  → Send via gateway 192.168.1.1

IP FORWARDING:

$ cat /proc/sys/net/ipv4/ip_forward
0  (disabled)

$ sudo sysctl net.ipv4.ip_forward=1
(Enable to act as router)

FRAGMENTATION:

MTU (Maximum Transmission Unit): 1500 bytes (Ethernet)

Large packet (3000 bytes):
Fragment 1: 0-1480 bytes (MF flag set)
Fragment 2: 1480-2960 bytes (MF flag set)
Fragment 3: 2960-3000 bytes (MF flag clear)

Reassembly at destination
```

### Layer 4: Transport (TCP/UDP)

```
TCP HEADER:

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |           |U|A|P|R|S|F|                               |
| Offset| Reserved  |R|C|S|S|Y|I|            Window             |
|       |           |G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Flags:
- SYN: Synchronize (connection establishment)
- ACK: Acknowledgment
- FIN: Finish (connection termination)
- RST: Reset (abort connection)
- PSH: Push (deliver immediately)
- URG: Urgent

UDP HEADER (simpler):

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

No connection state
No reliability
Fast and simple
```

---

## Socket Layer

### Socket Types

```
SOCKET TYPES:

SOCK_STREAM (TCP):
- Connection-oriented
- Reliable, ordered delivery
- Byte stream
- Example: HTTP, SSH

SOCK_DGRAM (UDP):
- Connectionless
- Unreliable, unordered
- Message-oriented
- Example: DNS, DHCP

SOCK_RAW:
- Raw IP packets
- Custom protocols
- Requires root
- Example: ping, traceroute

SOCKET STATES (TCP):

CLOSED → LISTEN → SYN_SENT → ESTABLISHED → FIN_WAIT_1
  ↑                                             ↓
  |                                        FIN_WAIT_2
  |                                             ↓
  +---------------------------------------- TIME_WAIT
                                                ↓
                                             CLOSED

$ ss -tan
State      Recv-Q Send-Q Local:Port  Peer:Port
ESTAB      0      0      192.168.1.100:22  192.168.1.1:54321
TIME_WAIT  0      0      192.168.1.100:80  192.168.1.50:12345
LISTEN     0      128    0.0.0.0:22        0.0.0.0:*
```

### Socket Buffers

```
SOCKET BUFFERS:

Send Buffer:
Application → write() → Send Buffer → TCP → Network

+------------------+
| Send Buffer      |
|  ┌──────────────┐|
|  │ Unsent Data  ││ → TCP sends when possible
|  └──────────────┘|
| Size: SO_SNDBUF  |
+------------------+

Receive Buffer:
Network → TCP → Receive Buffer → read() → Application

+------------------+
| Receive Buffer   |
|  ┌──────────────┐|
|  │ Received Data││ ← TCP stores here
|  └──────────────┘|
| Size: SO_RCVBUF  |
+------------------+

Buffer Sizes:
$ cat /proc/sys/net/core/rmem_default
212992  (default receive)

$ cat /proc/sys/net/core/wmem_default
212992  (default send)

$ cat /proc/sys/net/core/rmem_max
212992  (max receive)

Set per-socket:
setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size));

FLOW CONTROL:

Sender:
Can send up to: min(congestion window, receive window)

Receiver:
Advertises receive window in TCP header
Window = Buffer space available

Example:
Buffer: 64 KB
Data in buffer: 16 KB
Advertised window: 48 KB

Sender can send up to 48 KB more
```

---

## TCP Implementation

### Three-Way Handshake

```
CONNECTION ESTABLISHMENT:

Client                          Server
  |                               |
  | SYN (seq=1000)                |
  +------------------------------>|
  |                               | (Server allocates resources)
  | SYN-ACK (seq=5000, ack=1001)  |
  |<------------------------------+
  |                               |
  | ACK (seq=1001, ack=5001)      |
  +------------------------------>|
  |                               |
  | Connection established        |
  

PARAMETERS NEGOTIATED:

- Initial sequence numbers (ISN)
- Maximum segment size (MSS)
- Window scale option
- SACK (Selective Acknowledgment)

$ tcpdump -i eth0 port 80
1. SYN:     seq=1000, win=65535, mss=1460
2. SYN-ACK: seq=5000, ack=1001, win=29200, mss=1460
3. ACK:     seq=1001, ack=5001

MSS = MTU - IP header - TCP header
    = 1500 - 20 - 20 = 1460 bytes
```

### Data Transfer

```
RELIABLE DELIVERY:

Sender                          Receiver
  |                               |
  | Data (seq=1000, len=100)      |
  +------------------------------>|
  |                               |
  |         ACK (ack=1100)        |
  |<------------------------------+
  |                               |
  | Data (seq=1100, len=100)      |
  +------------------------------>| Packet lost!
  |                               | (timeout)
  |         ACK (ack=1100)        |
  |<------------------------------+ (Duplicate ACK)
  |                               |
  | Data (seq=1100, len=100)      |
  +------------------------------>| (Retransmission)
  |                               |
  |         ACK (ack=1200)        |
  |<------------------------------+

SLIDING WINDOW:

Window Size: 4 packets

Sent & ACKed: [1][2][3][4] [5][6][7][8] [ ][ ][ ][ ]
                          ↑ Window
                          Can send packets 5-8

After ACK for 5,6:
Sent & ACKed: [1][2][3][4][5][6] [7][8][9][10] [ ][ ]
                                ↑ Window
                                Can send packets 7-10

CONGESTION CONTROL:

Slow Start:
cwnd = 1 MSS
For each ACK: cwnd += 1 MSS

Timeline:
RTT 1: Send 1 packet  → cwnd = 2
RTT 2: Send 2 packets → cwnd = 4
RTT 3: Send 4 packets → cwnd = 8
...

Exponential growth until ssthresh

Congestion Avoidance:
cwnd >= ssthresh
For each RTT: cwnd += 1 MSS

Linear growth

Fast Retransmit/Recovery:
3 duplicate ACKs:
- Retransmit lost packet
- ssthresh = cwnd / 2
- cwnd = ssthresh + 3

Graph:
cwnd
  |           /\
  |          /  \     /
  |         /    \   /
  |        /      \ /
  |       /        X Loss
  |      /
  +-------------------> Time
     Slow  Cong.  Fast
     Start Avoid. Recov.
```

### Connection Termination

```
GRACEFUL CLOSE:

Client                          Server
  |                               |
  | FIN (seq=1000)                |
  +------------------------------>|
  |                               |
  |         ACK (ack=1001)        |
  |<------------------------------+
  |                               |
  |         FIN (seq=5000)        |
  |<------------------------------+
  |                               |
  | ACK (ack=5001)                |
  +------------------------------>|
  |                               |
  | TIME_WAIT (2 × MSL)           |
  
TIME_WAIT: Ensures all packets cleared (typically 60s)

ABORTIVE CLOSE:

Client                          Server
  |                               |
  | RST                           |
  +------------------------------>|
  |                               |
  | Connection immediately closed |

Causes:
- Port not listening
- Connection timeout
- Application error
```

---

## IP Layer

### IP Routing

```
ROUTING DECISION PROCESS:

1. Destination IP: 192.168.1.50

2. Check routing table (longest prefix match):

Destination     Gateway         Netmask         Interface
192.168.1.0     0.0.0.0         255.255.255.0   eth0
10.0.0.0        192.168.1.254   255.0.0.0       eth0
0.0.0.0         192.168.1.1     0.0.0.0         eth0

3. Match 192.168.1.0/24 (direct route)

4. Send on eth0 (local delivery)

5. ARP for destination MAC address

6. Build Ethernet frame and send

EXAMPLE: Packet to internet

Destination: 8.8.8.8

No specific route → Use default (0.0.0.0)
Gateway: 192.168.1.1
ARP for gateway MAC
Send packet to gateway

Gateway forwards based on its routing table

ROUTING PROTOCOLS:

Static routes:
$ sudo ip route add 10.20.0.0/16 via 192.168.1.254

Dynamic protocols:
- RIP (Routing Information Protocol)
- OSPF (Open Shortest Path First)
- BGP (Border Gateway Protocol)
```

### NAT (Network Address Translation)

```
NAT OPERATION:

Private Network         NAT Router              Internet
192.168.1.100:12345 → 203.0.113.1:54321 → 8.8.8.8:53

NAT Table:
Internal            External
192.168.1.100:12345 → 203.0.113.1:54321

Outgoing:
Src: 192.168.1.100:12345 → 203.0.113.1:54321
Dst: 8.8.8.8:53

Incoming:
Src: 8.8.8.8:53
Dst: 203.0.113.1:54321 → 192.168.1.100:12345

PORT FORWARDING:

External:80 → Internal:192.168.1.10:80

$ sudo iptables -t nat -A PREROUTING -p tcp --dport 80 \
  -j DNAT --to-destination 192.168.1.10:80

Allows external access to internal server
```

---

## Network Device Drivers

### Interrupt Handling

```
PACKET RECEPTION:

1. Packet arrives at NIC
2. NIC writes packet to ring buffer (DMA)
3. NIC raises interrupt
4. Interrupt handler:
   - Disable NIC interrupts
   - Schedule softirq (NAPI)
   - Return
5. Softirq (NAPI):
   - Poll packets from ring buffer
   - Process multiple packets (batching)
   - Pass to network stack
   - Re-enable NIC interrupts

NAPI (New API):

Traditional: Interrupt per packet (high overhead)
NAPI: Interrupt → Poll mode (efficient under load)

Rx Ring Buffer:
+---+---+---+---+---+---+---+---+
| P | P | P | E | E | E | E | E |
+---+---+---+---+---+---+---+---+
  ↑
  Head (next packet to process)

P = Packet
E = Empty

$ ethtool -g eth0
Ring parameters for eth0:
Pre-set maximums:
RX:        4096
TX:        4096
Current hardware settings:
RX:        512
TX:        512

Increase for high-traffic systems
```

### Network Card Offloading

```
OFFLOADING FEATURES:

TSO (TCP Segmentation Offload):
Large TCP packet → NIC segments into MSS-sized packets

Without TSO:
CPU: Split 64KB into 44 × 1460 byte packets

With TSO:
CPU: Pass 64KB to NIC
NIC: Split into 44 packets

$ ethtool -k eth0 | grep tcp-segmentation
tcp-segmentation-offload: on

GRO (Generic Receive Offload):
NIC: Combine multiple packets into one large packet
CPU: Process once instead of N times

Checksum Offload:
NIC calculates/verifies checksums (not CPU)

$ ethtool -K eth0 tso on
$ ethtool -K eth0 gro on
$ ethtool -K eth0 rx on tx on

Benefits:
- Reduced CPU usage
- Higher throughput
- Lower latency
```

---

## Network Performance

### Performance Monitoring

```bash
BANDWIDTH:

$ sar -n DEV 1

IFACE   rxpck/s txpck/s rxkB/s txkB/s
eth0    1500    1200    2000   800

Metrics:
- rxpck/s: Received packets/second
- txpck/s: Transmitted packets/second  
- rxkB/s: Received KB/second
- txkB/s: Transmitted KB/second

ERRORS:

$ netstat -i

Iface   RX-OK RX-ERR RX-DRP TX-OK TX-ERR TX-DRP
eth0    1000   0      0      800   0      0

Watch for:
- RX-ERR: Receive errors (bad hardware?)
- RX-DRP: Receive drops (buffer overflow?)
- TX-ERR: Transmit errors

CONNECTION STATES:

$ ss -tan state established | wc -l
500  (established connections)

$ ss -tan state time-wait | wc -l
2000  (connections in TIME_WAIT)

Too many TIME_WAIT may indicate:
- High connection rate
- Need to tune tcp_tw_reuse
```

### Performance Tuning

```bash
TCP TUNING:

# Increase buffers
$ sudo sysctl -w net.core.rmem_max=16777216
$ sudo sysctl -w net.core.wmem_max=16777216
$ sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 16777216'
$ sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 16777216'

# Enable window scaling
$ sudo sysctl -w net.ipv4.tcp_window_scaling=1

# Enable SACK
$ sudo sysctl -w net.ipv4.tcp_sack=1

# Increase connection backlog
$ sudo sysctl -w net.core.somaxconn=4096
$ sudo sysctl -w net.ipv4.tcp_max_syn_backlog=8192

# Reduce TIME_WAIT
$ sudo sysctl -w net.ipv4.tcp_fin_timeout=15
$ sudo sysctl -w net.ipv4.tcp_tw_reuse=1

# Use better congestion control
$ sudo sysctl -w net.ipv4.tcp_congestion_control=bbr

NIC TUNING:

# Increase ring buffers
$ sudo ethtool -G eth0 rx 4096 tx 4096

# Enable offloading
$ sudo ethtool -K eth0 tso on gro on gso on

# Set MTU (if supported)
$ sudo ip link set eth0 mtu 9000

# Multiple queues (RSS)
$ sudo ethtool -L eth0 combined 4

FIREWALL OPTIMIZATION:

# Connection tracking table size
$ sudo sysctl -w net.netfilter.nf_conntrack_max=262144

# Timeout values
$ sudo sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600
```

---

## Summary

- **Stack**: Application → Socket → Transport → Network → Link → Physical
- **Layers**: Each layer adds header, opposite removes on receive
- **TCP**: Reliable, connection-oriented, flow control, congestion control
- **UDP**: Unreliable, connectionless, fast, simple
- **IP**: Routing, fragmentation, addressing
- **Sockets**: API between application and network stack
- **Drivers**: DMA, interrupts, NAPI for efficiency
- **Performance**: Buffer tuning, offloading, connection management

Network stack is complex but well-layered for modularity!

---

**Next: Boot Process**

