# P59 PCM (OS 12587603) — Idle Control & Sensor Signal Chains

> Traced from `/f/github/12587603/12587603-2004-Corvette-M6.sanitized.asm`  
> 936,975-line disassembly, Motorola 68000 (68330 CPU)
> OS: 12587603 — 2004 Corvette M6

---

## 1. SENSOR SIGNAL CHAINS

### 1.1 MAP Sensor (Manifold Absolute Pressure) — ADC → kPa

**Raw ADC source:** `unk_FFFFF2BC` (hardware TPU/memory-mapped ADC register)

**Conversion chain — Function `sub_807E0` (0x303844):**

```
Step 1:   d3 = unk_FFFFF2BC         ; read raw ADC word
Step 2:   d3 = d3 >> 2               ; lsr.w #2 — discard 2 LSBs (noise)
Step 3:   d3 = d3 << 8               ; asl.w #8 — shift to upper byte
Step 4:   unk_FFFFB290 = d3          ; store Filtered_ADC_Count (8-bit in upper byte)
Step 5:   d3 = d3 * KE_MAP_SENSOR_SCALE_FACTOR   ; mulu.w $12E3 = 4835 (kPa/Count × 256)
Step 6:   d3 = d3 >> 16              ; lsr.l #8; lsr.l #8 — divide by 65536
Step 7:   d3 = d3 + KE_MAP_SENSOR_OFFSET         ; add.w $211 = 5.29 kPa
Step 8:   clamp: 0 ≤ d3 ≤ $14FF      ; ~105 kPa (internal format)
Step 9:   unk_FFFFB296 = d3          ; MAP_kPa (internal format, ×51.2 per LSB)
```

**Calibration constants:**

| Name | Address | Value | Units | Description |
|------|---------|-------|-------|-------------|
| `MANIFOLD_KE_MAP_SENSOR_SCALE_FACTOR` | 0x195B8 | `$12E3` (4835) | kPa/Count (×256) | ~4.84 kPa per ADC count after descaling |
| `MANIFOLD_KE_MAP_SENSOR_OFFSET` | 0x195BA | `$211` (529) | kPa (×100) | ~5.29 kPa offset |
| `MANIFOLD_KE_MAP_DEFAULT_SLOPE` | 0x1958E | `$500` (1280) | kPa/Gram/Cyl (×256) | Default MAP from MAF |
| `MANIFOLD_KE_MAP_DEFAULT_MINIMUM` | 0x19592 | `$340` (832) | kPa (×100) | Minimum default MAP from MAF |
| `MANIFOLD_KE_MAP_DEFAULT_ENGINE_NOT_RUNNIN` | 0x195B2 | `$1200` (46.08) | kPa (×256) | Default MAP when engine not running |
| `MANIFOLD_KV_MAP_DEFAULT_OFFSET` | — | Table | kPa (×100) | RPM-based offset for default MAP calc |

**Internal format:** The final MAP value is stored at `unk_FFFFB296` in an internal format where 1 LSB = 1/51.2 kPa (approx 0.0195 kPa). Max clamp at `$14FF` ≈ 105.0 kPa.

**Output variables:**
- `unk_FFFFB296` — filtered MAP sensor reading (kPa, internal format)
- `unk_FFFFB294` — final MAP for use (sensor or default if faulted)
- `unk_FFFFB298` — vacuum = baro − MAP (clamped to 0..$1000)
- `unk_FFFFAEF2` — vacuum (full range)
- `unk_FFFFAEF4` — vacuum / 2

**Redundant MAP (Baro source):** Function `sub_8093C` (0x304008) reads `unk_FFFFF2BA` and applies the same scale factor and offset, storing to `unk_FFFFB292`. Typically used as the barometric pressure reference.

---

### 1.2 ECT (Engine Coolant Temperature) — Thermistor Lookup

**Raw ADC source:** `unk_FFFFADB6`

**Conversion chain:**

```
Step 1:   d3 = unk_FFFFADB6         ; read ECT ADC count
Step 2:   d3 = d3 + $400             ; addi.w #$400 (bias to unsigned lookup range)
Step 3:   d3 = tblu.w($15724, d3)    ; 17-entry linear lookup table (16-bit entries)
Step 4:   stored as coolant temp     ; used throughout as Deg_C internal format
```

**Lookup table:** at ROM address `0x15724` (`unk_15724`) — 17 entries, 16-bit each.

This table translates the biased ADC count to °C (internal format). The `+$400` bias puts the ADC reading into the unsigned 16-bit range for the table lookup instruction `tblu.w`.

