# P59 OS 12587603 — Hardware Register Map & Interrupt Vectors

> Traced from 68k disassembly, PCM Hammer kernel, and 68332 datasheet
> 2026-06-22 — NSA-level hardware documentation

---

## 1. CPU: Motorola 68332 (MC68332)

The P59 PCM uses the **MC68332** microcontroller, a member of the Motorola
68300 family. Key specifications:

| Parameter | Value |
|-----------|-------|
| CPU Core | CPU32 (68020 subset) |
| Data Bus | 16-bit |
| Address Bus | 24-bit (16 MB address space) |
| Clock | 20.97 MHz (crystal) / 20.97 MHz (system) |
| Timers | TPU (16 channels), GPT (4 channels) |
| Serial | QSM (SCI + QSPI) |
| CAN | TouCAN (MC68376 variant — not present on base 68332) |
| ADC | QADC (10-bit, up to 16 channels) |
| RAM | 2 KB internal SRAM + external |
| Flash | External 1 MB (Intel 28F800B) |
| Watchdog | COP (Computer Operating Properly) |

---

## 2. Interrupt Vector Table (0x000000-0x0003FF)

The CPU32 has 256 exception vectors. Each is 4 bytes (longword address).
This table shows the vectors populated in OS 12587603.

| Vector | Address | Handler | 68332 Exception |
|--------|---------|---------|-----------------|
| 0 | 0x000 | SSP=0xFFCE00 | Reset: Initial Stack Pointer |
| 1 | 0x004 | Reset (0x000440) | Reset: Initial Program Counter |
| 2 | 0x008 | loc_55C | Bus Error |
| 3 | 0x00C | loc_55C | Address Error |
| 4 | 0x010 | loc_6C2 | Illegal Instruction |
| 5 | 0x014 | loc_55C | Zero Divide |
| 6 | 0x018 | loc_55C | CHK/CHK2 Instruction |
| 7 | 0x01C | loc_55C | TRAPcc/TRAPV |
| 8 | 0x020 | loc_55C | Privilege Violation |
| 9 | 0x024 | loc_55C | Trace |
| 10 | 0x028 | loc_55C | Line 1010 Emulator |
| 11 | 0x02C | loc_55C | Line 1111 Emulator |
| 12-14 | 0x030-0x038 | Reserved (unused) |
| 15 | 0x03C | loc_55C | Uninitialized Interrupt |
| 16-23 | 0x040-0x05C | Reserved (unused) |
| 24 | 0x060 | loc_55C | Spurious Interrupt |
| 25 | 0x064 | loc_55C | Level 1 Autovector |
| 26 | 0x068 | loc_55C | Level 2 Autovector |
| 27 | 0x06C | loc_55C | Level 3 Autovector |
| 28 | 0x070 | loc_55C | Level 4 Autovector |
| 29 | 0x074 | loc_55C | Level 5 Autovector |
| 30 | 0x078 | loc_55C | Level 6 Autovector |
| 31 | 0x07C | loc_55C | Level 7 Autovector (NMI) |
| 32-47 | 0x080-0x0BC | loc_55C | Trap 0-15 Instructions |
| 48 | 0x0C0 | Reserved |
| 49 | 0x0C4 | unk_596 | Likely: TPU Channel 0? |
| 50-59 | 0x0C8-0x0EC | loc_55C | Reserved / unimplemented |
| 60 | 0x0F0 | unk_5AE | Likely: TPU / QADC |
| 61-72 | 0x0F4-0x120 | loc_55C | Reserved |
| 73 | 0x124 | unk_634 | Likely: QADC / SCI |
| 74-79 | 0x128-0x13C | loc_55C | Reserved |
| 80 | 0x140 | unk_610 | Likely: TouCAN / GPT |
| 81-86 | 0x144-0x158 | loc_55C | Reserved |
| 87-90 | 0x15C-0x168 | unk_5FE, loc_55C, unk_5DA, unk_5EC | TPU channels |
| 91-94 | 0x16C-0x178 | Reserved |
| 95-100 | 0x17C-0x190 | unk_622 (×6) | SCI / QSPI / Timer |
| 101-134 | 0x194-0x218 | loc_55C | Reserved |
| 135-140 | 0x21C-0x230 | unk_622 (×6) | SCI / QSPI / Timer |
| 141-266 | 0x234-0x428 | loc_55C | Reserved / unimplemented |
| 267 | 0x42C | sub_1626 | User-defined: likely scheduler |
| 268 | 0x430 | sub_1634 | User-defined |
| 269 | 0x434 | loc_872F2 | User-defined |
| 270 | 0x438 | loc_4A678 | User-defined |
| 271 | 0x43C | loc_87992 | User-defined |
| 272 | 0x440 | loc_8789E | User-defined |
| 273 | 0x444 | FF8000 | User-defined (PCM Hammer kernel entry!) |
| 274 | 0x448 | loc_66E44 | User-defined |
| 275 | 0x44C | locret_66E46 | User-defined |
| 276 | 0x450 | loc_66C8E | User-defined |
| 277 | 0x454 | loc_66CFC | User-defined |
| 278-279 | 0x458-0x45C | locret_66E46 | User-defined |
| 280 | 0x460 | loc_66D42 | User-defined |
| 281 | 0x464 | locret_66E46 | User-defined |
| 282 | 0x468 | loc_66E1A | User-defined |

