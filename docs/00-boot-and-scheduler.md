# P59 OS 12587603 — Boot Sequence & Task Scheduler

> Traced from 68k disassembly — 2026-06-22

## 1. Reset Vector (0x000000-0x000440)

```
Address 0x000000:  dc.l 0x00FFCE00     ← Initial stack pointer (SSP)
Address 0x000004:  dc.l Reset            ← Initial program counter (0x000440)
Address 0x000008-0x00005F:              ← Interrupt vectors (26 entries)
```

SSP = 0x00FFCE00 (top of internal RAM / bottom of external RAM)
PC = 0x00000440 → "Reset:" label

## 2. Reset Handler (0x000440-0x0004xx)

```
Reset:
  1. Clear frame pointer (suba.l a6,a6)
  2. Configure chip select registers:
     FFFFFB04 = 0xFFFFC000  (CS0 base)
     FFFFFB44 = 0xFFFF8000  (CS1 base)
     FFFFFB84 = 0xFFFF9000  (CS2 base)
     FFFFFA84 = 0xFFFFA000  (CS3 base)
     FFFFFAC4 = 0xFFFFB000  (CS4 base)
     FFBFB40/80/80 = 0x0200 (CS block size = 512)
  3. Set VBR (Vector Base Register) = 0x00000000
  4. Read hardware config from flash via CS0
  5. Call sub_138E (hardware initialization)
  6. Check FFFFFA07 bit 6 → branch to startup path
```

### Memory Map (from chip selects)

| CS# | Base Address | Size | Purpose |
|-----|-------------|------|---------|
| CS0 | 0xFFFFC000 | 512B | External flash / hardware regs |
| CS1 | 0xFFFF8000 | 512B | Internal module (QADC?) |
| CS2 | 0xFFFF9000 | 512B | Internal module (GPT?) |
| CS3 | 0xFFFFA000 | 512B | Internal RAM |
| CS4 | 0xFFFFB000 | 512B | Internal RAM / TPU RAM |

This confirms: all FFFFxxxx addresses are in the CPU's internal memory space.
The calibration data (0x008000-0x01FFFF) is in EXTERNAL flash.

## 3. Hardware Init → Main Loop

```
Reset
  ↓
sub_138E (hardware init)
  ↓
sub_80E (secondary init)
  ↓
sub_850 (VPW communication + boot completion)
  ↓
sub_AA0 (main message loop — VPW/J1850 handler)
  ↓
OS1:0002BA1E (main scheduler entry)
  ↓
DoManyThings1 (pre-loop initialization)
  ↓
ExecuteMainLoops (launch all 7 task loops)
```

## 4. Cooperative Multitasking Scheduler

The PCM uses a **cooperative multitasking** model. 7 independent loops run as infinite tasks, each calling its DoLoop function repeatedly:

```
ExecuteMainLoops:
  For each loop (G→F→E→D→C→B→A):
    BetweenMainLoops1(scratch_area, stack_frame, timing)  ← setup
    BetweenMainLoops2(scratch_area)                        ← launch

Each LoopX (infinite):
  LoopX:
    save SR, lower interrupt mask to level 0
    a0 = scratch_area_ptr
    SharedByMainLoops(a0)    ← common pre-loop handler
    DoLoopX()                 ← specific subsystem
    bra LoopX                 ← repeat forever
```

### Loop Assignments

| Loop | DoLoop | Scratch RAM | Priority | Subsystem |
|------|--------|-------------|----------|-----------|
| G | DoLoopG | FF99A0 | First launched | Vehicle speed, ETC gov, diag |
| F | DoLoopF | FF999A | | O2 sensors, fuel trim, EVAP |
| E | DoLoopE | FF9994 | | Fuel calculation |
| D | DoLoopD | FF998E | | Transmission, ETC governing |
| C | DoLoopC | FF9988 | | Idle, IAC, throttle follower |
| B | DoLoopB | FF9982 | | Fuel-cut, DFCO, RPM limiter |
| A | DoLoopA | FF997C | Last launched | Spark, knock, launch spark |

### Execution Model

- Each loop runs UNTIL COMPLETION (cooperative — no preemption)
- BetweenMainLoops1/2 handle timing — each loop may run at a different rate
- Interrupts fire between loop iterations (mask lowered to 0 at top of each loop)
- `SharedByMainLoops` handles common tasks for all loops (watchdog reset, timer updates?)

## 5. VPW Communication (sub_AA0 + sub_850)

The main message loop (sub_AA0) handles VPW/J1850 diagnostic requests in parallel with the task loops. It processes:
- Mode $27 (Security Access — seed/key)
- Mode $34/$36 (Flash read/write)
- Mode $3D (Kernel functions)

The communication happens independently — the task loops and VPW handler share RAM variables but run as separate execution contexts.

## 6. Key RAM Variables (Scheduler)

| Address | Size | Purpose |
|---------|------|---------|
| FFFFB550 | word | Current task/loop identifier |
| FFFFBE5D-FFBE68 | bytes | VPW message header/data |
| FFFFBE6E | byte | Communication mode flag |
| FFFFBE74 | byte | Hardware status flags |
| FF997C | 6 bytes | LoopA scratch area |
| FF9982 | 6 bytes | LoopB scratch area |
| FF9988-FF99A0 | varies | LoopC-G scratch areas |
| FFFFFA07 | byte | Hardware config / startup mode |

## 7. Interrupt Architecture

The vector table at 0x000000-0x00005F defines up to 26 interrupt vectors. Key ones:
- Offset 0x00: SSP (stack pointer)
- Offset 0x04: Reset PC
- Other vectors: timer interrupts, serial I/O, external interrupts

Most vectors point to `loc_55C` (default handler — likely an RTI loop).
Special handlers: sub_1626, sub_1634, loc_872F2, etc. handle specific hardware events.