**Usage pattern:** The ECT value at `unk_FFFFADB6` appears in hundreds of locations, compared against coolant temperature calibrations like:
- `CCP_KE_COOLANT_TEMPERATURE_STARTRUN` (0x8EC6)
- `FUEL_ST_KV_CLOSED_LOOP_COOLANT_TEMPERATU` (0xED1A)
- `IAC_RPM_KE_COOLANT_TEMPERATURE_LOW_LIMIT` (0xF6DA)
- `IAC_RPM_KE_COOLANT_TEMPERATURE_HIGH_LIMI` (0xF6DC)

**Key calibrations referencing ECT:**

| Name | Address | Value | Units | Purpose |
|------|---------|-------|-------|---------|
| `IAC_RPM_KE_COOLANT_TEMPERATURE_LOW_LIMIT` | 0xF6DA | — | °C | Min ECT for heater perf idle speed offset |
| `IAC_RPM_KE_COOLANT_TEMPERATURE_HIGH_LIMI` | 0xF6DC | — | °C | Max ECT for heater perf idle speed offset |
| `CCP_KE_COOLANT_TEMPERATURE_STARTRUN` | 0x8EC6 | — | °C | Coolant threshold for purge enable delay |
| `FUEL_ST_KV_CLOSED_LOOP_COOLANT_TEMPERATU` | 0xED1A | — | °C | ECT above which closed loop is allowed |

---

### 1.3 IAT (Intake Air Temperature) — Thermistor

**Internal variable:** `unk_FFFFB3EA` (already calibrated to internal °C format)

**OBD-II PID 000F conversion (GetPid_000F_IntakeAirTemperature at 0x205824):**

```
Step 1:   d0 = unk_FFFFB3EA         ; internal IAT value (raw scaled format)
Step 2:   d0 = d0 + d0              ; add.w d0,d0 — multiply by 2
Step 3:   d0 = d0 / $33             ; divs.w #$33 — divide by 51
Step 4:   d0 = d0 + $28             ; addi.w #$28 — add 40
Step 5:   Result = °C               ; OBD-II IAT in degrees Celsius
```

**Conversion formula:** `IAT_°C = (IAT_internal × 2 / 51) + 40`

**Diagnostic calibrations:**

| Name | Address | Value | Units | Purpose |
|------|---------|-------|-------|---------|
| `DI_AIR_KE_AIRD_INTAKE_AIR_TEMP_MIN` | 0x16D56 | — | °C | Min IAT to enable AIR diagnostic |
| `DI_AIR_KE_AIRD_INTAKE_AIR_TEMP_MAX` | 0x16DCC | — | °C | Max IAT to enable AIR diagnostic |
| `DI_ICAT_KE_CAT_INTAKE_AIR_TEMP_MAX` | 0x17B72 | — | °C | Max IAT for catalyst test |
| `DI_ICAT_KE_CAT_INTAKE_AIR_TEMP_MIN` | 0x17B74 | — | °C | Min IAT for catalyst test |
| `DI_IDLE_KE_IAC_INTAKE_AIR_TEMP_MIN` | 0x17BEE | — | °C | Min IAT for IAC diagnostic |

---

### 1.4 TPS (Throttle Position Sensor) — ADC Chain

**Raw ADC source:** `unk_FFFFF2FC` (hardware ADC register)

**OBD-II PID 1143 conversion (`GetPid_1143_ThrottlePositionSensor` at 0x194889):**

```
Step 1:   d0 = unk_FFFFF2FC         ; read TPS ADC raw
Step 2:   d0 = d0 >> 2               ; lsr.w #2 — discard 2 LSBs
Step 3:   d0 = d0 << 8               ; asl.w #8 — shift to upper byte
Step 4:   d0 = d0 >> 8               ; lsr.w #8 — extract 8-bit result
Step 5:   d0 = 8-bit ADC count       ; 0..255 raw TPS
```

**Processed TPS (percent):** `unk_FFFFAB64` — TPS position in degree-percent internal format. Used by OBD-II PID 1151 (`GetPid_1151_ThrottlePositionSensorNormalizedinDegreesPercent`) and throughout the idle control logic.

**Usage in idle control:**
- `unk_FFFFAB66` is used in `DecideIdleMode` to check `IAC_REGULATORS_KE_EARLY_PID_ENTRANCE_MAX_TPS` threshold
- `IAC_MOTOR_KE_IMRR_THROTTLE_POSITION` (0xF54C, `$1400`) — Minimum TPS for IAC running reset

**Calibrations:**

