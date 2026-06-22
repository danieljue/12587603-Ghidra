# P59 OS 12587603 — Engine Protection Modes

> Traced from 68k disassembly — 2026-06-22
> Engine protection prevents catastrophic engine damage from overheat, low
> coolant, and other critical conditions. Uses progressive cylinder deactivation,
> audible alarms, and engine shutdown as last resort.

---

## 1. Overview

The P59 engine protection system has three escalation levels:
1. **Warning**: 120 beeps/min alarm + "Check Gauges" lamp when coolant exceeds
   KE_ENGINE_ALARM_COOLANT_TEMP
2. **Overheat Protection**: Progressive cylinder deactivation to reduce heat
   generation when coolant exceeds KE_ENGINE_PROTECTION_COOLANT_HIGH
3. **Engine Shutdown**: 300 beeps/min alarm followed by forced engine stop
   when low coolant or extreme overtemperature is detected

Cylinder deactivation alternates between two cylinder groups (KV_CYLINDER_GROUP_ONE
and TWO) every KE_CYCLES_BETWEEN_SWITCHING cycles to distribute thermal load
evenly. Cylinders are ramped in/out one at a time every
KE_CYCLES_BETWEEN_RAMP_STEPS cycles.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_7D7AA | 0x07D7AA | — | Overheat cylinder deactivation ramp control |
| sub_7DCB4 | 0x07DCB4 | — | Coolant temperature alarm (120 beeps/min) |
| sub_7DCEE | 0x07DCEE | — | Engine shutdown logic (low coolant / extreme overheat) |
| sub_7DB64 | 0x07DB64 | — | Engine shutdown timer |
| sub_7D8E0 | 0x07D8E0 | — | Cylinder cutout control with torque percentage hysteresis |

---

## 3. Calibration Parameters (ENG_PROTECTION module, 0x9A50-0x9A7A)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x09A50 | KE_ENGINE_PROTECTION_COOLANT_HIG | word | — | °C | ECT above which overheat protection enabled |
| 0x09A52 | KE_ENGINE_PROTECTION_COOLANT_LOW | word | — | °C | ECT below which overheat protection disabled |
| 0x09A54 | KE_ENGINE_PROTECTION_DELAY_TIME | word | — | Seconds | Delay before activation |
| 0x09A56 | KE_CYCLES_BETWEEN_RAMP_STEPS | word | 0x14 | Engine cycles | Cycles between cylinder ramp steps |
| 0x09A58 | KE_CYCLES_BETWEEN_SWITCHING | word | 0xB4 | Engine cycles | Cycles between cylinder group switching |
| 0x09A5A | KE_ENGINE_ALARM_COOLANT_TEMP | word | 0xDFF | °C | 120 beeps/min alarm threshold |
| 0x09A5C | KE_ENGINE_PROTECTION_STARTUP_DEL | word | 0x640 | Seconds | Delay after engine start before protection |
| 0x09A5E | KE_ENG_SHUTDOWN_CLT_TEMP_OFFSET | word | 0xFFFF | °C | Temp offset for shutdown decision |
| 0x09A60 | KE_ENGINE_SHUTDOWN_COOLANT_TIME | word | 0xFFFF | Seconds | Time with low coolant before shutdown |
| 0x09A62 | KE_ENG_SHUTDOWN_LOW_CLT_ENABLE | byte | 0 | BOOLEAN | Enable shutdown on low coolant |
| 0x09A64 | KE_ENGINE_SHUTDOWN_TIME | word | 0xFFFF | Seconds | 300 beeps/min alarm before shutdown |
| 0x09A66 | KE_CYLINDER_CUTOUT_HYSTERESIS | word | 0x133 | Percent | Hysteresis to prevent cycling |
| 0x09A68 | KV_CYLINDER_GROUP_ONE | byte | 0x55 | BOOLEAN vector | Cylinder group 1 disable vector |
| 0x09A69 | KV_CYLINDER_GROUP_TWO | byte | — | BOOLEAN vector | Cylinder group 2 disable vector |
| 0x09A6A | KV_ENG_PROT_CYLINDERS_TO_DISABLE | byte | — | BOOLEAN vector | Cylinders to disable for protection |
| 0x09A72 | KV_BTM_PM_CYLINDERS_TO_DISABLE | byte | — | BOOLEAN vector | Cylinders for BTM/power management |
| 0x09A7A | KV_POWER_HOP_PM_CYL_TO_DISABLE | byte | — | BOOLEAN vector | Cylinders for power hop protection |

