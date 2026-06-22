# P59 PCM Remaining Subsystems — Security/VATS, Transmission Shift Scheduling, CCP

> Traced from: `12587603-2004-Corvette-M6.sanitized.asm` (936,975 lines, P59 68332)
> Platform: 2004 Corvette M6 (manual 6-speed), GMT800 Y-body

---

## 1. Security / VTD (Vehicle Theft Deterrent) — VATS

### 1.1 Overview

The P59 PCM implements GM's VTD (Vehicle Theft Deterrent) system, colloquially known as VATS. The PCM receives a security password from the BCM over Class 2 serial data (J1850 VPW), compares it against stored/learned values, and enables or disables fuel delivery based on the result.

### 1.2 Calibration Parameters

| Address | Symbol | Value | Description |
|---------|--------|-------|-------------|
| 0x1F784 | `VEH_SYS_KE_VTD_CONFIGURATION` | varied | Master VTD enable (bitfield) |
| 0x1FE80 | `VTD_KE_VTD_DIAG_ENABLED` | 1 | Report VTD failures via Class 2 |
| 0x1FE83 | `VTD_KE_VTD_BAD_PASSWORD` | 3 | Bad password counter threshold |
| 0x1FE84 | `VTD_KE_VTD_LEARNED_ENOUGH` | 3 | Auto-learn counter threshold |
| 0x1FE85 | `VTD_KE_VTD_LEARNED_PASSWORD` | 3 | Identical password counter threshold |
| 0x1FE86 | `VTD_KE_VTD_DISABLE_TIME` | 0x280 (640 s) | Fuel disable lockout duration |
| 0x1FE88 | `VTD_KE_VTD_AUTO_LEARN` | 0x17700 (~26.7 hr) | Auto-learn timer |
| 0x1FE8C | `VTD_KE_VTD_C2_INIT` | 0xF0 (240 s) | PCM C2 init timer |
| 0x1FE8E | `VTD_KE_VTD_C2_AUTO_LEARN` | 0x17700 (~26.7 hr) | C2 auto-learn timer |
| 0x1FE92 | `VTD_KE_VTD_TIME_TO_IGNITION_OFF` | 0xA0 (160 s) | Time before powerdown transition |
| 0x1FE94 | `VTD_KE_VTDC2_NOT_AN_EXPORT_VEHICLE` | 1 | Enable C2 auto-learn (non-export only) |

### 1.3 RAM Variables

| Address | Symbol | Description |
|---------|--------|-------------|
| `unk_FFFF8D17` | VTD State | State machine state number (0-F) |
| `unk_FFFF8D16` | VTD Flags | Bitfield: status/fault flags |
| `unk_FFFF8D18` | Auto-Learn Counter | Counts valid learned passwords |
| `unk_FFFF8D19` | Password Valid | 1 = password received and valid |
| `unk_FFFF8D1A` | Fuel Enabled | 1 = fuel enabled, 0 = fuel disabled |
| `unk_FFFF8D1B` | Init Done | 1 = BCM VTD message initialized |
| `unk_FFFF8D1C` | VTD Enabled | 1 = VTD is active (from ignition off timer) |
| `unk_FFFF8D1E` | Ignition Off Timer | Countdown before VTD activates |
| `unk_FFFF8D20` | Prev VTD State | Previous value of 0x8D1C |
| `unk_FFFF90F2` | BCM Password (word) | Password received from BCM |
| `unk_FFFF90E2` | BCM Password Valid | Flag: new password data available |
| `unk_FFFFB118` | Fuel Disable Timer | Fuel disable lockout timer |
| `unk_FFFFB11A` | C2 Init Timer | Class 2 initialization timer |
| `unk_FFFFB11C` | Password Timer | Password validation timeout |
| `unk_FFFFB11E` | Stored Password | Learned/valid password |
| `unk_FFFFB120` | C2 Init Status | Flag for Class 2 init complete |
| `unk_FFFFB121` | VTD Auth Flag | Used during authentication |
| `unk_FFFFB122` | Auto-Learn Active | Auto-learn in progress |
| `unk_FFFFB123` | Bad Password Counter | Counts bad password attempts |
| `unk_FFFFB124` | Identical Password Counter | Counts identical password matches |
| `unk_FFFFB10E` | Auto-Learn Timer | Auto-learn elapsed time tracking |
| `unk_FFFFB112` | C2 Auto-Learn Timer | C2 auto-learn elapsed time tracking |

