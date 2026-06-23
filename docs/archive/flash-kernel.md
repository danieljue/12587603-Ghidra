# PCM Hammer Flash Kernel — Architecture Reference

> Source: `f:/github/PcmHammer/Kernels/68k-VPW-Asm/Kernel.S` (1,452 lines) + `Common-Assembly.h` (121 lines)
> Authors: Antus, Gampy (pcmhacking.net) · 2018-2026

---

## Memory-Mapped Registers (P01/P59)

### J1850 VPW Communication (MC68HC58 DLC)
| Register | Address | Purpose |
|----------|---------|---------|
| J1850_Config | 0xFFF600 | DLC configuration |
| J1850_Command | 0xFFF60C | BTAD byte type + destination |
| J1850_TX_FIFO | 0xFFF60D | Transmit data byte |
| J1850_Status | 0xFFF60E | RFS (receive) + TMFS (transmit) status |
| J1850_RX_FIFO | 0xFFF60F | Receive data byte |

### Watchdog (COP)
| Register | Address | Reset Sequence |
|----------|---------|---------------|
| COP1 | 0xFFFA27 | Write 0x55 then 0xAA |
| COP2 | 0xFFD006 | Toggle bit 7 (XOR 0x80) |

### System Integration Module (Flash Control)
| Register | Address | Purpose |
|----------|---------|---------|
| SIM_CSBARBT | 0xFA48 | Boot block chip select base address |
| SIM_CSORBT | 0xFA4A | Boot block chip select options |
| SIM_CSBAR0 | 0xFA4C | Main flash chip select base address |
| SIM_CSOR0 | 0xFA4E | Main flash chip select options |

### Flash Programming Voltage
| Register | Address | Purpose |
|----------|---------|---------|
| HARDWARE_IO | 0xE2FA | VPP (12V programming voltage) control — P01/P59 |

---

## VPW Protocol — Kernel Command Set

### Kernel Main Loop Flow
```
1. Wait for VPW packet with destination ID 0x10 (PCM ID)
2. Read mode byte from message
3. Dispatch to mode handler
4. Send response
5. Loop
```

### Mode $3D — Kernel Functions (sub-mode in byte after mode)

| Sub-mode | Function | Request | Response |
|----------|----------|---------|----------|
| 0x00 | Kernel ID | — | 10 bytes: version, build timestamp, PCM type |
| 0x01 | Flash ID | — | 9 bytes: manufacturer + flash chip ID |
| 0x02 | CRC | address + length | 15 bytes: CRC32 of range |
| 0x03 | OSID | — | 9 bytes: OSID from flash |
| 0x05 | Erase Sector | sector address | 7 bytes: status |
| 0x06 | Detect IAC | — | 8 bytes: IAC driver chip present? (P01/P59 only) |

### Mode $34 — Download Request
Tool requests permission to send N bytes to address A.
```
Tool → PCM: 6C F0 10 34 00 <len2> <len1> <addr3> <addr2> <addr1>
PCM → Tool: 6C F0 10 74 00 44 (success) or 7F (error)
```

### Mode $35 — Upload Request
Tool requests PCM to read N bytes from address A.
```
Tool → PCM: 6C F0 10 35 <len> <addr3> <addr2> <addr1>
PCM → Tool: 6C F0 10 75 <submode> <data...> <checksum2> <checksum1>
```

### Mode $36 — Data Transfer
Tool sends data bytes to write (after $34 handshake).
```
Tool → PCM: 6C F0 10 36 <data...> <checksum2> <checksum1>
PCM → Tool: 6C F0 10 76 00 00 (success)
```

### Mode $20 — Halt Kernel
Resets the PCM, returns to normal operation.
```
Tool → PCM: 6C F0 10 20
PCM → Tool: 6C F0 10 60
PCM then executes RESET instruction → watchdog timeout → reboot
```

---

## Flash Chip Detection

### Intel Detection (0x0089)
1. Write 0x9090 to address 0 → read manufacturer ID
2. Read word at address 2 → flash device ID
3. Write 0xFFFF to address 0 → return to read array mode

### AMD Detection (0x0001)
1. Write 0xAAAA to 0xAAA, 0x5555 to 0x554 → unlock
2. Write 0x9090 to 0xAAA → autoselect
3. Read address 0 → manufacturer ID, address 2 → device ID
4. Write 0xF0F0 → reset

---

## P59 Flash Sector Layout (Intel 28F800B — 1MB)

| Sector | Start | End | Size | Purpose |
|--------|-------|-----|------|---------|
| 0 | 0x000000 | 0x003FFF | 16 KB | Boot vectors — ⚠️ DO NOT ERASE |
| 1 | 0x004000 | 0x005FFF | 8 KB | Parameter block — 🔴 FREE |
| 2 | 0x006000 | 0x007FFF | 8 KB | Parameter — mostly 🔴 FREE |
| 3 | 0x008000 | 0x01FFFF | 96 KB | OS boot code |
| 4 | 0x020000 | 0x03FFFF | 128 KB | OS code |
| 5 | 0x040000 | 0x05FFFF | 128 KB | OS code |
| 6 | 0x060000 | 0x07FFFF | 128 KB | OS code |
| 7 | 0x080000 | 0x09FFFF | 128 KB | OS + calibration (last blocks free) |
| 8 | 0x0A0000 | 0x0BFFFF | 128 KB | Calibration + free |
| 9 | 0x0C0000 | 0x0DFFFF | 128 KB | 🔴 FREE |
| 10 | 0x0E0000 | 0x0FFFFF | 128 KB | 🔴 FREE |

**SAFE SECTORS FOR CUSTOM CODE**: Sectors 9-10 (256 KB), plus the tail ends of sectors 7-8.

---

## Key Addresses in Flash

| Address | Content |
|---------|---------|
| 0x000000-0x000003 | Initial SSP (0x00FFCE00 for P59) |
| 0x000004-0x000007 | Initial PC / reset vector (0x00000440) |
| 0x000504 | OSID location (reads 4 bytes) |
| 0xFF8000 | Kernel load address (P01/P59) |

---

## Watchdog Reset Sequence
```asm
ResetWatchdog:
    move.b  #0x55, (COP1).l    ; COP1 = 0xFFFA27
    move.b  #0xAA, (COP1).l    
    eori.b  #0x80, (COP2).l    ; COP2 = 0xFFD006, toggle bit 7
    rts
```

---

## VPW Message Format

Each VPW frame on J1850:
```
[priority/type] [dest_id] [source_id] [mode] [submode] [data...] [CRC]
```

Priority 0x6C = normal, 0x6D = high priority.

Device IDs:
- Tool: 0xF0
- PCM: 0x10
- Broadcast: 0xFE

---

*Kernel source: `PcmHammer/Kernels/68k-VPW-Asm/Kernel.S` — the Rosetta Stone for P01/P59 flash protocol.*