| Name | Address | Value | Units | Purpose |
|------|---------|-------|-------|---------|
| `IAC_REGULATORS_KE_EARLY_PID_ENTRANCE_MAX_TPS` | 0x56853 | 0 | Percent | Max TPS for early PID entrance |
| `IAC_AIRFLOW_KE_THROTTLE_CRACKER_ENABLE_THRES` | 0xED48 | — | MPH | VSS to enable throttle cracker |
| `IAC_AIRFLOW_KE_THROTTLE_CRACKER_DISABLE_THRE` | 0xED46 | — | MPH | VSS to disable throttle cracker |
| `IAC_AIRFLOW_KE_THROTTLE_FOLLOWER_TPS_HYSTERE` | 0xEDC0 | — | Percent | TPS hysteresis for throttle follower |
| `IAC_MOTOR_KE_IMRR_THROTTLE_POSITION` | 0xF54C | `$1400` | Percent | Min TPS to trigger IAC running reset |

---

### 1.5 MAF (Mass Air Flow) — Frequency → grams/sec

**Raw MAF frequency:** `unk_FFFFAC84` — MAF sensor frequency in Hz (directly readable via PID 1250)

**OBD-II PID 0010 conversion (`GetPid_0010_MassAirFlow` at 0x205817):**

```
Step 1:   d0 = unk_FFFFAC82           ; internal airflow variable
Step 2:   d0 = d0 * $19               ; mulu.w #$19 — multiply by 25
Step 3:   d0 = d0 >> 5                ; lsr.l #5 — divide by 32
Step 4:   d0 = grams/sec              ; OBD-II MAF in g/s
```

**Conversion formula:** `MAF_gps = (MAF_internal × 25) / 32 = MAF_internal × 0.78125`

The actual MAF sensor frequency-to-g/s conversion likely happens elsewhere in the TPU input processing. `unk_FFFFAC82` is the already-processed internal format.

**Calculated Load (PID 0004) uses MAF:**

```
Calc_Load = (unk_FFFFAC82 * $1400) / C2_PIDS_KE_PEAK_AIRFLOW_SEALEVEL
         ≈ MAF_grams * 20 / peak_airflow_at_sealevel
```

**Diagnostic calibrations:**

| Name | Address | Value | Units | Purpose |
|------|---------|-------|-------|---------|
| `DG_MAF_KE_MAFD_FREQ_HIGH_THRESH` | 0x16B14 | — | Hz | High frequency failure threshold |
| `DG_MAF_KE_MAFD_FREQ_LOW_THRESH` | 0x16B1A | — | Hz | Low frequency failure threshold |
| `DI_MAF_KE_MAFD_FREQ_RPM_MIN` | 0x16B54 | — | RPM | Min RPM for MAF frequency test |
| `DI_MAF_KE_MAFD_FREQ_ENG_RUN_TIME_MIN` | 0x16B4E | — | Sec | Min run time for MAF frequency test |

---

## 2. IDLE CONTROL

### 2.1 Idle Control Architecture

The idle control system is organized as a hierarchical state machine with these sub-systems:

| Function | Address | Purpose |
|----------|---------|---------|
| `sub_35B80` | 0x168016 | Main idle loop entry (called from DoLoopC) |
| `DecideIdleMode` | 0x173174 | Idle mode state machine — decides control mode |
| `sub_37C54` | 0x172235 | Initialize idle parameters (early PID) |
| `sub_37D56` | 0x172361 | IAC motor running reset detection |
| `sub_37DEE` | 0x172438 | IACV step frequency selection |
| `sub_37FAE` | 0x172677 | IAC main periodic task (calls stepper & reset) |
| `sub_37FC2` | 0x172689 | IAC lost motor reset (stepper re-homing) |
| `DetermineIdleContribution` | 0x135037 | ETC idle area contribution |

---

### 2.2 Idle Speed Target Calculation

**Desired idle speed location:** `unk_FFFFAE3A`

This value is calculated upstream (by sub_35B80 and its callees) based on:
- Coolant temperature (ECT from `unk_FFFFADB6`)
- Transmission state (PN vs Drive)
- A/C status
- Heater performance mode
- VSDI (Vehicle Speed Dependant Idle) — `IAC_AIRFLOW_KV_VSDI_DESIRED_IDLE_SPEED` table

**OBD-II PID 1192** (`GetPid_1192_DesiredIdleSpeed` at 0x195068):
```
d0 = unk_FFFFAE3A >> 6     ; divide by 64, result in RPM/4
clamp to 0..255
```