### 1.4 State Machine (`sub_84AB0`, line 311625)

Called from `DoLoopE` (100 ms loop). The state machine has these states:

| State | Description | Behavior |
|-------|-------------|----------|
| **0** | Idle/Powerup | Initial state or no VTD activity |
| **1** | Valid Password | Current password matched; fuel enabled |
| **4** | Fuel Disable Lockout | Fuel disabled, timer running (640 s default) |
| **5** | Bad Password Lockout | Bad password counter exceeded; fuel disabled |
| **6** | Auto-Learn Pending | Waiting for password from BCM; auto-learn timer running |
| **7** | Auto-Learn Active | Received password; counting identical matches toward "learned enough" |
| **8** | Password Valid (2) | Secondary password validation |
| **9** | Transitional | Intermediate state during bad password handling |
| **$A** | Learn Password | Recording password for auto-learn |
| **$B** | Password Stored | Password learned and stored successfully |
| **$C** | Password Check | Receiving and validating BCM password |
| **$D** | Password Verify | Comparing received password against stored |
| **$E** | Bad Password | Bad password received; incrementing counter, may lead to lockout |
| **$F** | Force Lockout | Forced fuel disable |

### 1.5 Fuel Enable/Disable Mechanism

1. **`sub_8515E`** (line 312302): Sets/clears bits in the VTD flags byte (`unk_FFFF8D16`). Two key bits:
   - Bit 1 (`0x02`): Fuel disable command
   - Bit 4 (`0x10`): VTD lockout active
   - Bit 5 (`0x20`): Password learned/stored

2. **`sub_8522E`** (line 312392): Tests individual status bits in `unk_FFFF8D16`. Used throughout the state machine and by diagnostics.

3. **`sub_85316`** (line 312496): Called by fuel delivery code to check if fuel should be enabled. Returns 0 if VTD is active AND fuel is disabled (`VEH_SYS_KE_VTD_CONFIGURATION` != 0 AND `unk_FFFF8D1A` == 0).

4. **`sub_85326`** (line 312510): Called at ignition-on to initialize VTD. Sets bit 0x10 (lockout) in the flags.

5. **PID $1106 - VTD Fuel Disable** (`GetPid_1106_VTDFuelDisable`, line 193416): Reports VTD status via OBD-II. Returns bit-encoded status:
   - Bit 7: VTD fuel disabled (from `unk_FFFF93F3`)
   - Bit 6: VTD auto-learn active (from `unk_FFFF93EB`)
   - Bits 5-3: VTD state (0-3 from `unk_FFFF9FB9`)
   - Bit 1: Security wait time active

### 1.6 Password Exchange with BCM

1. BCM sends security password via Class 2 (J1850 VPW) serial data
2. Password arrives as a word at `unk_FFFF90F2` with a validity flag at `unk_FFFF90E2`
3. **`sub_274AE`**: Compares received password against stored/expected value
4. **`sub_274B4`**: Stores validated password
5. **`sub_274A0`**: Gets timestamp for password timing
6. **`sub_274C0`**: Initializes VTD message reception from BCM

### 1.7 VATS Relearn Procedure

The auto-learn process (state 6→7→A→B):

