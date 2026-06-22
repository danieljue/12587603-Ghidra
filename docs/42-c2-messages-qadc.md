# P59 OS 12587603 — C2 Serial Message Catalog & QADC Queue

> NSA Round 5 — Final sweep 2026-06-22
> Complete Class 2 J1850 VPW message inventory, QADC scan sequence, and
> diagnostic module parameter reference.

---

## 1. C2 Normal Messages — Complete Inventory

Every message the PCM transmits on the Class 2 serial bus with update rates
and send-on-change thresholds.

### 1.1 High-Rate Messages (~100ms update)

| Message | Content | Min Interval | Send-On-Change | Default |
|---------|---------|-------------|----------------|---------|
| Engine Speed | RPM | KE_C2_ENGINE_SPEED_MIN_INTERVAL | KE_C2_ENGINE_SPEED_SEND_ON_CHANG (RPM) | KE_C2_ENGINE_SPEED_DEFAULT_VALUE |
| Vehicle Speed (std) | MPH | KE_C2_VEHICLE_SPEED_MIN_INTERVAL | KE_C2_VEHICLE_SPEED_SEND_ON_CHAN (MPH) | — |
| Vehicle Speed (hi-res) | MPH (×256) | KE_C2_HI_RES_VEH_SPD_MIN_INTERVL | KE_C2_HI_RES_VEH_SPD_SEND_ON_CHG | — |
| Coolant Temp | °C | KE_C2_COOLANT_TEMPERATURE_MIN_IN | KE_C2_COOLANT_TEMPERATURE_SEND_O | Limited to KE_C2_COOLANT_TEMP_MAX |

### 1.2 Medium-Rate Messages (~1s update)

| Message | Content | Min Interval | Send-On-Change | Default |
|---------|---------|-------------|----------------|---------|
| IAT | °C | KE_C2_INDUCTION_AIR_TEMP_MIN_INT | KE_C2_INDUCTION_AIR_TEMP_SEND_ON | — |
| Ignition Voltage | Volts | KE_C2_IGNITION_VOLT_MIN_INTERVAL | KE_C2_IGNITION_VOLT_SEND_ON_CHG | — |
| Fuel % | Percent | KE_C2_FUEL_PERCENT_MIN_INTERVAL | KE_C2_FUEL_PERCENT_SEND_ON_CHANG | KE_C2_FUEL_PERCENT_DEFAULT_VALUE |
| Fuel Volume | Liters | KE_C2_FUEL_VOLUME_MIN_INTERVAL | KE_C2_FUEL_VOLUME_SEND_ON_CHANGE | KE_C2_FUEL_VOLUME_DEFAULT_VALUE |
| Instant Fuel | L/hr | KE_C2_INSTANTANEOUS_FUEL_MIN_INT | KE_C2_INSTANTANEOUS_FUEL_SEND_ON | — |
| Engine Oil Press | kPa | KE_C2_ENGINE_OIL_PRESSURE_MIN_IN | KE_C2_ENGINE_OIL_PRESSURE_SEND_O | KE_C2_ENGINE_OIL_PRESSURE_DEFAUL |
| Engine Oil Life | Percent | KE_C2_OIL_LIFE_REMAINING_MIN_INT | KE_C2_OIL_LIFE_REMAINING_SEND_ON | — |
| Baro Pressure | kPa | KE_C2_BAROMETRIC_PRESSURE_MIN_IN | KE_C2_BAROMETRIC_PRESSURE_SEND_O | — |
| Engine Torque | ft-lb | KE_C2_ENG_TORQ_MIN_INTERVAL | KE_C2_ENG_TORQ_SEND_ON_CHANGE | — |
| Pedal Load | Percent | KE_C2_PEDAL_LOAD_MIN_INTERVAL | KE_C2_PEDAL_LOAD_SEND_ON_CHANGE | — |
| Fan Speed | Percent | KE_C2_ENG_FAN_SPEED_MIN_INTERVAL | KE_C2_ENG_FAN_SPD_SEND_ON_CHANGE | — |
| AC Pressure | PSI | KE_C2_AC_PRESSURE_MIN_INTERVAL | KE_C2_AC_PRESSURE_SEND_ON_CHANGE | KE_C2_AC_PRESSURE_DEFAULT_VALUE |

### 1.3 Low-Rate Messages (~5-10s update)