**Speed error calculation** (in `DecideIdleMode`):
```
Speed_Error = unk_FFFFA562 - unk_FFFFAE3A    ; actual RPM - desired idle RPM
clamped to ±32767
stored at unk_FFFFA6EE
```

---

### 2.3 DecideIdleMode — Idle Mode State Machine

**Function:** `DecideIdleMode` (0x173174)  
**Inputs:**
- `unk_FFFFA562` — actual engine speed (RPM)
- `unk_FFFFAE3A` — desired idle speed (RPM)
- `unk_FFFFAB66` — TPS position (percent)
- `unk_FFFFAEBC` — vehicle speed (MPH)
- `unk_FFFFA6F7` — current idle state
- `unk_FFFFA723` — PID enable flags (bits 7,6,5,4,3,2,1)
- `unk_FFFFAD23` — engine run state

**Outputs:**
- `unk_FFFFA6EE` — speed error (RPM)
- `unk_FFFFA6F0` — speed error for early PID
- `unk_FFFFA6F5` — stall saver active flag
- `unk_FFFFA6F7` — idle state transition
- `unk_FFFFA6FA` — early PID mode flag
- `unk_FFFFA716` — P-gain term
- `unk_FFFFA6FE` — D-gain term
- `unk_FFFFA720` — D-gain term (stall saver)
- `unk_FFFFA704` — lightly filtered RPM
- `unk_FFFFA702` — heavily filtered RPM
- `unk_FFFFA700` — RPM ratio (light/heavy)
- `unk_FFFFA724` — throttle cracker enable flag

**State machine modes defined by `unk_FFFFA6F7`:**
- **0** = No idle control (engine off or above threshold)
- **1** = Early PID (RPM close to target, TPS < threshold)
- **2** = Full PID control  
- **3** = Startup delay (under-speed condition)

**PID term enable flags** (`unk_FFFFA723`):
- Bit 7: P-gain control enabled
- Bit 6: D-gain control enabled  
- Bit 5: I-gain control enabled
- Bit 4: Idle spark control enabled
- Bit 3: P-gain just transitioned
- Bit 2: D-gain just transitioned
- Bit 1: I-gain just transitioned

**Transition delays** (each checked against time since entering mode):
- `IAC_REGULATORS_KE_DELAY_P_CONTROL` (0x56862) — `$D0` seconds
- `IAC_REGULATORS_KE_DELAY_D_CONTROL` (0x56868) — `$D0` seconds  
- `IAC_REGULATORS_KE_DELAY_I_CONTROL` (0x56865) — `$D0` seconds
- `IAC_REGULATORS_KE_DELAY_IDLE_SPARK` (0x56871) — `$D0` seconds
- `IAC_REGULATORS_KE_START_UP_PID_DELAY` (0x56859) — `$C0` seconds

---

### 2.4 PID Gains — Proportional, Derivative

**P-gain lookup:** Speed error in `d3/d4` is used as an index into calibrated tables. Four tables selectable by transmission mode and A/C status:

| Table | Address | Condition |
|-------|---------|-----------|
| `IAC_REGULATORS_KV_P_SPEED_HIGH_IN_PARK_NEUTRAL` (pos error) | 0xF660 | PN, no AC |
| `IAC_REGULATORS_KV_P_SPEED_HIGH_IN_DRIVE` (pos error) | 0xF630 | Drive, no AC |
| `IAC_REGULATORS_KV_P_SPEED_HIGH_IN_DRIVE_AC` (pos error) | 0xF648 | Drive, AC on |
| Negative error tables | 0xF678 | PN neg error |
| Negative error tables | 0xF690 | PN_Drive neg error (AC) |
| Negative error tables | 0xF6A8 | PN_Drive neg error (no AC) |

All use `tbls.w` (signed table lookup) with 16-bit signed entries.

**D-gain lookup:** Two tables, selected by whether engine speed is increasing or decreasing:

| Table | Address | Condition |
|-------|---------|-----------|
| `IAC_REGULATORS_KV_D_SPEED_INCREASING` | 0xF5BC | RPM increasing |
| `IAC_REGULATORS_KV_D_SPEED_DECREASING` | 0xF5A8 | RPM decreasing |

**Derivative term calculation:**
```
RPM_ratio = lightly_filtered_RPM / heavily_filtered_RPM × 2000
clamped to 1000..3000

If RPM above 2000 (increasing):
    d3 = RPM_ratio - 2000
    if d3 ≤ 200:  d3 = d3 * 25166 / 3 / 819  (steep ramp)
    elif d3 < 300: d3 = (d3 * 25166 - 5046480) / 3 / 3277 + 2048
    else: d3 = 2302
    tbls.w(0xF5BC, d3)  →  negate → stored as D-term

If RPM below 2000 (decreasing):  
    same calculation but uses table at 0xF5A8
```