> **Note:** Vector 273 (0x444) points to **0xFF8000** — this is the PCM Hammer
> flash kernel load address. The boot ROM reserves this vector for external
> code injection during flash programming.

---

## 3. Boot Sequence (Reset Handler at 0x000440)

```
Reset:
  1. Clear A6 (frame pointer register)
  
  2. Configure SIM Chip Selects (68332 System Integration Module):
     CS0: base=0xFFFC000 (at FFFFFB04), option=0x200 (at FFFFFB40)
     CS1: base=0xFFFF8000 (at FFFFFB44), option=0x200 (at FFFFFB80)
     CS2: base=0xFFFFA000 (at FFFFFA84), option=0x200 (at FFFFFA80)
     CS3: base=0xFFFFB000 (at FFFFFAC4), option=0x200 (at FFFFFAC0)
  
     Interpretation:
     CS0: Internal RAM block (0xFFFC000 → 0xFFFC000+4KB)
     CS1: I/O Peripherals (0xFFFF8000-0xFFFF9FFF)
     CS2: I/O Peripherals (0xFFFFA000-0xFFFFBFFF)
     CS3: I/O Peripherals (0xFFFFB000-0xFFFFBFFF)
  
  3. Read SIM Configuration Register (FFFFFA07):
     Check module configuration / interrupt arbitration level
  
  4. Execute memory tests (RAM, ROM checksums)
  
  5. Initialize peripheral modules (TPU, QADC, SCI, TouCAN)
  
  6. Jump to main OS entry point
```

### Chip Select Base Registers (68332 SIM)

| CS# | Base Register | Option Register | Purpose |
|-----|--------------|-----------------|---------|
| CS0 | 0xFFFA80 | 0xFFFA84 | Flash memory (0x000000-0x0FFFFF) |
| CS1 | 0xFFFA88 | 0xFFFA8C | — |
| CS2 | 0xFFFA90 | 0xFFFA94 | — |
| CS3 | 0xFFFA98 | 0xFFFA9C | — |
| CS4 | 0xFFFAA0 | 0xFFFAA4 | — |
| CS5 | 0xFFFAA8 | 0xFFFAAC | — |
| CS6 | 0xFFFAB0 | 0xFFFAB4 | — |
| CS7 | 0xFFFAB8 | 0xFFFABC | — |
| CS8 | 0xFFFAC0 | 0xFFFAC4 | — |
| CS9 | 0xFFFAC8 | 0xFFFACC | — |
| CS10 | 0xFFFAD0 | 0xFFFAD4 | Boot ROM — not used after reset |

---

## 4. J1850 VPW Serial Interface (MC68HC58 DLC)

The P59 uses the MC68HC58 Data Link Controller for J1850 VPW communication.
Registers as identified in the disassembly and PCM Hammer kernel:

| Address | Register | Width | Direction | Description |
|---------|----------|-------|-----------|-------------|
| 0xFFF600 | J1850_Config | word | R/W | Configuration (baud rate, mode) |
| 0xFFF606 | — | byte | W | Secondary config byte |
| 0xFFF607 | — | byte | W | Secondary config byte |
| 0xFFF60C | J1850_Command | word | W | Command byte register (BTAD + RFC) |
| 0xFFF60D | J1850_TX_FIFO | byte | W | Transmit FIFO |
| 0xFFF60E | J1850_Status | word | R | Status byte (RFS, DLI, NETF, 4XMD, TMFS) |
| 0xFFF60F | J1850_RX_FIFO | byte | R | Receive FIFO |

### J1850 Protocol Modes (as used by this OS)

| Mode | Purpose | Documented In |
|------|---------|---------------|
| $27 | Security Access | doc 19 (VATS) |
| $28 | Disable Normal Message Transmission | doc 12 (VPW) |
| $34 | Download Request | doc 12 |
| $35 | Upload Request | doc 12 |
| $36 | Data Transfer | doc 12 |
| $3D | Kernel Functions (flash ID, CRC, erase) | doc 12 |

---

## 5. Watchdog (COP)

The COP watchdog resets the CPU if not serviced within the timeout period.

| Address | Register | Width | Description |
|---------|----------|-------|-------------|
| 0xFFFA27 | COP1 (internal) | byte | COP service register — write 0x55 then 0xAA to reset |
| 0xFFD006 | COP2 (external) | word | External watchdog — used on P01/P59 |

**P01/P59 COPs:**
- Internal: SIM COP at 0xFFFA27 (MC68332 standard)
- External: Hardware watchdog at 0xFFD006

**COP Timeout:** The 68332 internal COP has a configurable timeout
(typically 2^18 / system_clock = ~12.5ms). The external COP at 0xFFD006
is likely the Intel 28F800B flash chip's hardware reset line — if the CPU
crashes, the flash enters reset and the engine stops.

