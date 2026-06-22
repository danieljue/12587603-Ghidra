# P59 ECM Architecture — MC68332, CPU32, and Emulation

> Capstone document — 2026-06-22
> The silicon-level architecture of the GM P59 Powertrain Control Module,
> its capabilities, and possibilities for simulation and emulation.

---

## 1. The Chip: Motorola MC68332

The P59 PCM is built around the **Motorola MC68332** microcontroller, a
member of the 68300 family introduced in 1989. This is a 32-bit microcontroller
built around the **CPU32** core — a 68020-derived processor with a 16-bit
data bus and 24-bit address bus.

### 1.1 Vital Statistics

| Parameter | Value |
|-----------|-------|
| CPU Core | CPU32 (68020 instruction subset) |
| Data Bus Width | 16 bits (external), 32 bits (internal registers) |
| Address Bus | 24 bits (16 MB addressable) |
| Clock Speed | 20.97 MHz (crystal) |
| System Clock | 20.97 MHz (no PLL multiplier on base 68332) |
| Bus Speed | 20.97 MHz (single-cycle external bus) |
| Execution | ~3-5 MIPS (typical for 68k at this clock) |
| Package | 132-pin PQFP (plastic quad flat pack) |
| Process | HCMOS (high-speed CMOS), 5V |
| Operating Temp | -40°C to +125°C (automotive grade) |
| Internal RAM | 2 KB standby SRAM (battery-backed possible) |
| Internal TPU RAM | 256 bytes (parameter storage for TPU) |

### 1.2 Why the 68332?

GM chose the 68332 for several reasons that still matter today:

1. **Ruggedness**: Automotive temperature range, tolerant of voltage sags,
   EMI-hardened. These chips survive underhood for decades.

2. **TPU (Time Processor Unit)**: The 68332's killer feature. 16 independent
   timer channels that can generate PWM, capture pulses, measure frequency,
   and output stepper motor sequences — all WITHOUT CPU intervention. This
   is how the PCM handles 8 injector outputs, 8 ignition coil dwell timers,
   VSS input, CKP/CMP input capture, IAC stepper control, and tachometer
   output simultaneously at 6200+ RPM.

3. **QADC (Queued ADC)**: 10-bit analog-to-digital converter with a
   programmable scan queue. Reads sensors in hardware-determined order
   without CPU polling. Essential for real-time engine control.

4. **Deterministic timing**: No cache, no branch prediction, no pipelining
   surprises. Every instruction takes a known number of cycles. This is
   critical for real-time control — you can count cycles to verify that
   your injector timing math completes before the next ignition event.

5. **Military/aerospace heritage**: The 68332 flew on satellites and guided
   missiles. GM's decision to use it meant the PCM could be validated to
   the same standards as flight computers.

---

## 2. The CPU32 Instruction Set

### 2.1 What You Get (68020 Subset)

CPU32 is a subset of the 68020 instruction set. What's INCLUDED:

```
Data movement:
  MOVE, MOVEA, MOVEM, MOVEP, MOVEQ, LEA, PEA, LINK, UNLK
  EXG, SWAP, EXT

Arithmetic (8/16/32-bit):
  ADD, ADDA, ADDI, ADDQ, ADDX
  SUB, SUBA, SUBI, SUBQ, SUBX
  MULS, MULU, DIVS, DIVU (32×32→32 multiply, 32/16→16 divide)
  NEG, NEGX, ABS, CLR

Logical:
  AND, ANDI, OR, ORI, EOR, EORI, NOT
  ASL, ASR, LSL, LSR, ROL, ROR, ROXL, ROXR

Bit manipulation:
  BTST, BSET, BCLR, BCHG (test/set/clear/change individual bits)

Program control:
  Bcc (BRA, BEQ, BNE, BCS, BCC, BMI, BPL, BVS, BVC, BGT, BGE, BLT, BLE, BHI, BLS)
  DBcc (DBRA, DBEQ, etc. — decrement-and-branch loops)
  JMP, JSR, RTS, RTE, RTR
  Scc (set byte on condition)

System:
  STOP, RESET, RTE, MOVEC (move to/from control registers)
  TAS (test-and-set for semaphores)
  CHK, CHK2 (array bounds checking)
  MOVES (move to/from alternate address space)

BCD (packed decimal, rarely used in ECU code):
  ABCD, SBCD, NBCD
```