The derivative term normally stored at `unk_FFFFA6FE`. Under stall saver conditions, it multiplies by 8 and stored at `unk_FFFFA720`.

**I-gain (Integral):** Managed through a separate integrator routine. Flag bit 5 in `unk_FFFFA723` enables I-control after the delay expires. The integral term is accumulated in `unk_FFFF94C6` and bounded.

---

### 2.5 Idle Spark Control

Idle spark is delayed (bit 4 of `unk_FFFFA723`) for `IAC_REGULATORS_KE_DELAY_IDLE_SPARK` seconds after entering full PID mode. When active, the idle control system can command spark retard to reduce engine speed when IAC airflow is at minimum. The ETC throttle position has limits via `ETC_THROT_KE_MAX_IDLE_THROTTLE_POSITION` ($3A9) and `ETC_R_THROTTLE_KE_R_MAX_IDLE_THROTTLE_POSITION` ($752).

---

### 2.6 IAC (Idle Air Control) Stepper Motor

**Motor control functions:**

| Function | Address | Purpose |
|----------|---------|---------|
| `sub_37D56` | 0x172361 | Running reset detection (vehicle speed + TPS > threshold) |
| `sub_37DEE` | 0x172438 | Step frequency selection (high/low vacuum) |
| `sub_37EE6` | 0x172577 | IAC coil phase control (step out / close) |
| `sub_37F4A` | 0x172627 | IAC coil phase control (step in / open) |
| `sub_37FC2` | 0x172689 | Lost motor reset (full re-home cycle) |

**IAC motor state register:** `byte_FF86B0`:
- 0 = Idle (no active stepping)
- 1 = Stepping open (increase airflow)
- 2 = Stepping closed (decrease airflow)
- 3 = Running reset in progress
- 4 = Post-reset (fully closed, re-homing)

**Current IAC position:** `word_FF86AE` (0-310 steps, max = $136)

**Output to TPU:** The IAC stepper uses TPU channels 0x10 and 0x12 (referenced in sub_37EE6/sub_37F4A via `sub_FC0` calls). The step frequency is stored in `unk_FFFFB144`:

**Step frequency selection** (in sub_37DEE):
```
if vacuum > IAC_MOTOR_KE_MANIFOLD_VACUUM_FOR_LOW_FREQU:
    frequency = IAC_MOTOR_KE_IACV_LOW_FREQUENCY_STEP   ($C80 = 3200 Hz)
elif vacuum < IAC_MOTOR_KE_MANIFOLD_VACUUM_FOR_HIGH_FREQ:
    frequency = IAC_MOTOR_KE_IACV_HIGH_FREQUENCY_STEP  ($1900 = 6400 Hz)
else:
    frequency = unchanged (hysteresis band)

Period = $16E360 / frequency  (timer counts)
```

**IAC motor calibrations:**

| Name | Address | Value | Units | Purpose |
|------|---------|-------|-------|---------|
| `IAC_MOTOR_KE_DEFAULT_PARK_POSITION` | 0xF4BC | `$136` (310) | Steps | Default park position at powerup |
| `IAC_MOTOR_KE_IACV_STEP_RANGE` | 0xF4BE | `$136` (310) | Steps | Max stepping range |
| `IAC_MOTOR_KE_IACV_LOW_FREQUENCY_STEP` | 0xF4C0 | `$C80` | Hz | Step rate, high vacuum |
| `IAC_MOTOR_KE_IACV_HIGH_FREQUENCY_STEP` | 0xF4C2 | `$1900` | Hz | Step rate, low vacuum |
| `IAC_MOTOR_KE_MANIFOLD_VACUUM_FOR_LOW_FREQU` | 0xF4C4 | `$200` | kPa | High-vac threshold (low freq entry) |
| `IAC_MOTOR_KE_MANIFOLD_VACUUM_FOR_HIGH_FREQ` | 0xF4C6 | — | kPa | Low-vac threshold (high freq entry) |
| `IAC_MOTOR_KE_MINIMUM_STEP_VOLTAGE` | 0xF4CA | `$900` | Volts | Min ign voltage to step |
| `IAC_MOTOR_KE_IMRR_VEHICLE_SPEED` | 0xF54A | `$7FFF` | MPH | Min VSS for running reset |
| `IAC_MOTOR_KE_IMRR_THROTTLE_POSITION` | 0xF54C | `$1400` | Percent | Min TPS for running reset |
| `IAC_MOTOR_KE_IMLR_DEADBAND_SPEED_ERROR` | 0xF546 | `$FFFF` | RPM | Max error deadband for lost-motor logic |
| `IAC_MOTOR_KV_AREA_TO_IACV_STEPS` | 0xF4CC | Table | Steps/mm² | Effective-area to IAC steps lookup |
| `IAC_MOTOR_KV_IMLR_STEP_INCREMENT` | 0xF56E | 0 | Steps | Step size for lost-motor re-home |