1. **Entry**: Ignition on, VTD configured (`VEH_SYS_KE_VTD_CONFIGURATION` != 0), auto-learn not disabled by export flag
2. **State 6 (Auto-Learn Pending)**: PCM waits for password from BCM. C2 auto-learn timer (`VTD_KE_VTD_C2_AUTO_LEARN` = ~26.7 hours) starts
3. **State 7 (Auto-Learn Active)**: Password received. Auto-learn counter (`unk_FFFF8D18`) increments each valid password match. Timer `VTD_KE_VTD_AUTO_LEARN` (~26.7 hours) runs
4. **State A (Learn Password)**: Counts identical passwords in `unk_FFFFB124`
5. **State B (Password Stored)**: When identical password count reaches `VTD_KE_VTD_LEARNED_PASSWORD` (3), the password is committed

**Bad Password Lockout**: If bad password counter exceeds `VTD_KE_VTD_BAD_PASSWORD` (3), enters state 4 (Fuel Disable) for `VTD_KE_VTD_DISABLE_TIME` (640 seconds)

### 1.8 Key Code Flow

```
DoLoopE (100 ms)
  → sub_84AB0 (VTD State Machine)
    ├─ Check ignition off timer → set VTD active flag (unk_FFFF8D1C)
    ├─ If VTD_CONFIGURATION == 0: skip VTD, init BCM message, fuel always enabled
    ├─ State dispatch based on unk_FFFF8D17
    │   ├─ State 0: Idle
    │   ├─ State 1: Valid password → fuel enabled
    │   ├─ State 4: Fuel disable lockout, timer-based
    │   ├─ State 5: Bad password lockout
    │   ├─ State 6: Auto-learn pending
    │   ├─ State 7: Auto-learn active
    │   ├─ State 8: Password validated
    │   ├─ State 9: Transitional
    │   ├─ State A: Learn password
    │   ├─ State B: Password stored
    │   ├─ State C: Password check (receive from BCM)
    │   ├─ State D: Password verify
    │   ├─ State E: Bad password
    │   └─ State F: Force lockout
    ├─ sub_8515E: Set/clear fuel enable bits
    ├─ sub_8522E: Read individual VTD status bits
    └─ sub_8523A: Powerdown transition handler

Fuel Delivery Path:
  sub_85316 → checks VTD_CONFIGURATION & unk_FFFF8D1A → returns 0 (disable) or 1 (enable)
```

---

## 2. Transmission Shift Scheduling

### 2.1 Overview

The P59 PCM contains a full automatic transmission shift scheduling subsystem, even on manual-transmission applications like this Corvette M6. Many automatic-specific calibrations are zeroed out, but the code structure and shift tables remain. The shift scheduling is primarily speed-based (MPH vs. throttle percentage), with separate tables for Normal, Cruise, Performance, and special modes.

### 2.2 Main Functions

| Function | Address | Called From | Description |
|----------|---------|-------------|-------------|
| `sub_4DD5C` | 0x4DD5C | DoLoopE | Main shift scheduling engine |
| `sub_4D97C` | 0x4D97C | sub_4DD5C | ETC shift stabilization |
| `sub_4DB06` | 0x4DB06 | sub_4DD5C | Upshift delay timing |
| `sub_4DB5C` | 0x4DB5C | sub_4DD5C | Shift execution validation |
| `sub_4A71A` | 0x4A71A | DoLoopF | Upshift indicator light algorithm |

### 2.3 Shift Tables

All shift tables are throttle vs. speed (MPH) lookup tables. Each row is a (throttle%, MPH) pair defining a shift boundary.

#### 2.3.1 Upshift Tables (Normal Mode)

| Table | Symbol | Entries | Description |
|-------|--------|---------|-------------|
| 1→2 | `T_SHIFT_TABLES_KV_1_2_NORMAL_LINE` | 17 | 0-43 MPH range |
| 2→3 | `T_SHIFT_TABLES_KV_2_3_NORMAL_LINE` | 20 | 0-44+ MPH range |
| 3→4 | `T_SHIFT_TABLES_KV_3_4_NORMAL_LINE` | 28 | Widest range |

#### 2.3.2 Downshift Tables (Normal Mode)