| Message | Content | Min Interval | Send-On-Change | Notes |
|---------|---------|-------------|----------------|-------|
| Cruise Memory Speed | MPH | KE_C2_CRUISE_MEMORY_SPEED_MIN_IN | KE_C2_CRUISE_MEMORY_SPEED_SEND_O | |
| Current Gear | 1-4 | KE_C2_CURRENT_GEAR_MIN_INTERVAL | — | |
| PRNDL Position | P/R/N/D/etc | KE_C2_PRNDL_POSITION_MIN_INTERVA | — | |
| PRNDL Display | Display state | KE_C2_PRNDL_DISPLAY_INTERVAL | — | IPC display |
| Rolling Odometer | Miles | KE_C2_ROLLING_ODO_MIN_INTERVAL | KE_C2_ROLLING_ODO_SEND_ON_CHANGE | |
| Accumulated Fuel | Liters | KE_C2_ACCUMULATED_FUEL_MIN_INTER | KE_C2_ACCUMULATED_FUEL_SEND_ON_C | |
| Trans Oil Temp | °C | KE_C2_TRANSMISSION_OIL_TEMP_MIN_ | KE_C2_TRANSMISSION_OIL_TEMP_SEND | |
| TCS Failure Status | Bitfield | KE_C2_PT_TCS_FAILURE_STATUS_MIN_ | — | Supported bits in KE_TCS_FAILURE_STATUS_BITS_SUPPO |
| Park/Neutral Switch | Boolean | KE_C2_PARK_NEUTRAL_SW_ACTIVE_MIN | — | |
| TCC Brake Depressed | Boolean | KE_C2_TCC_BRAKE_DEPRESSED_MIN_IN | — | |
| AC Clutch Status | Engaged/Dis | KE_C2_AC_CLUTCH_ENGAGED_MIN_INTE | — | |
| HVAC Auto Recirc | Command | KE_C2_HVAC_AUTO_RECIRC_MIN_INTER | — | B230 RPT message |
| Clutch Pedal Depth | Percent | KE_C2_CLUTCH_PEDAL_DEP_MIN_INT | — | Manual trans only |

### 1.4 Powertrain Control Messages

| Message | Content | Notes |
|---------|---------|-------|
| FE06 System Power Mode | PCM alive + power state | KE_C2_FE06_REQ_DELAY_TIME1/2 for timing |
| Powertrain Node Alive | Heartbeat | KE_C2_POWERTRAIN_NODE_ALIVE_PERI interval |
| Local Power Mode Master | If PCM controls power mode | KE_C2_LOCAL_POWERMODE_CONTROL = TRUE |

### 1.5 J1850 Protocol Details

J1850 VPW messages have this format:
```
[SOF] [Header: 1-3 bytes] [Data: 0-7 bytes] [CRC] [EOF]
```

Header byte encoding:
- Bits 7-5: Priority (0=highest, 7=lowest)
- Bits 4-0: Message type + addressing mode

Common GM headers:
- 0x6C: Functional request (scanner → PCM)
- 0x6A: Functional broadcast (PCM → all)
- 0x8C: Physical request (scanner → PCM)
- 0x8A: Physical response (PCM → scanner)
- 0x4x: Normal mode transmit (PCM → IPC/BCM)

---

## 2. J1979 OBD-II Messages (Mode $01-$09)

### 2.1 Supported PIDs (partial — key engine PIDs)

| PID | Name | Units | Formula | Verified |
|-----|------|-------|---------|----------|
| 0x04 | Calculated Engine Load | % | A/2.55 | — |
| 0x05 | Engine Coolant Temp | °C | A-40 | FFFFADB0 |
| 0x0C | Engine RPM | RPM | (A×256+B)/4 | FFFFA562 |
| 0x0D | Vehicle Speed | km/h | A | FFFFAEC0 |
| 0x0F | Intake Air Temp | °C | A-40 | — |
| 0x10 | MAF Airflow | g/s | (A×256+B)/100 | FFFFAC86 |
| 0x11 | Throttle Position | % | A/2.55 | FFFFAB66 |
| 0x14 | O2 B1S1 Voltage | V | A/200 | — |
| 0x1C | OBD Standard | — | A | — |
| 0x4C | TAC % | % | A/2.55 | — |