What's MISSING from full 68020 (not in CPU32):

```
- 32×32→64 multiply and 64/32→32 divide (MUL.L, DIV.L with 64-bit)
- Bit field instructions (BFINS, BFEXT, BFFFO, etc.)
- Coprocessor interface (cpGEN, cpRESTORE, etc.)
- Full 32-bit address bus (only 24 bits externally)
- Instruction cache
- Burst memory cycles
- Dynamic bus sizing (CPU32 has static 16-bit bus)
```

### 2.2 Addressing Modes

CPU32 supports the full 68000 addressing mode set:

```
Data register direct:        D0-D7
Address register direct:     A0-A7 (A7 = SP)
Address register indirect:   (An)
Post-increment:              (An)+
Pre-decrement:               -(An)
With displacement:           d16(An)
With index:                  d8(An, Xn)
Absolute short:              xxx.W  (16-bit address, sign-extended)
Absolute long:               xxx.L  (32-bit address)
PC-relative with disp:       d16(PC)
PC-relative with index:      d8(PC, Xn)
Immediate:                   #xxx
```

The P59 firmware relies heavily on:
- **Absolute long addressing** for RAM: `move.w (0xFFFFA562).l, d0` — reads RPM
- **Absolute long addressing** for calibration data: `cmp.w (0x00009A82).l, d3`
- **Address register indirect with displacement** for table lookups: `tblu.w (a2), d3`
- **PC-relative** for position-independent code in the flash kernel

### 2.3 Table Lookup Instructions

CPU32 adds two instructions crucial for ECU calibration tables:

```
TBLU (Table Lookup Unsigned):
  Performs linear interpolation between table entries.
  Format: tblu.w (An), Dn
  Input: Dn contains the fractional index
  The table at (An) has a special compressed format

TBLS (Table Lookup Signed):
  Same as TBLU but for signed values (spark, fuel trims)
```

These instructions are the hardware implementation of what every ECU does
in software: look up a value in a 1D table and interpolate between
breakpoints. The 68332 does this in ONE instruction, taking ~20 cycles.
For a 17×20 VE table lookup with bilinear interpolation, the CPU32
executes it in ~150 cycles — about 7 microseconds at 21 MHz.

---

## 3. The On-Chip Peripherals

### 3.1 SIM (System Integration Module)

The SIM is the chip's central nervous system — it configures everything:

```
SIM Registers (base 0xFFFA00):
  Module Configuration:   0xFFFA00  — clock, bus width, pin functions
  Clock Synthesizer:      0xFFFA04  — clock source, dividers
  Chip Selects CS0-CS10:  0xFFFA80-0xFFFAD4  — 11 programmable chip selects
  System Protection:       0xFFFA20  — bus error, halt, reset control
  Periodic Interrupt Timer (PIT):  0xFFFA30  — programmable interval timer
  COP Watchdog:            0xFFFA27  — service register

Chip Select registers (per CS):
  CSBAR (base address):    sets the starting address
  CSOR (option):           sets block size, wait states, bus width
```

The P59 configures 4 chip selects at boot:
- CS0: Flash memory at 0x000000 (1 MB, 16-bit)
- CS1: Internal peripherals at 0xFFFF8000
- CS2: TPU/QADC at 0xFFFFA000
- CS3: External I/O at 0xFFFFB000

The chip select unit is programmable enough to map any peripheral to any
address. This is why the P01 (512KB flash) and P59 (1MB flash) can run
the same OS — only the CS0 block size changes.

### 3.2 TPU (Time Processor Unit)

The TPU is the PCM's secret weapon. 16 channels, each can be independently
configured for one of these functions:

```
TPU Functions (pre-programmed in mask ROM):
  Input Capture:      measure pulse width / period (CKP, CMP, VSS)
  Output Compare:     generate precise timing pulses (injectors, spark)
  PWM:                variable duty cycle output (IAC, EGR, boost)
  Stepper Motor:      sequenced output for IAC stepper
  Period/PWM Measure: frequency measurement (MAF)
  Queued Output:      programmed sequence of events
  Synchronized PWM:   phase-locked PWM for multi-cylinder

Per channel: 16 bytes of parameter RAM
  Parameter 0: function code (selects which TPU function to run)
  Parameters 1-3: configuration (pin state, TCR1/TCR2 selection)
  Parameters 4-7: data (compare values, periods, duty cycles)

The TPU runs at system clock speed independently.
Once configured, it generates injector pulses and spark events
without CPU involvement. The CPU just writes new compare values
to the parameter RAM, and the TPU handles the timing.
```

This is why the PCM can fire 8 injectors sequentially at 6200 RPM: each
injector event is a TPU output compare on its own channel. The CPU just
updates the compare value (injector pulse width) and the TPU does the rest.

### 3.3 QADC (Queued Analog-to-Digital Converter)

```
10-bit resolution (0-1023 counts)
Up to 16 analog input channels (AN0-AN15)
Programmable scan queue (up to 64 entries)
Automatic scan mode: queue wraps and re-scans continuously
Conversion time: ~10 μs per channel
Result registers: 0xFFFFF200-0xFFFFF23F

Queue entry format:
  Bits 15-11: channel number (0-15)
  Bits 10-8: input sample time
  Bit 7: resolution (0=10-bit, 1=8-bit)
  Bits 6-0: reserved

The PCM configures a continuous scan queue:
  1. ECT (coolant temp — safety critical, checked every scan)
  2. TPS1/TPS2 (throttle — safety critical)
  3. MAP (speed-density primary input)
  4. O2 sensors (closed-loop fuel feedback)
  5. APP1/APP2 (pedal position)
  ...remaining sensors at lower priority
```

### 3.4 QSM (Queued Serial Module)

```
SCI (Serial Communication Interface):
  Asynchronous UART — can be used for RS-232 or LIN
  Baud rate generator, programmable to any standard rate
  Used for development/diagnostic serial (ALDL connector pin)

QSPI (Queued Serial Peripheral Interface):
  Synchronous SPI master/slave
  Up to 16 programmable transfer queue entries
  Used for internal PCM communication (flash chip, external ICs)
```

The VPW J1850 transceiver is a separate external chip (MC68HC58 DLC)
mapped to memory addresses 0xFFF600-0xFFF60F, NOT the internal SCI.

### 3.5 GPT (General Purpose Timer)

```
4-channel timer module:
  Input capture (2 channels): pulse/period measurement
  Output compare (3 channels): PWM, frequency generation
  Pulse accumulator: counts external events

Used for:
  - Fuel pump pulse counting (safety: if pump pulses stop, cut fuel)
  - Knock sensor window timing
  - Spare PWM outputs
```

---

## 4. CPU32 Assembly Patterns in the P59 Firmware

### 4.1 The Signature Pattern: Table Lookup + Interpolation

```asm
; Look up VE table at RPM and MAP
; Input: d0 = RPM index, d1 = MAP index, d2 = stride
; Output: d0 = interpolated VE value

    lea     (0x00008442).l, a0    ; a0 = VE table base address
    move.w  #0x28, d2             ; d2 = stride (20 cols × 2 bytes = 40)
    jsr     (sub_16D6).l          ; call bilinear interpolation

; sub_16D6 performs bilinear interpolation using TBLU:
;   Reads table[a0 + row*stride + col]
;   Reads table[a0 + (row+1)*stride + col]
;   Interpolates between them based on fractional bits in d0/d1
;   Returns interpolated 16-bit result in d0
```

### 4.2 Bitfield State Machines

```asm
; VATS state machine: check if password is valid
    move.b  (0xFFFF8D19).w, d0    ; read password valid flag
    beq.s   password_invalid       ; branch if zero
    bset    #0, (0xFFFF8D16).w    ; set "authenticated" bit
    bra.s   continue

password_invalid:
    bclr    #0, (0xFFFF8D16).w    ; clear "authenticated" bit
    addq.b  #1, (0xFFFF8D18).w    ; increment failure counter
```