| Table | Symbol | Entries |
|-------|--------|---------|
| 2→1 | `T_SHIFT_TABLES_KV_2_1_NORMAL_LINE` | 10 |
| 3→2 | `T_SHIFT_TABLES_KV_3_2_NORMAL_LINE` | 18 |
| 4→3 | `T_SHIFT_TABLES_KV_4_3_NORMAL_LINE` | 25 |

#### 2.3.3 Cruise Mode Tables

| Table | Symbol | Entries |
|-------|--------|---------|
| 1→2 up | `T_SHIFT_TABLES_KV_1_2_CRUISE_LINE` | 17 |
| 2→3 up | `T_SHIFT_TABLES_KV_2_3_CRUISE_LINE` | 20 |
| 3→4 up | `T_SHIFT_TABLES_KV_3_4_CRUISE_LINE` | 28 |
| 2→1 dn | `T_SHIFT_TABLES_KV_2_1_CRUISE_LINE` | 10 |
| 3→2 dn | `T_SHIFT_TABLES_KV_3_2_CRUISE_LINE` | 18 |
| 4→3 dn | `T_SHIFT_TABLES_KV_4_3_CRUISE_LINE` | 25 |

#### 2.3.4 Special Mode Tables

| Table | Symbol | Description |
|-------|--------|-------------|
| 1→2 | `T_SHIFT_TABLES_KV_1_2_DRIVE_2_LINE` | Drive-2 (manual gear hold) |
| 2→1 | `T_SHIFT_TABLES_KV_2_1_DRIVE_2_LINE` | Drive-2 downshift |
| 1→2 | `T_SHIFT_TABLES_KV_1_2_HP_EP_DELTA_LINE` | High Perf / Engine Protection modifier |

#### 2.3.5 Shift Pattern Selection

`T_SHIFT_TABLES_KV_SHIFT_STAB_SHIFT_PATTRN_ENBLE` — 12-entry array of boolean flags enabling shift stabilization per pattern index. Pattern index comes from `unk_FFFF95F1` (shift pattern selector).

### 2.4 WOT (Wide Open Throttle) Shift Parameters

#### WOT Upshift RPM

| Address | Symbol | Description |
|---------|--------|-------------|
| 0x1A634 | `WOT Upshift RPM - Normal` | 3 rows: 1-2, 2-3, 3-4 RPM |
| 0x1A63A | `WOT Upshift RPM - Hot` | Hot temperature modifier |
| 0x1A646 | `WOT Upshift RPM - Performance` | Performance mode |
| 0x1A93E | `WOT Upshift RPM - 4WD Lo` | 4WD low range |

Cold temperature modifiers for each shift are separate offsets added to the base RPM thresholds.

#### WOT Upshift/Downshift Speed (MPH/KPH)

| Address | Description |
|---------|-------------|
| 0x1A5AA | WOT Upshift Speed MPH - Normal |
| 0x1A5B0 | WOT Downshift Speed MPH - Normal |
| 0x1A5B6 | WOT Upshift Speed MPH - Hot |
| 0x1A5BC | WOT Downshift Speed MPH - Hot |
| 0x1A5C2 | WOT Upshift Speed MPH - Performance |
| 0x1A5C8 | WOT Downshift Speed MPH - Performance |
| 0x1A932 | WOT Downshift Speed MPH - 4WD Lo |
| 0x1A938 | WOT Upshift Speed MPH - 4WD Lo |

#### Altitude Compensation

| Address | Description |
|---------|-------------|
| 0x1A64C | Barometric Pressure Upshift Correction - Max Allowed RPM Bias (3 rows) |

### 2.5 Shift Pressure Control

| Parameter | Address | Value | Description |
|-----------|---------|-------|-------------|
| `XMSN_IO_KE_MAX_PRESSURE` | 0x1C??? | 0x1680 (5760 PSI scaled) | Max force motor pressure |
| `T_FM_CONTROL_KE_FM_MIN_DUTY_CYCLE_MFD` | 0x1A??? | 0x666 (16.4% scaled) | Min FM duty cycle for current measurement |