---

## 4. Algorithm Detail

### 4.1 Escalation Levels

```
LEVEL 1 — Warning (120 beeps/min alarm):
  ECT > KE_ENGINE_ALARM_COOLANT_TEMP
  → 120 beeps per minute audible alarm
  → "Check Gauges" lamp illuminated
  → No power reduction

LEVEL 2 — Overheat Protection (cylinder deactivation):
  ECT > KE_ENGINE_PROTECTION_COOLANT_HIGH
  AND engine run time > KE_ENGINE_PROTECTION_STARTUP_DEL
  → Begin cylinder deactivation:
    1. Disable cylinders per KV_ENG_PROT_CYLINDERS_TO_DISABLE
    2. Ramp in/out one cylinder at a time every
       KE_CYCLES_BETWEEN_RAMP_STEPS cycles
    3. Alternate between KV_CYLINDER_GROUP_ONE and TWO every
       KE_CYCLES_BETWEEN_SWITCHING cycles
    4. This distributes thermal load evenly across cylinders
    5. Torque percentage hysteresis: KE_CYLINDER_CUTOUT_HYSTERESIS
       prevents oscillation between cylinder counts
  → Exit when ECT < KE_ENGINE_PROTECTION_COOLANT_LOW

LEVEL 3 — Engine Shutdown (300 beeps/min alarm):
  Low coolant switch active (if KE_ENG_SHUTDOWN_LOW_CLT_ENABLE)
  OR extreme ECT condition
  → 300 beeps per minute alarm
  → After KE_ENGINE_SHUTDOWN_TIME seconds of alarm:
    Force engine stop (fuel cut + disable ignition)
```

### 4.2 Cylinder Group Switching

```
Cylinder group vectors are bitfields (1 bit per cylinder, bits 0-7 = cyl 1-8):

KV_CYLINDER_GROUP_ONE = 0x55 = 0b01010101 = cylinders 1,3,5,7
KV_CYLINDER_GROUP_TWO                      = cylinders 2,4,6,8

Every KE_CYCLES_BETWEEN_SWITCHING cycles:
  Active group alternates
  → Cylinders from the other group are re-enabled
  → Cylinders from the new active group are disabled
  → Even heat distribution across all cylinders
```

---

## 5. Integration Points

| Connected To | How |
|-------------|-----|
| Fuel System (doc 07) | Cylinder deactivation via injector disable |
| Ignition Control | Cylinder deactivation via spark disable |
| Coolant Temperature | Primary trigger for all protection levels |
| IPC / Instrument Cluster | "Check Gauges" lamp + audible alarm |
| Low Coolant Switch | Hardware input for shutdown decision |
| Torque Management (doc 32) | Shares cylinder disable mechanism |

---

## 6. Gaps & Unresolved

1. **Low coolant switch input**: The hardware pin for the low coolant level
   sensor has not been identified.

2. **Audible alarm output**: The specific Class 2 message or discrete output
   for the 120/300 beeps-per-minute alarm has not been traced.

3. **Power hop protection**: KV_POWER_HOP_PM_CYL_TO_DISABLE references "power
   hop torque management" — this is likely a Corvette-specific wheel hop
   protection that deactivates cylinders to reduce drivetrain oscillation.
   Not traced.

---

## 7. Community Knowledge

- **Overheat protection delete**: Some tuners disable overheat protection
  (max out thresholds) on race cars. This is risky — the protection exists
  because the PCM cannot otherwise prevent engine damage from coolant loss.

- **Low coolant switch**: The C5 Corvette has a low coolant sensor in the
  surge tank. KE_ENG_SHUTDOWN_LOW_CLT_ENABLE = 0 on stock tune means the
  PCM does not shut down the engine on low coolant (only warns).

- **Cylinder deactivation feel**: When overheat protection activates, the
  engine runs rough due to missing cylinders. This is intentional — it forces
  the driver to notice and pull over before engine damage occurs.