**IAC airflow (effective area) calibrations:**

| Name | Address | Units | Purpose |
|------|---------|-------|---------|
| `IAC_AIRFLOW_KE_IDLE_AREA_SCALAR` | 0xED44 | Scalar | Scalar for idle effective area |
| `IAC_AIRFLOW_KE_MAX_DESIRED_IDLE_EFF_AREA` | 0xED7A | mm² | Max desired idle effective area |
| `IAC_AIRFLOW_KE_OFFIDLE_SCALAR` | 0xED82 | Scalar | Off-idle effective area scalar |
| `IAC_AIRFLOW_KE_START_UP_DECAY_INITIAL` | 0xEDBE | — | Initial startup decay airflow |
| `IAC_AIRFLOW_KE_MAP_FOR_IAC_RESET` | 0xED78 | kPa | MAP threshold for IAC park position |
| `IAC_AIRFLOW_KV_START_UP_AIRFLOW` | 0xEFBE | Table | Startup airflow vs ECT |
| `IAC_AIRFLOW_KV_WARMED_UP_AIRFLOW_DRIVE` | 0xF04C | Table | Warmed-up airflow in drive |
| `IAC_AIRFLOW_KV_WARMED_UP_AIRFLOW_PARK_NEUTRA` | 0xF06C | Table | Warmed-up airflow in PN |

---

### 2.7 Throttle Follower / Cracker

**Throttle follower:** Adds airflow proportional to throttle position during off-idle transitions to prevent engine RPM dips when the throttle closes.

**Lookup table:** `IAC_AIRFLOW_KV_THROTTLE_FOLLOWER_AIRFLOW` (0xF02A) — TPS-indexed table producing airflow in g/s.

**Throttle cracker:** Adds airflow when vehicle is moving (above 0 MPH) to prevent RPM dips during deceleration and clutch-in events. Controlled by vehicle speed crossing thresholds.

**Enable/disable calibrations:**

| Name | Address | Units | Purpose |
|------|---------|-------|---------|
| `IAC_AIRFLOW_KE_THROTTLE_CRACKER_ENABLE_THRES` | 0xED48 | MPH | VSS ≥ this → enable cracker |
| `IAC_AIRFLOW_KE_THROTTLE_CRACKER_DISABLE_THRE` | 0xED46 | MPH | VSS ≤ this → disable cracker |
| `IAC_AIRFLOW_KE_THROTTLE_FOLLOWER_TPS_HYSTERE` | 0xEDC0 | Percent | TPS hysteresis for follower activation |

**Throttle cracker airflow tables:**

| Name | Address | Purpose |
|------|---------|---------|
| `IAC_AIRFLOW_KV_THROTTLE_CRACKER_AF_DECAY` | 0xEFE6 | Decay rate after cracker airflow |
| `IAC_AIRFLOW_KA_THROTTLE_CRACKER_AIRFLOW` | 0xF11C | Cracker airflow vs. vehicle speed |
| `IAC_AIRFLOW_KV_PN_EXTENDED_THROT_CRACKER` | 0xF3D6 | Extended cracker airflow in PN |

**RPM follower:** `IAC_AIRFLOW_KV_RPM_FOLLOWER_AIRFLOW` (0xEDFC) provides airflow offset based on RPM to handle accessory loads that may drag idle speed.

---

### 2.8 Additional Idle Airflow Compensators