Pressure control tables include:
- Desired Shift Time tables (normal/cruise modes with altitude compensation)
- Downshift pressure temperature compensation (3D tables)
- Torque reduction during shift (percentage tables for each upshift, normal and performance patterns)

### 2.6 Shift Stabilization (ETC-based)

The PCM can use electronic throttle control to smooth shifts (reduce torque during shift, match engine speed to next gear).

| Parameter | Value | Description |
|-----------|-------|-------------|
| `X_SHIFT_KE_ETC_STAB_ENABLE` | 0 | ETC shift stab enable (disabled on M6) |
| `XTCC_CONTROL_KE_SHIFT_STABILIZATION_ENABLE` | varied | Global stabilization enable |
| `X_SHIFT_KV_SHIFT_STABLE_OVERALL_RATIO` | 0x45CE | Overall gear ratio for torque calc |
| `X_SHIFT_KV_TRQ_CONV_K_FACTOR` | 0x30 | Torque converter K-factor |
| `X_TCM_EXECUTION_KE_USE_SHIFT_STABILIZATION_ACCEL` | 0 | Accel-based stab bypass |

Shift stabilization algorithm flow:
1. `sub_4DD5C` calculates normalized engine torque from airmass and RPM
2. Computes gearbox torque using converter torque ratio and gear ratio
3. `sub_4D97C` manages shift timing and delays
4. `sub_4DB06` handles upshift delay timing (prevents rapid re-shifts)

### 2.7 Manual Transmission Notes

Since this is a Corvette M6 (manual), many automatic-specific calibrations are zero:
- `X_SHIFT_KE_POWER_ON_THROTTLE` = 0 (no power-on upshift)
- `X_SHIFT_KE_VEHICLE_ACCELERATING_MAX` = 0
- `X_SHIFT_KV_PRED_TRQ_CONV_SPD_RATIO` = 0 (no torque converter)
- `X_SHIFT_KV_PRED_BASE_NORM_VEH_TORQUE` = 0
- `TCM_OPTIONS_K_TCC_ENABLE_SOLENOID_PRESENT` = 0
- `X_SHIFT_KE_32_23_SOLENOID_DELAY_ENABLE` = 0

---

## 3. CCP (CAN Calibration Protocol)

### 3.1 Overview

The P59 PCM supports CCP (CAN Calibration Protocol) via the ETAS interface. When an ETAS calibration tool (like INCA) connects, it writes a magic presence pattern (0xB99C) to a dedicated calibration location. The PCM then configures the TouCAN module for CCP communication on the CAN bus, enabling real-time calibration read/write (slewing) and data acquisition (DAQ).

### 3.2 ETAS Presence Detection

| Address | Symbol | Description |
|---------|--------|-------------|
| 0x8024 | `ETAS_KE_ETAS_PRESENCE_PATTERN` | Magic value 0xB99C written by ETAS tool |
| 0x8025 | `ETAS_KE_ETAS_DATA_ACQUIRE_RATE_GROUP` | DAQ rate group selector (0-3) |
| 0x8026 | `ETAS_KE_ETAS_PAD_BYTE_1` | Alignment padding |
| 0x8027 | `ETAS_KE_ETAS_PAD_BYTE_2` | Alignment padding |
| 0x8028 | `ETAS_KE_ETAS_PAD_BYTE_3` | Alignment padding |

**Detection Flow** (`sub_78BBE`, line 289551, called from DoLoopF 25ms loop):
```
sub_78BBE:
  check ETAS_KE_ETAS_PRESENCE_PATTERN == 0xB99C
  if match:
    set unk_FFFF819D = 1 (ETAS present flag)
    re-configure TouCAN registers (0xFFFFFA00-FFFFFAFF)
    configure CAN bit timing
    configure acceptance filters for CCP CRO/DTO
  else:
    set unk_FFFF819D = 0
```

### 3.3 CCP Slew (Real-Time Calibration Modification)

**Function**: `sub_27C78` (line 142987), called from DoLoopF (25ms loop)