The BSET/BCLR/BTST instructions let the PCM pack 8 flags into a single byte,
critical for the 2KB of internal RAM.

### 4.3 Saturated Math (Anti-Windup)

```asm
; Clamp integrator to calibrated min/max
    move.w  (integrator).w, d0
    cmp.w   (INTEGRATOR_HIGH).l, d0
    ble.s   check_low
    move.w  (INTEGRATOR_HIGH).l, d0    ; clamp to max
    bra.s   store

check_low:
    cmp.w   (INTEGRATOR_LOW).l, d0
    bge.s   store
    move.w  (INTEGRATOR_LOW).l, d0     ; clamp to min

store:
    move.w  d0, (integrator).w
```

No built-in saturating math — all limit checking is explicit.

### 4.4 Fixed-Point Arithmetic

The P59 firmware uses fixed-point math extensively. Typical formats:

```
8.8 format:   upper byte = integer, lower byte = fraction/256
12.4 format:  upper 12 bits = integer, lower 4 bits = fraction/16
16.16 format: upper word = integer, lower word = fraction/65536

RPM scaling:  raw = RPM × 5.12  (RPM in lower 11 bits, fraction in upper 5?)
Temperature:  °C × 25.6 (raw / 25.6 = degrees)
VE:           gm·K/kPa × 655.36 (to get 16.16 fixed-point resolution)
```

---

## 5. Emulation and Simulation Possibilities

### 5.1 What Exists Today

**Ghidra (disassembly + decompilation):**
The 68332/CPU32 is natively supported. Ghidra decompiles 68k to C pseudocode.
The P59 firmware has been fully disassembled (936,975 lines).

**QEMU (full system emulation):**
QEMU does NOT have a 68332 target. The closest is the `m68k` target which
emulates a 68040 or ColdFire. These lack the TPU, QADC, QSM, and GPT
peripherals that make the 68332 unique.

**Other emulators:**
- MAME/MESS: includes some 68332-based systems (pinball machines, not ECUs)
- UAE (Amiga emulator): 68000/68020/68030, no 68332 peripherals
- None emulate the TPU, QADC, or chip select unit

### 5.2 What's Possible

**Option A: Ghidra Emulation (PCode)**
Ghidra's PCode intermediate representation can emulate CPU32 instructions.
Tools like `ghidra-emu` extend this to run binaries. Limitation: PCode
doesn't emulate TPU/QADC — you'd need to mock the memory-mapped I/O.

**Option B: Custom Emulator in Rust/C**
A from-scratch emulator for the 68332 is achievable:
- CPU32 core: ~3,000 lines (well-documented, straightforward 68k subset)
- SIM/chip selects: ~500 lines (address decoding logic)
- TPU: ~2,000 lines (16 channels, timing-critical, hardest part)
- QADC: ~500 lines (simple queue processor)
- QSM/SCI/QSPI: ~1,000 lines (standard serial peripherals)
- VPW DLC (MC68HC58): ~800 lines
- Flash memory model: ~300 lines

Total: ~8,000 lines of Rust for a cycle-accurate 68332 emulator.
The TPU and QADC are the significant challenges.

**Option C: Renode (multi-node emulation framework)**
Antmicro's Renode can emulate heterogeneous SoCs. It has 68k CPU support
but would need a 68332 peripheral model written in C#. The framework
handles memory maps, interrupts, and peripheral bus routing.

**Option D: Hardware-in-the-Loop (HiL)**
The practical approach for testing custom OS code:
1. Run the patcher on a PC
2. Flash the binary to a real P59 PCM via PCM Hammer
3. Connect the PCM to a JimStim or Arduino-based engine simulator
   (generates CKP, CMP, TPS, O2 signals)
4. Monitor outputs with a logic analyzer
5. This is what Boost OS developers actually do

### 5.3 The "Compile C for P59" Pipeline

It IS possible to compile C code for the P59:

```
1. m68k-elf-gcc -mcpu32 -msoft-float → produces CPU32 object code
2. The compiler generates standard 68k ELF binaries
3. You must write linker scripts that place code in the free OS5-OS7
   segments (0x0A0000-0x0EFFFF)
4. No libc, no malloc, no stdio — bare metal only
5. You must manually write TPU/QADC register accesses via memory-mapped I/O
6. The toolchain exists: m68k-elf-gcc is available on all platforms
7. PCM Hammer kernel was written in 68k assembly, but C is viable

Challenges:
- The 68332 has no FPU — floating point must be soft-float (slow)
- No MMU — no virtual memory, no memory protection
- 2KB internal RAM is TINY (but external RAM is available)
- Interrupt latency must be predictable (no long C functions in ISRs)
```

### 5.4 Why This Matters for open12587603

The open12587603 project (our Boost OS alternative) has two paths:

**Path 1: Assembly Patcher (current approach)**
- Hand-encode 68k subroutines in Python (doc 17, open12587603.py)
- Inject into free flash space (OS5-OS7, 192KB available)
- Patch existing functions with JSR hooks
- Advantages: no toolchain needed, minimal code, guaranteed to work
- Disadvantages: tedious, error-prone, hard to debug

**Path 2: C Compilation (future possibility)**
- Write boost control, wideband CL, and launch logic in C
- Compile with m68k-elf-gcc -mcpu32
- Link into free flash space
- Advantages: readable, maintainable, testable on PC
- Disadvantages: toolchain overhead, larger code size, no C runtime

The documentation we've built (42 docs, every RAM address, every function)
makes Path 2 viable. A developer could write C code that reads `*(volatile
uint16_t*)0xFFFFADB6` for MAP, calls `sub_16D6` for table interpolation,
and writes the TPU parameter RAM for injector timing — all from C, with
our docs as the API reference.

---

## 6. Comparison to Modern ECUs

| Feature | P59 (2004, 68332) | E38 (2008, MPC5565) | Modern (2024, TriCore/S32K) |
|---------|-------------------|---------------------|-----------------------------|
| CPU | CPU32 @ 21 MHz | PowerPC e200 @ 80 MHz | ARM Cortex-R52 @ 400 MHz |
| Bits | 16/32 | 32 | 32 |
| Flash | 1 MB (external) | 2 MB (internal) | 8+ MB (internal) |
| RAM | 2 KB + external | 80 KB (internal) | 1+ MB (internal) |
| ADC | 10-bit QADC | 12-bit eQADC | 12+ bit SAR ADC |
| CAN | Via external chip | 3× FlexCAN | 6+ CAN FD |
| Emulation | None | QEMU possible (PPC) | QEMU ARM |
| Documentation | Complete (our work) | Partial | OEM-proprietary |

The P59 is attractive for open-source because:
1. It's the last generation of the simple, well-documented 68k architecture
2. The entire firmware has been reverse-engineered and published
3. The 68332 is understood at the transistor level — no hidden features
4. Aftermarket tools (PCM Hammer, Universal Patcher) are mature
5. The ECU is cheap ($50-100 used), plentiful, and the connectors are standard

---

## 7. Further Reading

- **MC68332 User Manual** (Motorola, 1990): The definitive hardware reference.
  Available as PDF. Covers every register, every timing diagram, every
  peripheral in exhaustive detail. ~400 pages.

- **CPU32 Reference Manual** (Motorola, 1990): Instruction set reference
  with cycle counts and addressing modes. ~300 pages.

- **MC68HC58 DLC Data Sheet** (Motorola): The J1850 VPW transceiver chip
  used alongside the 68332. Covers the 5 DLC registers at 0xFFF600.

- **Intel 28F800B Data Sheet**: The 1MB flash memory chip. Sector erase
  (16 × 64KB), word-program, 12V VPP. Reference for PCM Hammer kernel
  development.

- **PCM Hammer Kernel Source** (`F:/github/PcmHammer/Kernels/68k-VPW-Asm/`):
  The definitive example of hand-written 68k assembly for this exact ECU.
  Shows how to program flash, communicate via VPW, and handle watchdog.

- **Our Documentation** (`F:/github/12587603-Ghidra/docs/`): 43 documents
  covering every subsystem, every RAM address, interrupt vectors, boot ROM,
  and calibration tables.