| Table/Calibration | Address | Purpose |
|-------------------|---------|---------|
| `IAC_AIRFLOW_KV_AC_OFF_PI_DELAY` | 0xF2B4 | Delay after A/C disengaged |
| `IAC_AIRFLOW_KV_AC_ON_PI_DELAY` | 0xF2D0 | Delay after A/C engaged |
| `IAC_AIRFLOW_KE_AC_OFFSET_FILTER_CONSTANT` | 0xED4A | A/C offset filter rate |
| `IAC_AIRFLOW_KE_COOLING_FAN_CORRECTION` | 0xED4E | Fan-on airflow offset |
| `IAC_AIRFLOW_KE_DRIVE_CORRECTION_HIGH` | 0xED58 | Drive correction upper limit |
| `IAC_AIRFLOW_KE_DRIVE_CORRECTION_LOW` | 0xED5A | Drive correction lower limit |
| `IAC_AIRFLOW_KV_SQUARE_ROOT_AIR_TEMPERATURE` | 0xEF9E | IAT density correction |
| `IAC_AIRFLOW_KV_GEAR_TF_DELAY_TIME` | 0xEEFC | P→D/N→D transition delay |
| `IAC_AIRFLOW_KV_BREAKAWAY_AIRFLOW_VALUE` | 0xEE26 | Torque converter breakaway airflow |
| `IAC_AIRFLOW_KV_BREAKAWAY_FRICTION_AIRFLOW` | 0xEE3A | Breakaway friction airflow |

---

## 3. KEY RAM ADDRESSES (Sensor & Idle Variables)

| Address | Symbolic Name (from IDA) | Content |
|---------|--------------------------|---------|
| `FFFFF2BC` | `unk_FFFFF2BC` | MAP sensor raw ADC |
| `FFFFF2BA` | `unk_FFFFF2BA` | Baro/MAP-2 sensor raw ADC |
| `FFFFF2FC` | `unk_FFFFF2FC` | TPS sensor raw ADC |
| `FFFFAB64` | `unk_FFFFAB64` | TPS percentage (processed) |
| `FFFFAB66` | `unk_FFFFAB66` | TPS (used in idle checks) |
| `FFFFADB6` | `unk_FFFFADB6` | ECT (calibrated °C internal) |
| `FFFFB3EA` | `unk_FFFFB3EA` | IAT (calibrated °C internal) |
| `FFFFAC82` | `unk_FFFFAC82` | MAF internal (→ g/s via *25/32) |
| `FFFFAC84` | `unk_FFFFAC84` | MAF frequency (Hz) |
| `FFFFB290` | `unk_FFFFB290` | Filtered MAP ADC count |
| `FFFFB296` | `unk_FFFFB296` | MAP kPa (internal format) |
| `FFFFB294` | `unk_FFFFB294` | MAP kPa (used by code) |
| `FFFFB298` | `unk_FFFFB298` | Vacuum (baro − MAP) |
| `FFFFB28E` | `unk_FFFFB28E` | Filtered Baro ADC count |
| `FFFFB292` | `unk_FFFFB292` | Baro kPa (internal format) |
| `FFFFAE3A` | `unk_FFFFAE3A` | Desired idle speed (RPM × 64) |
| `FFFFA562` | `unk_FFFFA562` | Actual engine speed (RPM) |
| `FFFFAEBC` | `unk_FFFFAEBC` | Vehicle speed (MPH) |
| `FFFFA6EE` | `unk_FFFFA6EE` | Speed error for idle control |
| `FFFFA716` | `unk_FFFFA716` | P-gain proportional term |
| `FFFFA6FE` | `unk_FFFFA6FE` | D-gain derivative term |
| `FFFFA720` | `unk_FFFFA720` | D-gain (stall saver mode) |
| `FFFFA704` | `unk_FFFFA704` | Engine speed (lightly filtered) |
| `FFFFA702` | `unk_FFFFA702` | Engine speed (heavily filtered) |
| `FFFFA700` | `unk_FFFFA700` | RPM ratio (light/heavy × 2000) |
| `FFFFA723` | `unk_FFFFA723` | PID/spark enable flags |
| `FFFFA6F7` | `unk_FFFFA6F7` | Idle mode state |
| `FFFFA6FA` | `unk_FFFFA6FA` | Early PID mode flag |
| `FFFFA6F5` | `unk_FFFFA6F5` | Stall saver active flag |
| `FFFFA724` | `unk_FFFFA724` | Throttle cracker enable flag |
| `FFFF94CC` | `unk_FFFF94CC` | Desired idle effective area (mm²) |
| `FFFFB144` | `unk_FFFFB144` | IACV step frequency |
| `FF86AE` | `word_FF86AE` | Current IAC motor position (steps) |
| `FF86B0` | `byte_FF86B0` | IAC motor state |
| `FF86B1` | `byte_FF86B1` | IAC stepping enable |
| `FF86B3` | `byte_FF86B3` | IAC coil phase |

---

## 4. KEY CALIBRATION TABLES LOCATIONS