Each slewable parameter has three calibration values:
- **`_MODE`**: Operation mode (0=disabled, 1=absolute, 2=modify)
- **`_ABS`**: Absolute value (replaces the runtime value when mode=1)
- **`_MOD`**: Modifier value (signed offset added to runtime value when mode=2)

**Slewable Parameters** (all at addresses ~0x8028-0x80EF):

| Parameter | Mode Cal | Abs Cal | Mod Cal | Units |
|-----------|----------|---------|---------|-------|
| CCP (Canister Purge)* | 0x8028 | 0x802A | 0x802C | Percent |
| EQVR (Equiv Ratio) | 0x8030 | (included) | 0x8034 | Ratio |
| EGR | 0x8038 | 0x803A | 0x803C | Percent |
| Fan Hz | 0x8040 | 0x8042 | 0x8044 | Hertz |
| FFS Hz | 0x8048 | 0x804A | 0x804C | Hertz |
| FFS Low Time | 0x8050 | 0x8052 | 0x8054 | ms |
| Fuel Econ | 0x8058 | (sign cal) | — | — |
| NVMEM | 0x8060 | 0x8062 | 0x8064 | — |
| TCS Discrete | 0x8068 | 0x806A | 0x806C | — |
| TCS DC | 0x8070 | 0x8072 | 0x8074 | — |
| Spark Crank | 0x8078 | 0x807A | 0x807C | Degrees |
| Spark Run | 0x8080 | 0x8082 | 0x8084 | Degrees |
| IAC Airflow | 0x8088 | 0x808A | 0x808C | g/s |
| IAC RPM | 0x8090 | 0x8092 | 0x8094 | RPM |
| IAC Position | 0x8098 | 0x809A | 0x809C | Steps |
| Oil Level | 0x80A0 | 0x80A2 | 0x80A4 | — |
| TCC Control | 0x80A8 | 0x80AA | 0x80AC | — |

> *Note: The CCP acronym is overloaded. In the ETAS slew context, "CCP" refers to Canister Purge (evaporative emissions). This is separate from the CAN Calibration Protocol (also abbreviated CCP). The ETAS slew framework handles both — the CAN Calibration Protocol is the transport, while individual slew parameters control specific engine functions.

### 3.4 DAQ (Data Acquisition)

**Function**: `sub_27AD2` (line 142769), called from DoManyThings1

**DAQ Rate Groups**: Controlled by `ETAS_KE_ETAS_DATA_ACQUIRE_RATE_GROUP`:
- Value 0-2: Select specific DAQ rate groups
- Value 3: High-speed DAQ mode

**DAQ List Upload** (`sub_27B26`, line 142832):
The DAQ mechanism copies calibration/RAM data into output buffers (DTOs) for transmission over CAN. Each DAQ list is structured as:

```
DAQ List Header:
  byte 0:     Status flag (1 = active)
  byte 1-3:   (padding)
  bytes 4-5:  Address of first ODT (Object Descriptor Table)
  bytes 6-7:  Reserved
  bytes 8+:   ODT pointers

ODT Entry:
  4 bytes: pointer to data element (RAM address)
```

Data types supported per ODT:
- **ODT type 0**: Longwords (4 bytes) — pointer array
- **ODT type 1**: Words (2 bytes) — pointer array  
- **ODT type 2**: Bytes (1 byte) — pointer array
- **ODT type 3**: Mixed — variable sizes based on header

Each DAQ list has a maximum size (word at offset 0x12 from list base) that limits how many ODT entries can be uploaded.

### 3.5 CCP on CAN Transport

The P59 PCM uses the **Motorola 68332 TouCAN module** for CAN communication.

