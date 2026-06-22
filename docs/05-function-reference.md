# P59 OS 12587603 — Function Reference

> 1,374 total subroutines in the factory OS
> Verified from the 936,975-line disassembly by LegacyNsfw

## Key Functions

| Function | Address | Category | Description |
|----------|---------|----------|-------------|
| `sub_30368` | 0x030368 | Fuel | Determines when to cut/re-enable fuel based on RPM, gear, VSS status, and cold engine protection. Key hook point for launch control. |
| `sub_30566` | 0x030566 | Fuel | Detects clutch pedal transitions and throttle changes for clutch-based decel fuel cut-off. Interacts with launch detection logic. |
| `sub_3090C` | 0x03090C | Fuel | Main DFCO (Decel Fuel Cut-Off) entry and exit logic. Handles clutch-based and normal DFCO. |
| `sub_3BDC4` | 0x03BDC4 | Spark | Calculates launch spark modifier and knock energy detection. Uses SPARK_ADVANCE_KA_LAUNCH_SPARK table. |
| `sub_79B10` | 0x079B10 | Airflow | Main dynamic airflow (Dyna-Air) calculation. Contains VE table lookups. VE expansion hooks go here. |
| `sub_16D6` | 0x0016D6 | Utility | General-purpose unsigned table lookup with interpolation. Used for VE, spark, and most 2D tables. |
| `sub_54C` | 0x00054C | System | Frequently called low-level utility (malloc, error handling, or IPC). Called by hundreds of functions. |
| `sub_850` | 0x000850 | System | Boot sequence: initializes hardware, memory, and jumps to main loop. |
| `sub_D6E` | 0x000D6E | System | Early boot hardware init. |
| `sub_AA0` | 0x000AA0 | System | Main operating loop dispatcher (calls DoLoopA through the main scheduling tasks). |
| `sub_83986` | 0x083986 | Transmission | Reads PRNDL switch, clutch switch, and transmission range. Sets FFFFA3AB (clutch state) and FFFFA3AF (gear). |
| `sub_21094` | 0x021094 | Vehicle | Electronic throttle control speed governor — limits vehicle speed via throttle. Uses KV_VEH_SPEED_GOV gains. |
| `sub_2CC22` | 0x02CC22 | Comms | CCP handler for ETAS calibration tools. Handles mode commands and data transfer. |
| `sub_2FC1E` | 0x02FC1E | Spark | Flat-foot shift spark blend calculation. Uses SPARK_ADVANCE_KV_FFS_SPARK_BLEND_FACTOR. |
| `sub_39F12` | 0x039F12 | Spark | Calculates base spark advance from high/low octane tables. Main spark lookup routine. |
| `sub_3AF0C` | 0x03AF0C | Spark | Catalytic converter lightoff spark retard. Cold-start emissions strategy. |
| `sub_3A754` | 0x03A754 | Spark | MBT (Maximum Brake Torque) spark calculation. |

## Finding Functions in Ghidra

```
Load the BIN at 0x0, processor 68000:BE:32:default
Use the Import12587603.java script to apply all 4,796 labels
Press G (Go To) and enter the address, e.g. 0x30368
```

## How Functions Are Organized

The OS uses a tick-based scheduler. `sub_AA0` is the main loop dispatcher.
It calls task functions (DoLoopA, DoLoopB, etc.) which each handle a subsystem:

| Loop | Purpose |
|------|---------|
| DoLoopA | Spark calculation, knock detection, launch spark |
| DoLoopB | Fuel-cut limiter, DFCO, RPM limiting |
| DoLoopC | Idle control, throttle follower |
| DoLoopD | Transmission control |
| DoLoopE | Diagnostics, DTCs |
| DoLoopF | O2 sensor, fuel trim, closed loop |
| DoLoopG | Vehicle speed, ETC governor |