| Address | Name | Type | Size |
|---------|------|------|------|
| 0x15724 | ECT thermistor lookup table | 17 × 16-bit word | $22 bytes |
| 0xF02A | `IAC_AIRFLOW_KV_THROTTLE_FOLLOWER_AIRFLOW` | TPS-axis table | variable |
| 0xF04C | `IAC_AIRFLOW_KV_WARMED_UP_AIRFLOW_DRIVE` | ECT-axis table | variable |
| 0xF06C | `IAC_AIRFLOW_KV_WARMED_UP_AIRFLOW_PARK_NEUTRA` | ECT-axis table | variable |
| 0xF11C | `IAC_AIRFLOW_KA_THROTTLE_CRACKER_AIRFLOW` | VSS-axis table | variable |
| 0xEDFC | `IAC_AIRFLOW_KV_RPM_FOLLOWER_AIRFLOW` | RPM-axis table | variable |
| 0xEFBE | `IAC_AIRFLOW_KV_START_UP_AIRFLOW` | ECT-axis table | variable |
| 0xF3FA | `IAC_AIRFLOW_KV_VSDI_DESIRED_IDLE_SPEED` | VSS-axis table | variable |
| 0xF4CC | `IAC_MOTOR_KV_AREA_TO_IACV_STEPS` | Area-axis table | variable |
| 0xF5A8 | `IAC_REGULATORS_KV_D_SPEED_DECREASING` | D-term table | variable |
| 0xF5BC | `IAC_REGULATORS_KV_D_SPEED_INCREASING` | D-term table | variable |
| 0xF58E | `IAC_REGULATORS_KV_STALL_SAVER_SPEED_NEUTRAL` | RPM-axis table | variable |
| 0xF576 | `IAC_REGULATORS_KV_STALL_SAVER_SPEED_DRIVE` | RPM-axis table | variable |
| 0xF630 | `IAC_REGULATORS_KV_P_SPEED_HIGH_IN_DRIVE` | P-gain table | variable |
| 0xF648 | `IAC_REGULATORS_KV_P_SPEED_HIGH_IN_DRIVE_AC` | P-gain table | variable |
| 0xF660 | `IAC_REGULATORS_KV_P_SPEED_HIGH_IN_PARK_NEUTRAL` | P-gain table | variable |
| 0xF678 | P-gain negative error (PN) | P-gain table | variable |
| 0xF690 | P-gain negative error (PN+AC) | P-gain table | variable |
| 0xF6A8 | P-gain negative error (Drive) | P-gain table | variable |
| 0x1B282 | `XMSN_IO_KV_LINEAR_HOT_TEMPERATURE_TABLE` | 17 × 16-bit word | Deg C |
| 0x1B2A4 | `XMSN_IO_KV_LINEAR_COLD_TEMPERATURE_TABLE` | 17 × 16-bit word | Deg C |
| 0x195B8 | `MANIFOLD_KE_MAP_SENSOR_SCALE_FACTOR` | 16-bit scalar | $12E3 |
| 0x195BA | `MANIFOLD_KE_MAP_SENSOR_OFFSET` | 16-bit scalar | $211 |

---

## 5. EXECUTION FLOW SUMMARY

### Main Loop (DoLoopC) → Idle Processing
```
DoLoopC:
  → sub_807E0          ; MAP sensor ADC → kPa conversion
  → sub_35B80          ; Main idle processing
      → sub_366BE      ; IAC airflow calculations
      → sub_36066      ; Idle speed target calculation  
      → sub_39792      ; Throttle follower/cracker
      → sub_37D56      ; IAC running reset check
      → sub_37DEE      ; IAC step frequency
      → DecideIdleMode ; Idle mode state machine (PID gains, mode transitions)
      → sub_37FC2      ; IAC lost motor logic
```

### Sensor Processing
```
MAP:   unk_FFFFF2BC → sub_807E0 → unk_FFFFB296 (kPa)
Baro:  unk_FFFFF2BA → sub_8093C → unk_FFFFB292 (kPa)
ECT:   unk_FFFFADB6 (already calibrated via lookup at $15724)
IAT:   unk_FFFFB3EA (internal) → PID 000F: *2 /51 +40 = °C
TPS:   unk_FFFFF2FC → PID 1143: lsr#2;asl#8;lsr#8 = 8-bit ADC
       unk_FFFFAB64 → PID 1151: TPS percent
MAF:   unk_FFFFAC82 → PID 0010: *25 /32 = g/s
       unk_FFFFAC84 → PID 1250: MAF Hz
```

---

*Document generated from disassembly analysis of GM P59 PCM OS 12587603*
*File: 12587603-2004-Corvette-M6.sanitized.asm (936,975 lines)*