---

## 6. TPU (Time Processor Unit)

The TPU has 16 programmable timer channels used for:

| Channel | Likely Function | Evidence |
|---------|----------------|---------|
| TPU0 | Injector driver 1 (cylinder 1) | sub_7D082 output |
| TPU1 | Injector driver 2 (cylinder 8) | — |
| TPU2 | Injector 3 (cylinder 7) | — |
| TPU3 | Injector 4 (cylinder 2) | — |
| TPU4 | Injector 5 (cylinder 6) | — |
| TPU5 | Injector 6 (cylinder 5) | — |
| TPU6 | Injector 7 (cylinder 4) | — |
| TPU7 | Injector 8 (cylinder 3) | — |
| TPU8 | CKP input capture (tooth period) | Misfire detection doc 30 |
| TPU9 | CMP input capture (cam position) | — |
| TPU10 | VSS input (speed sensor) | Speedometer doc 21 |
| TPU11 | IAC stepper motor control | Idle doc 08 |
| TPU12 | Spark dwell timer (coil primary) | Spark dwell doc 38 sec 7 |
| TPU13 | Tachometer output | KE_TACH_PULLUP_ENABLE |
| TPU14 | Fuel pump PWM | Fuel pump doc 21 |
| TPU15 | EGR / Boost control PWM | EGR doc 22 |

> **Note:** These channel assignments are INFERRED from function analysis and
> 68332 TPU capability. Exact assignment requires tracing each TPU configuration
> write in the disassembly at addresses 0xFFFFFAxx (TPU RAM parameter block).

---

## 7. QADC (Queued Analog-to-Digital Converter)

The QADC has up to 16 analog input channels (10-bit resolution):

| Channel | Sensor | Verified Via |
|---------|--------|-------------|
| AN0 | MAP (Manifold Absolute Pressure) | sub_79B10 VE lookup |
| AN1 | MAF (Mass Airflow — frequency, not ADC!) | — |
| AN2 | IAT (Intake Air Temperature) | thermistor input |
| AN3 | ECT (Engine Coolant Temperature) | thermistor input |
| AN4 | TPS1 (Throttle Position Sensor 1) | ETC dual-track |
| AN5 | TPS2 (Throttle Position Sensor 2) | ETC dual-track |
| AN6 | O2 Bank 1 Sensor 1 (pre-cat) | FUEL_O2 module |
| AN7 | O2 Bank 2 Sensor 1 (pre-cat) | FUEL_O2 module |
| AN8 | O2 Bank 1 Sensor 2 (post-cat) | — |
| AN9 | O2 Bank 2 Sensor 2 (post-cat) | — |
| AN10 | AC Pressure | AC doc 26 |
| AN11 | EGR Pintle Position (C1 Pin 55) | sub_2DA2A → FFFFF2C0 |
| AN12 | Fuel Tank Pressure (EVAP) | DG_EVAP |
| AN13 | APP1 (Accelerator Pedal Position 1) | ETC doc 08 |
| AN14 | APP2 (Accelerator Pedal Position 2) | ETC doc 08 |
| AN15 | System Voltage Monitor | VOLTAGE_MONITOR |

> **Note:** QADC channel assignments are INFERRED. The exact ANx pin mapping
> requires tracing QADC configuration writes at SIM registers 0xFFFFFAxx.

---

## 8. Gaps & Unresolved (NSA Round 2)

1. **TPU exact channel mapping**: Each TPU channel must be configured by
   writing to the TPU parameter RAM at 0xFFFFFAxx. The exact channel-to-
   function mapping requires tracing those writes.

2. **QADC exact channel mapping**: QADC configuration registers (0xFFFFFAxx
   QADC module registers) control which AN0-AN15 pins are scanned.

3. **TouCAN registers**: Some P59 variants have a TouCAN module (MC68376
   derivative). If present, CAN registers at 0xFFFFExx need mapping.

4. **QSM (SCI + QSPI)**: The Queued Serial Module provides the SCI (UART)
   and QSPI (synchronous serial). SCI register locations and QSPI
   configuration are not documented.

5. **GPT (General Purpose Timer)**: 4-channel timer module for additional
   timing functions. Register locations and channel functions unknown.

6. **External memory interface**: The 28F800B flash uses a 16-bit data bus
   with address latch. The exact bus timing (wait states) set in the SIM
   chip select option registers is not verified.

7. **Checksum algorithm**: The CVN calculation for flash segments uses
   a CRC polynomial. Source in Universal Patcher / gm-checksum-plugins.
   Not reverse-engineered here.

8. **Boot ROM code (0x000440-0x003FFF)**: Only the reset handler's first
   30 instructions traced. The full boot sequence (memory test, peripheral
   init, kernel vector setup) is not documented line-by-line.

**NSA question for round 3:** If an NSA engineer spent 40 MORE hours, they
would trace every TPU channel configuration write, map every QADC channel,
decode the CAN register map, and reverse-engineer the checksum algorithm.
