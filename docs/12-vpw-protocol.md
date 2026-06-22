# P59 OS 12587603 — VPW Communication & Flash Interface

> Traced from 68k disassembly — 2026-06-22

## Hardware

The P59 uses the **68HC58 DLC** (Data Link Controller) chip for J1850 VPW communication.

| Register | Address | Purpose |
|----------|---------|---------|
| J1850_Status | 0xFFFFF60E | RFS + TMFS status flags |
| J1850_Config | 0xFFFFF600 | DLC configuration |
| J1850_Command | 0xFFFFF60C | BTAD + RFC control |
| J1850_TX_FIFO | 0xFFFFF60D | Transmit data byte |
| J1850_RX_FIFO | 0xFFFFF60F | Receive data byte |

### Status Register Sampling
```
sub_75A: move.b (FFFFF60E).w, (FFFFBE74).w   ← Read status byte (low byte)
sub_76A: move.w (FFFFF60E).w, (FFFFBE74).w   ← Read status word (low + high)
```

The status is mirrored to FFFFBE74 for the main loop to check.

## Message Processing Flow

```
VPW Bus → 68HC58 DLC → Interrupt → sub_850 (message handler)
                                          ↓
                                    sub_72A (mode $xx dispatcher)
                                    sub_77A (mode $yy dispatcher)
                                          ↓
                                    sub_794 (mode jump table)
                                          ↓
                              ┌──────────────────────────┐
                              │ Mode $27: Security Access │
                              │ Mode $34: Download Req   │
                              │ Mode $35: Upload Req     │
                              │ Mode $36: Data Transfer  │
                              │ Mode $3D: Kernel Funcs   │
                              │ Mode $A0-$A2: Custom     │
                              └──────────────────────────┘
```

### Service Handler (sub_72A)
```
sub_72A:
    save SR, disable interrupts (level 7)
    d0 = byte_80A (mode byte from VPW message)
    call sub_794(d0)        ← dispatch to mode handler
    call sub_1626 5 times   ← delay loop / timing
    restore SR
    rts
```

## Mode $34/$35/$36 — Flash Upload/Download

These modes are the PCM Hammer interface:

| Mode | Direction | Purpose |
|------|-----------|---------|
| $34 | Tool → PCM | **Request Download** — PCM prepares for flash write |
| $35 | Tool → PCM | **Request Upload** — PCM prepares to send data |
| $36 | Tool ↔ PCM | **Transfer Data** — actual flash read/write bytes |

### Flash Write Sequence (PCM Hammer)
```
1. Mode $34: Send download request (address, size)
   → PCM validates address range, unlocks flash
2. Mode $36: Send data blocks (up to flash page size)
   → PCM writes to flash, verifies
3. Checksum verification
```

### Flash Kernel
The flash programming kernel (loaded by Mode $34) runs from RAM. It:
- Erases flash sectors (must erase before write)
- Programs flash pages
- Verifies written data

PCM Hammer's kernel (`Kernel.S`) is a separate 68k assembly program uploaded to the PCM's RAM and executed there.

## Mode $27 — Security Access

```
1. Tool sends: [6C F0 10 27 01]  ← Request seed
2. PCM responds: [6C 10 F0 27 02 seed]  ← Send seed value
3. Tool computes key from seed using secret algorithm
4. Tool sends: [6C F0 10 27 03 key]  ← Send key
5. PCM validates key, unlocks protected modes ($34/$36)
```

The seed/key algorithm is proprietary GM. It's been reverse-engineered and is implemented in PCM Hammer.

## Why Boost OS Requires Full Flash

Boost OS patches are in the calibration segment AND the OS segments. A "calibration-only write" wouldn't include the OS code patches. The custom OSID also requires a full OS segment write for PCM Hammer to recognize the new ID.

PCM Hammer V20 is required because V21 changed how OSID validation works — it rejects the custom OSID that Boost OS uses.

## VPW Message Format

```
[Priority:1B] [Target:1B] [Source:1B] [Mode:1B] [Submode:1B] [Data:N] [CRC:1B]
    6C            10           F0          34         00         ...
```

- Priority 0x6C = normal diagnostic
- Target 0x10 = PCM (primary ID)
- Source 0xF0 = scan tool
- CRC is a simple 8-bit checksum over the message