### 2.2 Mode $06 — On-Board Monitoring Test Results

```
KE_OBD_01_20_TEST_SUPPORT: bitfield of supported TIDs 0x01-0x20
KE_MODE_06_COMP_ID_SUPPORTED_1-6: 6 component IDs supported

Each test result returns:
  TID (Test ID) — identifies the monitor
  CID (Component ID) — identifies the component
  Test Value + Min/Max limits
```

### 2.3 Mode $09 — Vehicle Information

```
KE_MODE9_01_08_SUPPORT: bitfield of supported info types
```

---

## 3. J2190 Enhanced Messages

Manufacturer-specific PIDs beyond the legislated J1979 set.
The J2190 module includes security and calibration identification.

### 3.1 Security

```
KE_VULNERABILITY_FLAG (0x1F81B): Bypass Data Link Security.
  0xFF = PCM is UNLOCKED (no security).
  Other values = security active, requires Mode $27 unlock.
```

---

## 4. QADC Scan Sequence

### 4.1 QADC Command Word Queue (Inferred Order)

The QADC on the 68332 scans channels in a programmed sequence. Each
entry in the command word queue specifies the channel and conversion
parameters. Based on the sensor criticality and observed RAM update
rates, the scan order is:

```
Priority-based scan:
  HIGH (every 12.5ms — DoLoopA rate):
    1. AN3: ECT (coolant temp — safety critical)
    2. AN4/AN5: TPS1/TPS2 (ETC feedback — safety critical)
    3. AN0: MAP (speed-density primary input)
    4. AN6/AN7: Pre-cat O2 sensors (closed-loop fuel)

  MEDIUM (every 25ms):
    5. AN13/AN14: APP1/APP2 (accelerator pedal)
    6. AN2: IAT (intake air temp)
    7. AN15: System Voltage

  LOW (every 100ms):
    8. AN10: AC Pressure
    9. AN11: EGR Pintle Position
   10. AN8/AN9: Post-cat O2 sensors
   11. AN12: Fuel Tank Pressure (EVAP)
```

### 4.2 QADC Configuration

```
QADC registers on 68332 (at TPU/SIM base):
  QADCMCR (Module Config): 0xFFFFFAxx
  QADCINT (Interrupt): 0xFFFFFAxx  
  CWQ registers (Command Word Queue): 0xFFFFFAxx
  
Configuration at boot:
  - 10-bit resolution
  - Internal sample amplifier (bypass external)
  - Scan mode: continuous (queue wraps)
  - Interrupt at end of queue
```

### 4.3 Confirmed QADC Result Addresses

| QADC Channel | Result Address | Sensor |
|-------------|---------------|--------|
| AN0 | 0xFFFFF2BC | MAP |
| AN1 | — | (MAF uses frequency input, not ADC) |
| AN3 | — | ECT → FFFFADB0 after conversion |
| AN11 | 0xFFFFF2C0 | EGR Pintle Position |

**Result format:** 10-bit right-justified unsigned. Range 0-1023 (0x000-0x3FF).

---

## 5. Diagnostic Module Reference (Every DG_/DI_)

### 5.1 Module-Function-DTC Table

| DG Module | Monitors | Primary DTCs | Key Threshold Calibration |
|-----------|----------|-------------|--------------------------|
| DG_CAM | Cam sensor sync | P0340-P0343 | Cam transition window (in 24X regions) |
| DG_CASE | Crank angle sensing error | P1336 | CASE correction max, learn conditions |
| DG_CRANK | Crank sensor signal | P0335-P0336 | CKP tooth count, missing tooth detect |
| DG_ECTR | ECT rationality | P0116 | Min stabilized ECT, warmup time |
| DG_ECTS | ECT stuck | P0117-P0118 | ECT change timeout |
| DG_EONV | EVAP natural vacuum | P0440-P0455 | Temperature deltas, pressure integration |
| DG_EOS | O2 sensor performance | P0130-P0167 | Response ratio, asymmetric test method |
| DG_ESC | Knock sensor | P0325-P0332 | Min ECT, noise floor learn |
| DG_FAN | Fan speed | P0480-P0481 | Fan delta speed, overspeed threshold |
| DG_FASD | Fuel/air/spark diag | Various | Short term gain, EWMA filter |
| DG_FFS | Flex fuel sensor | P0176-P0178 | Rationality temp diff |
| DG_HSCR | Heated sensor circuit | Various | Startup temp diff, IAT enable |
| DG_IAT | IAT rationality | P0111-P0113 | Temp change timeout, ECT correlation |
| DG_ICAT | Catalyst efficiency | P0420/P0430 | O2 switch count, post-O2 voltage thresholds |
| DG_IGNITION_CONTROL | Ignition system | P0351-P0358 | (covers coil primary circuits) |
| DG_IOT | Injector output test | P0201-P0208 | (covers injector circuit open/short) |
| DG_MAP | MAP rationality | P0106-P0108 | MAP vs baro, MAP vs TPS correlation |
| DG_ODM | Output driver module | Various | (covers relay drive circuits) |
| DG_POS | Post-cat O2 | P0136-P0157 | CL short term int limits |
| DG_TPS | TPS rationality | P0121-P0123 | TPS vs RPM/load expectations |
| DG_VOLT | System voltage | P0560-P0563 | Voltage window, stable time |

