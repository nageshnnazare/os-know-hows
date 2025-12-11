# Operating Systems - Security and Protection

## Table of Contents
1. [Security Goals](#security-goals)
2. [Authentication](#authentication)
3. [Access Control](#access-control)
4. [Cryptography](#cryptography)
5. [Security Threats](#security-threats)
6. [Protection Mechanisms](#protection-mechanisms)
7. [Security in Modern Systems](#security-in-modern-systems)

---

## Security Goals

### CIA Triad

```
+------------------+
|                  |
|  CONFIDENTIALITY |  Only authorized users can access data
|                  |
+--------+---------+
         |
    +----+----+
    |         |
+---v---+ +---v---+
|       | |       |
|INTEGR-| |AVAILA-|
| ITY   | |BILITY |
|       | |       |
+-------+ +-------+
  Data      System
 accuracy   accessible

CONFIDENTIALITY:
  Information disclosed only to authorized parties
  
  Example: Medical records, financial data
  Violation: Data breach, eavesdropping

INTEGRITY:
  Data not altered by unauthorized parties
  
  Example: Financial transactions
  Violation: Data tampering, man-in-the-middle

AVAILABILITY:
  System accessible when needed
  
  Example: Banking system uptime
  Violation: DoS attacks, system crashes
```

### Additional Security Goals

```
AUTHENTICATION:
  Verify identity of user/system
  
  Who are you?
  User → [Username + Password] → System
       ← [Granted/Denied]

AUTHORIZATION:
  What can you do?
  
  User (authenticated) → Request resource
                      → Check permissions
                      → Grant/Deny access

NON-REPUDIATION:
  Cannot deny action
  
  Digital signatures
  Audit logs
  
  Example: Email sent with digital signature
           Sender cannot deny sending it

ACCOUNTABILITY:
  Track actions to specific users
  
  Audit trail:
  2024-01-15 10:30 - User alice deleted file.txt
  2024-01-15 10:35 - User bob accessed database
```

---

## Authentication

### Authentication Factors

```
THREE FACTORS:

1. SOMETHING YOU KNOW:
   +----------------+
   | Password       |
   | PIN            |
   | Security Q&A   |
   +----------------+

2. SOMETHING YOU HAVE:
   +----------------+
   | Smart card     |
   | Security token |
   | Phone (2FA)    |
   +----------------+

3. SOMETHING YOU ARE:
   +----------------+
   | Fingerprint    |
   | Iris scan      |
   | Face           |
   | Voice          |
   +----------------+

MULTI-FACTOR AUTHENTICATION (MFA):
Combine 2+ factors

Example: Banking
1. Password (know)
2. SMS code to phone (have)

Stronger than single factor!
```

### Password Security

```
PASSWORD STORAGE:

BAD: Plain text
+-------+------------+
| User  | Password   |
+-------+------------+
| alice | secret123  |
| bob   | mypass     |
+-------+------------+

Breach = All passwords compromised!

BETTER: Hash
+-------+--------------------------------+
| User  | Hash(Password)                 |
+-------+--------------------------------+
| alice | 5f4dcc3b5aa765d61d8327deb882cf99 |
| bob   | 8621ffdbc5698829397d97767ac13db3 |
+-------+--------------------------------+

One-way function
Cannot reverse hash to get password

BEST: Salt + Hash
+-------+------+--------------------------------+
| User  | Salt | Hash(Salt + Password)          |
+-------+------+--------------------------------+
| alice | x7a9 | 7a3f9b2c8d4e5f6a1b2c3d4e5f6a7b |
| bob   | k2m5 | 9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a |
+-------+------+--------------------------------+

Salt: Random value per user
Prevents rainbow table attacks
Even same password has different hash

VERIFICATION:

User login: alice / secret123

1. Retrieve alice's salt: x7a9
2. Compute: Hash(x7a9 + secret123)
3. Compare with stored hash
4. Match → Allow login

PASSWORD POLICY:

Requirements:
- Minimum length (8-12+ characters)
- Mix of uppercase, lowercase, numbers, symbols
- Not based on dictionary words
- Regular changes (controversial)
- No reuse of recent passwords

Example:
Good: Tr0ub4dor&3
Bad: password, 123456, alice123
```

### Biometric Authentication

```
PROCESS:

1. ENROLLMENT:
   User → Scan fingerprint → Extract features
        → Store template in database

2. AUTHENTICATION:
   User → Scan fingerprint → Extract features
        → Compare with stored template
        → Match? Grant access

BIOMETRIC TEMPLATE:
Not the actual fingerprint image!
Mathematical representation of unique features

Fingerprint:          Template:
    _____           [0.234, 0.891, 0.456, ...]
   /     \          (Feature vector)
  |   O   |
  | /   \ |
  ||     ||

ACCURACY METRICS:

False Acceptance Rate (FAR):
  Unauthorized user accepted
  Security risk

False Rejection Rate (FRR):
  Authorized user rejected
  Usability issue

Equal Error Rate (EER):
  Point where FAR = FRR
  Lower EER = Better system

Graph:
Rate
  |
  |  FAR \
  |       \
  |         X  ← EER
  |        /
  |   FRR/
  |
  +-------------> Threshold

Adjust threshold for security vs. usability
```

---

## Access Control

### Access Control Models

```
1. DISCRETIONARY ACCESS CONTROL (DAC):

Owner controls access to their resources

Example: UNIX file permissions

File: report.txt
Owner: alice
Permissions: rwxr-x---
             ↑  ↑  ↑
           Owner Group Others
           
alice: Read, Write, Execute
Group: Read, Execute
Others: No access

Access Control List (ACL):
+--------+-----------+
| User   | Permission|
+--------+-----------+
| alice  | RWX       |
| bob    | RX        |
| carol  | R         |
+--------+-----------+

Flexible but:
- Difficult to manage at scale
- Owner can grant access to anyone
- Hard to enforce system-wide policies


2. MANDATORY ACCESS CONTROL (MAC):

System enforces access based on security labels

Security Levels:
Top Secret > Secret > Confidential > Unclassified

User Clearance:     Document Classification:
Alice: Secret       Doc1: Confidential ✓ (can access)
Bob: Confidential   Doc2: Secret ✗ (cannot access)

Rules:
- No read up (cannot read higher classification)
- No write down (cannot write to lower classification)

Bell-LaPadula Model:
  Focus: Confidentiality
  
  +-----------+    Can read    +-----------+
  | Level 3   |<---------------|           |
  +-----------+                |   User    |
  | Level 2   |<---------------|  Level 2  |
  +-----------+   Cannot read  |           |
  | Level 1   |                +-----------+
  +-----------+

Biba Model:
  Focus: Integrity
  Opposite of Bell-LaPadula


3. ROLE-BASED ACCESS CONTROL (RBAC):

Permissions assigned to roles, users assigned to roles

ROLES:
+----------+     +----------+     +----------+
| Doctor   |     | Nurse    |     | Admin    |
+----------+     +----------+     +----------+
     |               |                 |
     +---------------+-----------------+
                     |
              PERMISSIONS
              +----------------+
              | Read patients  |
              | Write patients |
              | Delete patients|
              +----------------+

Example:
Alice → Doctor → Can read/write patient records
Bob → Nurse → Can read patient records
Carol → Admin → Can delete records

Advantages:
+ Easier to manage
+ Reflects organizational structure
+ Separation of duties
```

### Access Control Matrix

```
CONCEPT:

        Objects (Files)
        F1    F2    F3
      +----+----+----+
Users P1| RW | R  | RWX|
      +----+----+----+
      P2| R  | RW | -- |
      +----+----+----+
      P3| -- | R  | R  |
      +----+----+----+

IMPLEMENTATION:

1. Access Control List (by column):
   F1: {P1: RW, P2: R}
   F2: {P1: R, P2: RW, P3: R}
   F3: {P1: RWX, P3: R}
   
   Stored with each object
   Good for: "Who can access this file?"

2. Capability List (by row):
   P1: {F1: RW, F2: R, F3: RWX}
   P2: {F1: R, F2: RW}
   P3: {F2: R, F3: R}
   
   Stored with each subject
   Good for: "What can this user access?"

UNIX IMPLEMENTATION:

Simplified 3-bit model per category:

File: /home/alice/doc.txt
-rw-r--r-- alice staff doc.txt

- : Regular file
rw- : Owner (alice) can read, write
r-- : Group (staff) can read
r-- : Others can read

Permission bits:
r (Read)    = 4
w (Write)   = 2
x (Execute) = 1

chmod 644 doc.txt
6 = 4+2   = rw- (owner)
4 = 4     = r-- (group)
4 = 4     = r-- (others)

Special bits:
SUID (Set User ID): Execute as file owner
SGID (Set Group ID): Execute as file group
Sticky: Only owner can delete (for directories)
```

---

## Cryptography

### Symmetric Encryption

```
CONCEPT:
Same key for encryption and decryption

Plaintext → [Encrypt with Key K] → Ciphertext
Ciphertext → [Decrypt with Key K] → Plaintext

EXAMPLE: Caesar Cipher

Key = 3 (shift by 3)
Plaintext:  HELLO
Ciphertext: KHOOR

H → K (shift 3)
E → H
L → O
L → O
O → R

MODERN: AES (Advanced Encryption Standard)

Key sizes: 128, 192, 256 bits

Process:
Message + Key → AES Encryption → Ciphertext
Ciphertext + Key → AES Decryption → Message

PROS:
+ Fast
+ Efficient

CONS:
- Key distribution problem (how to share key securely?)
- Need different key for each pair of users

N users → N(N-1)/2 keys needed!

100 users → 4,950 keys!
```

### Asymmetric Encryption

```
CONCEPT:
Public key (encryption) + Private key (decryption)

Key Pair Generation:
     +-----------------+
     | Key Pair        |
     +-----------------+
     | Public Key      | (Share with everyone)
     | Private Key     | (Keep secret)
     +-----------------+

ENCRYPTION:

Alice → Bob

1. Alice gets Bob's public key
2. Alice encrypts with Bob's public key
3. Send ciphertext to Bob
4. Bob decrypts with his private key

Message → [Encrypt: Bob's Public] → Ciphertext
Ciphertext → [Decrypt: Bob's Private] → Message

DIGITAL SIGNATURE:

Prove message authenticity

Alice signs message:
1. Hash message
2. Encrypt hash with Alice's private key (signature)
3. Send message + signature

Bob verifies:
1. Hash received message
2. Decrypt signature with Alice's public key
3. Compare hashes
4. Match → Authentic from Alice

Workflow:
Message → [Hash] → Hash Value
              ↓
         [Encrypt with Alice's Private Key]
              ↓
          Signature
              
Verification:
Signature → [Decrypt with Alice's Public Key] → Hash1
Message → [Hash] → Hash2
Compare Hash1 == Hash2? → Verified!

COMMON ALGORITHMS:

RSA (Rivest-Shamir-Adleman):
- Key sizes: 2048, 4096 bits
- Based on factorization problem

ECC (Elliptic Curve Cryptography):
- Shorter keys (256 bit ≈ 3072 bit RSA)
- Faster
- Modern choice

PROS:
+ Solves key distribution
+ Digital signatures
+ N users → N key pairs (not N²)

CONS:
- Slower than symmetric
- More complex

HYBRID APPROACH:

Most systems use both:

1. Asymmetric: Exchange session key
2. Symmetric: Encrypt actual data with session key

Example: TLS/HTTPS

Client → Server:
1. Exchange keys (RSA/ECC)
2. Establish session key (AES key)
3. Communicate with AES
```

### Hashing

```
CONCEPT:
One-way function: Message → Fixed-size hash

Properties:
1. Deterministic: Same input → Same hash
2. Fast to compute
3. Infeasible to reverse
4. Small change → Completely different hash
5. Collision-resistant

EXAMPLE:

Message 1: "Hello"
Hash: 5d41402abc4b2a76b9719d911017c592

Message 2: "hello" (lowercase 'h')
Hash: 5d41402abc4b2a76b9719d911017c593
       ↑ Different!

COMMON ALGORITHMS:

MD5: 128 bits (deprecated, broken)
SHA-1: 160 bits (deprecated, broken)
SHA-256: 256 bits (current standard)
SHA-512: 512 bits (more secure)

USES:

1. Password storage (as discussed)

2. Data integrity:
   Download file + hash
   Compute hash of downloaded file
   Compare hashes
   Match → File intact

   File: linux.iso (4 GB)
   SHA-256: a3f5b8...1c2d

3. Digital signatures (as discussed)

4. Blockchain:
   Block N: [Data + Hash of Block N-1]
   Tamper Block 5 → Hash changes
                 → Block 6 invalid
                 → Chain broken
```

---

## Security Threats

### Types of Attacks

```
1. MALWARE:

VIRUS:
  Infects files, replicates
  Needs host program
  
  Clean File: [Program Code]
  Infected:   [Program Code][Virus Code]

WORM:
  Self-replicating, spreads over network
  No host needed
  
  Computer A → [Worm] → Computer B
                     → Computer C
                     → ...

TROJAN HORSE:
  Appears legitimate, hides malicious code
  
  "Free Game.exe"
  [Game Code] + [Backdoor Code]

RANSOMWARE:
  Encrypts data, demands payment
  
  Your Files → [Encrypted] → Pay Bitcoin to decrypt

SPYWARE:
  Steals information
  Keylogger, screen capture, etc.


2. NETWORK ATTACKS:

EAVESDROPPING:
  Intercept network traffic
  
  Alice → [Message] → Eve (intercepts) → Bob

MAN-IN-THE-MIDDLE:
  Attacker between two parties
  
  Alice → Attacker → Bob
       ← Attacker ←

DENIAL OF SERVICE (DoS):
  Overwhelm system with requests
  
  Attackers → [Flood] → Server (overwhelmed)
           → Can't serve legitimate users

DISTRIBUTED DoS (DDoS):
  Multiple attackers (botnet)
  
  Bot 1 ----+
  Bot 2 ----+--→ [Flood] → Server
  Bot 3 ----+
  Bot N ----+


3. PRIVILEGE ESCALATION:

Gain higher privileges than authorized

Example:
Normal User → [Exploit] → Root/Admin

Buffer Overflow:
  void vulnerable(char *input) {
    char buffer[100];
    strcpy(buffer, input); // No bounds check!
  }
  
  Input: [100 bytes of data][Return address overwrite]
         → Hijack control flow
         → Execute attacker's code


4. SOCIAL ENGINEERING:

Manipulate people, not systems

PHISHING:
  Fake email pretending to be legitimate
  
  "Your bank account is locked! Click here:"
  → Fake website
  → Steal credentials

PRETEXTING:
  Create scenario to extract information
  
  "Hi, I'm from IT. What's your password?"

BAITING:
  Leave infected USB drive
  User plugs in → Compromised


5. SIDE-CHANNEL ATTACKS:

Extract information from physical implementation

TIMING ATTACK:
  Measure time to decrypt
  Infer key bits

POWER ANALYSIS:
  Measure power consumption
  Deduce operations

Example: Spectre/Meltdown
  Exploit CPU speculative execution
  Read privileged memory
```

### Security Vulnerabilities

```
COMMON VULNERABILITIES:

1. BUFFER OVERFLOW:
   Write beyond buffer bounds
   Overwrite return address
   Execute arbitrary code

2. SQL INJECTION:
   Malicious SQL in input
   
   Username: admin' --
   Query: SELECT * FROM users 
          WHERE name='admin' --' AND pass='...'
          (Comment out password check!)

3. CROSS-SITE SCRIPTING (XSS):
   Inject malicious script in web page
   
   Comment: <script>steal_cookies()</script>

4. RACE CONDITIONS:
   Time-of-check to time-of-use gap
   
   T0: Check if user can access file
   T1: [ATTACKER CHANGES FILE]
   T2: Access file
   
   TOCTOU vulnerability

5. INSECURE DEFAULTS:
   Default password (admin/admin)
   Unnecessary services enabled
   Weak configurations
```

---

## Protection Mechanisms

### Sandboxing

```
CONCEPT:
Isolate program in restricted environment

+----------------------------------+
|        Operating System          |
|                                  |
|  +----------------------------+  |
|  | Sandbox                    |  |
|  |                            |  |
|  | +-----------------------+  |  |
|  | | Untrusted Application|  |  |
|  | +-----------------------+  |  |
|  |                            |  |
|  | Restricted Access:         |  |
|  | - Limited file access      |  |
|  | - No network (or limited)  |  |
|  | - Can't install software   |  |
|  +----------------------------+  |
+----------------------------------+

IMPLEMENTATIONS:

1. Virtual Machines:
   Full OS isolation
   
2. Containers:
   OS-level isolation
   Docker, LXC
   
3. Language-level:
   Java VM, JavaScript in browser

BROWSER SANDBOX:
Web page runs in sandbox
Cannot access:
- Local files
- Other tabs
- System resources

If exploited, damage contained
```

### Principle of Least Privilege

```
CONCEPT:
Give minimum permissions needed

BAD:
User runs all programs as root/admin

GOOD:
User runs with minimal permissions
Escalate only when necessary

EXAMPLE:

Web Server:
- Runs as 'www-data' user (not root)
- Can only access /var/www/
- Cannot modify system files

If compromised:
- Attacker has limited access
- Cannot take over system

IMPLEMENTATION:

1. Separate accounts for different tasks
2. Use sudo/UAC for admin tasks
3. Drop privileges after startup
4. Capability-based security
```

### Address Space Layout Randomization (ASLR)

```
CONCEPT:
Randomize memory addresses

WITHOUT ASLR:
Stack:   Always at 0xFFFF0000
Heap:    Always at 0x08048000
Library: Always at 0xB7E00000

Attacker knows where to jump!

WITH ASLR:
Run 1:
  Stack:   0xFFE12000
  Heap:    0x09A53000
  Library: 0xB7F45000

Run 2:
  Stack:   0xFF987000
  Heap:    0x08F21000
  Library: 0xB7A32000

Attacker cannot predict addresses
Exploits much harder!

COMBINED WITH:
- NX (No-Execute): Stack/heap not executable
- Stack Canaries: Detect buffer overflows

Defense in depth!
```

### Intrusion Detection Systems (IDS)

```
TYPES:

1. SIGNATURE-BASED:
   Detect known attack patterns
   
   Database of attack signatures
   Match network traffic/system calls
   
   Pros: Fast, accurate for known attacks
   Cons: Cannot detect new attacks

2. ANOMALY-BASED:
   Detect deviations from normal
   
   Learn normal behavior
   Flag unusual activity
   
   Pros: Can detect new attacks
   Cons: False positives

DEPLOYMENT:

NETWORK IDS (NIDS):
  Monitor network traffic
  
  Internet → [Firewall] → [NIDS] → Internal Network

HOST IDS (HIDS):
  Monitor single host
  System calls, logs, file integrity
  
  Host → HIDS Agent → Central Console

RESPONSE:

1. Alert administrator
2. Log event
3. Block traffic (IPS - Intrusion Prevention)
4. Quarantine host
```

---

## Security in Modern Systems

### Virtualization Security

```
HYPERVISOR ISOLATION:

+------------------------------------------+
| Hardware                                 |
+------------------------------------------+
| Hypervisor (Type 1 / Type 2)             |
+------------------------------------------+
|  VM1      |  VM2      |  VM3             |
|  [OS]     |  [OS]     |  [OS]            |
|  [Apps]   |  [Apps]   |  [Apps]          |
+------------------------------------------+

Each VM isolated
VM1 cannot access VM2's memory

SECURITY BENEFITS:
+ Isolation
+ Easier backup/restore
+ Snapshots for recovery
+ Testing in isolated environment

RISKS:
- Hypervisor vulnerabilities
- VM escape (break out of VM)
- Resource sharing (side channels)
```

### Trusted Platform Module (TPM)

```
HARDWARE SECURITY MODULE:

+------------------+
| CPU              |
+------------------+
         ↓
+------------------+
| TPM Chip         |
| - Secure storage |
| - Crypto keys    |
| - Random numbers |
+------------------+

MEASURED BOOT:

1. BIOS measures itself → TPM
2. Bootloader measured → TPM
3. OS kernel measured → TPM
4. Each component verified before execution

Tampered component → Different hash → Boot fails

FULL DISK ENCRYPTION:

Encryption key stored in TPM
Released only if:
- Correct boot sequence
- Correct platform state
- User authenticated

Prevents:
- Booting from USB to bypass security
- Removing disk to another system
```

### Secure Enclaves

```
CONCEPT:
Isolated execution environment within CPU

Intel SGX (Software Guard Extensions):

+------------------------------+
| CPU                          |
|                              |
| Normal Execution             |
|                              |
| +--------------------------+ |
| | Enclave                  | |
| | - Isolated memory        | |
| | - Encrypted              | |
| | - Even OS cannot access  | |
| +--------------------------+ |
+------------------------------+

USE CASES:
- Digital Rights Management (DRM)
- Secure authentication
- Cryptocurrency wallets
- Confidential computing

Application:
Sensitive code/data in enclave
Even if OS compromised, enclave secure
```

### Security Updates

```
PATCH MANAGEMENT:

+------------------+
| Vendor discovers |
| vulnerability    |
+------------------+
         ↓
+------------------+
| Develop patch    |
+------------------+
         ↓
+------------------+
| Test patch       |
+------------------+
         ↓
+------------------+
| Release update   |
+------------------+
         ↓
+------------------+
| User installs    |
+------------------+

CHALLENGES:

1. Zero-day: Exploited before patch available
2. Patch compatibility: May break systems
3. User delay: Not installing updates
4. Legacy systems: Cannot be patched

BEST PRACTICES:
- Automatic updates (for critical security)
- Test in staging before production
- Have rollback plan
- Maintain inventory of systems
```

---

## Security Best Practices

```
DEFENSE IN DEPTH:

Multiple layers of security:

+----------------------------------+
| Physical Security (locks, cameras)
+----------------------------------+
| Perimeter (firewall)             |
+----------------------------------+
| Network (IDS/IPS)                |
+----------------------------------+
| Host (antivirus, HIDS)           |
+----------------------------------+
| Application (input validation)   |
+----------------------------------+
| Data (encryption)                |
+----------------------------------+

One layer fails → Others still protect

SECURITY POLICIES:

1. Password Policy
   - Complexity requirements
   - Change frequency
   - No sharing

2. Access Control Policy
   - Least privilege
   - Role-based access
   - Regular review

3. Acceptable Use Policy
   - What users can/cannot do
   - Personal use limits
   - Consequences

4. Incident Response Plan
   - How to detect incidents
   - Who to notify
   - Recovery procedures

REGULAR ACTIVITIES:

1. Backups (3-2-1 rule):
   - 3 copies
   - 2 different media
   - 1 off-site

2. Audits:
   - Log review
   - Access review
   - Vulnerability scans

3. Training:
   - Security awareness
   - Phishing tests
   - Incident reporting

4. Testing:
   - Penetration testing
   - Disaster recovery drills
   - Backup restoration tests
```

---

## Summary

- **Security Goals**: CIA Triad (Confidentiality, Integrity, Availability)
- **Authentication**: Password, biometric, multi-factor
- **Access Control**: DAC, MAC, RBAC models
- **Cryptography**: Symmetric, asymmetric, hashing
- **Threats**: Malware, network attacks, social engineering
- **Protection**: Sandboxing, least privilege, ASLR, IDS
- **Modern Security**: TPM, secure enclaves, virtualization isolation
- **Best Practices**: Defense in depth, regular updates, training

Security is an ongoing process, not a one-time implementation!

---

**Next Topic:**
- Advanced Operating System Concepts

