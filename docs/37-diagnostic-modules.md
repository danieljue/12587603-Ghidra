# P59 OS 12587603 — Diagnostic Module Reference

> Compiled from CSV catalog — 2026-06-22
> Reference table mapping diagnostic modules (DG_/DI_) to sensor/system,
> primary DTCs, and documented coverage.

---

## 1. Diagnostic Module Architecture

The P59 diagnostic system has two layers per sensor/system:

- **DG_ (Diagnostic Gate)**: The test execution logic. Controls when a
  diagnostic runs, how many samples to collect, and what failure thresholds
  to use.
- **DI_ (Diagnostic Inhibit)**: The enable/inhibit conditions. Determines
  when the diagnostic CAN run based on engine state, temperatures, voltages,
  faults in related systems, etc.

Each module contains calibrations specific to that diagnostic test. The
DTC/MIL system (doc 18) manages fault storage, freeze frame, and MIL
illumination independently of the test execution logic.

---

## 2. Complete Module Reference

### 2.1 Engine Sensors

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_CAM | Camshaft position sensor | P0340-P0343 | Not documented |
| DG_CASE | Crank angle sensing error (CASE learn) | P1336 | Not documented |
| DG_CRANK | Crankshaft position sensor | P0335-P0336 | Not documented |
| DG_ECTR | Engine coolant temp rationality | P0116-P0118 | Not documented |
| DG_ECTS | Engine coolant temp stuck | P0117-P0118 | Not documented |
| DG_IAT | Intake air temperature | P0111-P0113 | Not documented |
| DG_MAP | Manifold absolute pressure | P0106-P0108 | Not documented |
| DG_TPS | Throttle position sensor | P0121-P0123 | Not documented |
| DI_IAT | IAT diagnostic inhibit conditions | — | Not documented |
| DI_MAP | MAP diagnostic inhibit conditions | — | Not documented |
| DI_TPS | TPS diagnostic inhibit conditions | — | Not documented |
| DI_CASE | CASE learn inhibit conditions | — | Not documented |

### 2.2 Oxygen Sensors

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_EOS | O2 sensor (pre/post) | P0130-P0167 | Partially (doc 28) |
| DI_EOS | O2 diag inhibit conditions | — | Partially (doc 28) |
| DG_POS | Post-catalyst O2 sensor | P0136-P0157 | Not documented |
| DI_POS | Post-O2 diag inhibit conditions | — | Not documented |

### 2.3 Fuel / Air / Spark

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_FASD | Fuel/Air/Spark diagnostic | Various | Not documented |
| DI_FASD | FASD inhibit conditions | — | Not documented |
| DG_FFS | Flex fuel sensor | P0176-P0178 | Not documented |
| DI_FFS | Flex fuel inhibit conditions | — | Not documented |
| DG_ICAT | Catalyst efficiency | P0420/P0430 | Partially (doc 29) |
| DG_ESC | Knock sensor | P0325-P0332 | Not documented |
| DG_MISFIRE | Misfire | P0300-P0308 | Partially (doc 30) |
| DI_MISFIRE | Misfire inhibit conditions | — | Partially (doc 30) |

### 2.4 EGR / EVAP

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_EGRQ | EGR flow test | P0400-P0404 | Not documented |
| DI_EGRQ | EGR flow inhibit conditions | — | Not documented |
| DG_LEGR | EGR position sensor | P0405-P0406 | Not documented |
| DI_LEGR | EGR position inhibit conditions | — | Not documented |
| DG_EONV | EVAP natural vacuum leak | P0440-P0455 | Not documented |
| DI_EONV | EVAP diag inhibit conditions | — | Not documented |

### 2.5 Secondary Air / Cooling

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_AIR | AIR pump/system | P0410-P0418 | Not documented |
| DI_AIR | AIR inhibit conditions | — | Not documented |
| DG_FAN | Cooling fan speed | P0480-P0481 | Not documented |
| DI_FAN | Fan diag inhibit conditions | — | Not documented |

### 2.6 Electrical / Heater Circuits

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_HSCR | Heated sensor circuit | Various | Not documented |
| DI_HSCR | HSCR inhibit conditions | — | Not documented |
| DG_VOLT | System voltage | P0560-P0563 | Not documented |
| DG_IOT | Injector output test | P0201-P0208 | Not documented |

### 2.7 Other

| Module | Sensor/System | Key DTCs | Documented In |
|--------|--------------|----------|---------------|
| DG_IGNITION_CONTROL | Ignition system | P0351-P0358 | Not documented |
| DG_ODM | Output driver module | Various | Not documented |
| DG_AC | AC clutch/pressure | P0531/P1539/P1546 | Partially (doc 26) |

---

## 3. Transmission Diagnostics (Not Documented)

| Module | Sensor/System | Key DTCs |
|--------|--------------|----------|
| T_DG_TASKS | Diagnostic task scheduling | — |
| T_DG_TYPES | Diagnostic type definitions | — |
| TRAN_DIAGNOSTICS | Transmission diagnostics | P07xx range |
| XDTP_TEMP | Trans temp performance | P0711-P0713 |
| XDTP_TRANS_RATIO | Gear ratio error | P0730-P0734 |
| XDTP_SLIP_COMPONENT | Clutch slip | P0740-P0742 |
| XDTP_TCC_SLIP | TCC stuck on/off | P0740-P0742 |
| XDTP_SHIFT_TIME | Shift time performance | — |
| XDTS_RANGE | PRNDL range sensor | P0705-P0706 |
| XDTS_BRAKE | Brake switch (trans) | P0719-P0724 |
| XDTS_INPT_SPD_SENSOR | Input speed sensor | P0716-P0717 |
| XDTS_OUTPT_SPD_SENSOR | Output speed sensor | P0720-P0722 |
| XDTS_TCC_REL_SWCH | TCC release switch | P0740 |
| XDTS_TEMP | Trans temp sensor | P0711-P0713 |

---

## 4. Coverage Summary

| Category | Total Modules | Documented | Coverage |
|----------|--------------|------------|----------|
| Diagnostic (DG_/DI_) | 30 | 8 (partial) | 27% |
| Transmission diagnostic | 13 | 0 | 0% |
| Infrastructure | 10+ | 2 | 20% |

**Recommendation:** Full documentation of each DG_/DI_ module would add ~30
more docs at significant effort for diminishing returns. The calibration
reference above enables navigation of all modules. Detailed diagnostic
tracing is best done on an as-needed basis when diagnosing specific DTCs.