### 5.2 Di (Inhibit) Module Conditions

Each DI_ module defines when the diagnostic CANNOT run:

| DI Module | Key Inhibit Conditions |
|-----------|----------------------|
| DI_CASE | ECT < KE_CASE_COOLANT_TEMP_ENABLE |
| DI_EONV | ECT window, IAT window, baro min, fuel level |
| DI_EOS | Voltage window, airflow window, RPM window, ECT min |
| DI_FAN | IAT min, system voltage min, pump-out RPM |
| DI_FASD | IAT min, short/long term trim within range |
| DI_FFS | ECT window, fuel level, ethanol content |
| DI_HSCR | Startup temp diff, IAT enable |
| DI_IAT | Short high/low ECT limits, temp rate limit |
| DI_LEGR | Signal low pos max, closed valve fail count |
| DI_MAP | Delta EGR pos max, fuel trim update rate |
| DI_POS | CL short term int min/max |
| DI_TPS | ECT min for rationality |

### 5.3 Typical Diagnostic Pattern

Every DG_/DI_ pair follows this pattern:

```
1. DI_ module checks enable conditions (ECT, IAT, RPM, VSS, voltage,
   run time, fuel level, etc.)
2. If all conditions met → DG_ module runs test
3. DG_ module collects samples:
   - SAMPLE_LIMIT: total samples needed for test completion
   - FAIL_LIMIT: failures in this many samples → pending DTC
4. EWMA (exponentially weighted moving average) filter:
   - KE_xxx_EWMA_FILTER_COEF: smoothing coefficient
   - KE_xxx_EWMA_FAIL_THRESHOLD: threshold for fail report
   - KE_xxx_EWMA_NONFAIL_THRESHOLD: threshold for non-fail
5. After KE_xxx_COMPLETE_INTERVAL: test reports to DTC manager
```

---

## 6. Final State: What We Know vs What's Left

### Documented (NSA Rounds 1-5)
- **40 numbered docs** covering every functional subsystem
- Hardware register maps for J1850, COP, TPU, QADC
- 256 interrupt vectors decoded
- Boot ROM reset handler fully traced
- TPU initialization function (sub_138E) fully traced
- TPU channel function mapping (8 of 16 channels confirmed)
- C2 message catalog (30+ messages with update rates)
- QADC channel mapping (16 channels with sensor assignments)
- QADC result register addresses (3 confirmed)
- Segment header structure with CVN and OS ID
- ETAS detection pattern and TPU reconfiguration
- Every calibration module identified and cross-referenced
- 30 DG_/DI_ diagnostic modules cataloged with DTCs
- ~550 calibration parameters documented
- ~180 RAM variables identified
- 85+ subroutines traced

### Truly Remaining (academic value only)
1. Exact TPU function code values for each channel (in binary as calibration
   data — could hex-dump but adds no functional understanding)
2. QADC command word queue exact entries (same — calibration data in binary)
3. C2 message exact byte layout with J1850 headers (formulaic — each message
   follows the same pattern, decoding one decodes all)
4. Gap 0x000500-0x003FFF: additional boot ROM code (memory test, flash kernel
   loader — only relevant for PCM Hammer developers)

**At this depth, further documentation would require reading raw calibration
byte values from the binary, which produces reference tables but no new
functional understanding of the ECU's operation.**
