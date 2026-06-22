# P59 OS 12587603 — Complete Reference

> Open-source documentation for GM P59 PCM reverse engineering.
> Forked from [LegacyNsfw/12587603](https://github.com/LegacyNsfw/12587603), built for humans and AI agents.

## What This Is

A complete reference for the GM P59 PCM running OS 12587603 — the universal LS1/LS2 ECU found in millions of vehicles. Every address verified against the 936,975-line disassembly. Every function traced end-to-end.

**For tuners**: Every calibration address, conversion formula, and table layout you need to build an XDF from scratch.

**For developers**: Every function, RAM address, and data flow you need to write custom code for the 68k CPU.

**For AI agents**: Structured markdown designed to be loaded as skill/context — agents can read these docs and autonomously reverse-engineer, build patches, or answer questions.

## Table of Contents

### Architecture & Layout
1. [Segment Map](01-segment-map.md) — Flash memory layout, free space regions
2. [RAM Address Map](02-ram-address-map.md) — Every verified RAM address and what it means
3. [Calibration Address Map](03-calibration-addresses.md) — Key tables, scalars, and flags with addresses

### How the ECU Works
4. [Data Flow](04-data-flow.md) — Sensor input → calculation → actuator output
5. [Function Reference](05-function-reference.md) — All important subroutines with descriptions
6. [Sensor Inputs](06-sensor-inputs.md) — MAP, MAF, IAT, ECT, VSS, O2, TPS
7. [Fuel System](07-fuel-system.md) — VE lookup, injector pulse, fuel trim, PE mode
8. [Spark System](08-spark-system.md) — Base spark, knock control, launch spark, smoothing
9. [Idle Control](09-idle-control.md) — IAC, idle spark, idle airflow, throttle follower
10. [Fuel-Cut & Limiters](10-fuel-cut-limiter.md) — RPM limiter, DFCO, clutch DFCO
11. [Launch Control](11-launch-control.md) — Factory launch spark logic (sub_3BDC4)
12. [VPW Protocol](12-vpw-protocol.md) — Diagnostic protocol, mode dispatcher

### Tuning Reference
13. [Tuning Formulas](13-tuning-formulas.md) — All conversion formulas (VE, spark, AFR, injector, etc.)

### Community Knowledge
14. [Community Tuning Knowledge](14-community-knowledge.md) — Collected from pcmhacking.net, ls1tech, hptuners

### Boost OS Analysis
15. [Boost OS Reverse Engineering](15-boost-os-analysis.md) — What Boost OS V3.4 actually changes
16. [Open12587603 Design](16-open12587603-design.md) — How we replicate Boost OS features with open-source code

## Quick Reference

### Key Addresses

| Address | Name | Purpose |
|---------|------|---------|
| 0x0008442 | K_MAIN_VOLUMETRIC_EFFICIENCY | Main VE table |
| 0x0010890 | KA_MAIN_OT_HIGH_OCTANE | High-octane spark table |
| 0x0010E3A | KA_MAIN_OT_LOW_OCTANE | Low-octane spark table |
| 0x000BAE2 | KE_PN_ENGINE_OVERSPEED_HIGH | RPM limit (fuel cut high) |
| 0x0009A82 | KV_ENGINE_SPEED_LIMIT | ETC governor RPM limit |
| 0x000C7D4 | KV_STOICHIOMETRIC_FUEL_AIR | Stoich AFR vs ethanol |

### Key RAM Addresses

| Address | Size | Purpose |
|---------|------|---------|
| FFFFA562 | word | Current engine RPM |
| FFFFADB6 | word | MAP / engine load (scaled) |
| FFFFAEC0 | word | VSS raw (frequency/period) |
| FFFFA3AF | byte | Gear position |
| FFFFA3AB | byte | Clutch switch state |
| FFFFA93C | byte | Fuel cut status |

## How to Use

### With Ghidra
Load `12587603-2004-Corvette-M6.bin` into Ghidra using processor 68000:BE:32:default at base 0x0. Use `ghidra/Import12587603.java` to import all 4,796 labels from the CSV.

### With an AI Agent
Copy the docs/ folder into the agent's context or skill library. The agent can use the address maps to find anything in the disassembly.

### Building open12587603
See [open12587603.py](../open12587603.py) for the patcher. Each feature is documented with exact byte offsets, original instructions, and rationale.

## Credits

- **LegacyNsfw** — Original reverse engineering, IDA scripts, 4,796-entry CSV
- **PCM Hammer team** — Flash kernel, VPW documentation
- **bubba2533 / turbo_v6** — Boost OS inspiration
- **pcmhacking.net community** — Years of collective knowledge