**CAN Register Map** (0xFFFFFA00 base):
```
0xFFFFFA00: CAN Module Control Register
0xFFFFFA04: CAN Bit Timing Register
0xFFFFFA15: CAN Acceptance Register
0xFFFFFA1D: CAN Acceptance Register
0xFFFFFA44-FFFFFA6E: CAN Message Buffer configuration
0xFFFFFA74-FFFFFA76: CAN Message Buffer data
0xFFFFFB00: TouCAN Prescaler
0xFFFFFB40/80/A0/C0: TouCAN bit timing
0xFFFFFC00-FFFFFC0A: TouCAN error/interrupt registers
0xFFFFD001/D003/D005: CAN output control
```

**CCP Standard Message IDs** (configured by `sub_78BBE`):
- **CRO** (Command Receive Object): Master→Slave command messages
- **DTO** (Data Transmission Object): Slave→Master response/data messages

The actual CAN IDs used for CCP are configured dynamically when ETAS is detected, via the calibration data at addresses 0x1642-0x16BA (CAN configuration tables).

### 3.6 CCP Command Support

While the disassembly shows the transport and slew infrastructure, the CCP command handler itself is integrated into the CAN receive processing. Based on the ETAS instrumentation framework visible in the code, the P59 supports:

- **CONNECT** (0x01): Establish CCP session
- **SET_MTA** (0x02): Set Memory Transfer Address
- **DNLOAD** (0x03): Download (write) data to PCM RAM
- **UPLOAD** (0x04): Upload (read) data from PCM RAM
- **GET_CCP_VERSION** (0x1B): Return CCP implementation version
- **EXCHANGE_ID** (0x17): Return PCM identification
- **SET_S_STATUS** (0x0C): Set session status
- **GET_S_STATUS** (0x0D): Get session status
- **START_STOP** (0x06): Start/stop DAQ
- **START_STOP_ALL** (0x08): Start/stop all DAQ lists
- **SET_DAQ_PTR** (0x14): Set DAQ list pointer
- **WRITE_DAQ** (0x15): Write DAQ list entries

### 3.7 Key Code Flow

```
Boot / Init:
  sub_138E → checks ETAS_KE_ETAS_PRESENCE_PATTERN for 0xB99C

DoLoopF (25 ms):
  → sub_78BBE        # ETAS detection + CAN configuration
  → sub_27C78        # CCP slew (update runtime cal values)
  → sub_266D2        # Apply slew values to engine control

DoManyThings1 (background):
  → sub_27AD2        # DAQ rate group management
    → sub_27B26      # DAQ list data upload (pack DTO data)
```

---

## Appendix: Key Address Reference

### VTD/VATS
| Address | Name | Type |
|---------|------|------|
| 0x84AB0 | VTD State Machine | Code |
| 0x8515E | VTD Flag Set/Clear | Code |
| 0x8522E | VTD Flag Test | Code |
| 0x85316 | VTD Fuel Enable Check | Code |
| 0x85326 | VTD Init | Code |
| 0x1F784 | VTD Configuration | Cal |
| 0x1FE80-0x1FE94 | VTD Calibrations | Cal |
| 0x43394 | PID $1106 VTD Fuel Disable | Code |

### Transmission
| Address | Name | Type |
|---------|------|------|
| 0x4DD5C | Main Shift Scheduler | Code |
| 0x4D97C | Shift Stabilization | Code |
| 0x4A71A | Upshift Light Logic | Code |
| 0x1A5AA-0x1A5C8 | WOT Shift Speed Tables | Cal |
| 0x1A634-0x1A64C | WOT Shift RPM Tables | Cal |
| 0x1A??? | Shift Line Tables (Normal/Cruise) | Cal |
| 0x1A93E | WOT Upshift RPM 4WD | Cal |

### CCP/ETAS
| Address | Name | Type |
|---------|------|------|
| 0x78BBE | ETAS Detection + CAN Config | Code |
| 0x27C78 | CCP Slew Handler | Code |
| 0x27AD2 | CCP DAQ Handler | Code |
| 0x8024 | ETAS Presence Pattern | Cal |
| 0x8028-0x80EF | ETAS Slew Calibrations | Cal |
| 0x1642-0x16BA | CAN Configuration Tables | Cal |
