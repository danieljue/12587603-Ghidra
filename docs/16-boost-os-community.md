# Boost OS — Community Knowledge & Research

> **Research compiled:** June 2026  
> **Sources:** pcmhacking.net forum posts, Patreon (Turbo V6 / Branden / bubba2533), Kemono mirrors, YouTube overviews, and cross-referenced LS tuning community discussions.  
> **Creator:** turbo_v6 (aka bubba2533, Branden) — active on pcmhacking.net and Patreon.  
> **Base OS:** 12587603 (P59 1MB blue/green connector PCM)

---

## 1. What is Boost OS?

Boost OS is a **patched custom operating system** for the GM P59 PCM (and earlier P01 on V1–V2) that adds forced-induction tuning features not present in the factory OS. It is distributed as a **bin patch** applied via a dedicated "Boost OS Patcher" tool, with an **XDF definition file** for TunerPro. The patch modifies the stock 12587603 OS binary by:

1. **Re-purposing unused factory code** — especially the EGR subsystem (EGR solenoid output becomes boost control output; EGR RAM/ROM space is reclaimed).
2. **Adding new code and tables** in free space at the end of the calibration section.
3. **Introducing a new custom OSID** — which is why only PCM Hammer V20 can flash it (V21 doesn't recognize the new OSID or parameter section).

Because new parameters live **outside the standard calibration address range**, all parameter changes require a **full "Write OS, Calibration, and Boot"** — you cannot do a calibration-only write with standard tools.

---

## 2. Version History & Feature Matrix

### V1.0 — Initial Release (July 2021)
- **Supported PCMs:** P01 (12212156, 12216125) and P59 (12587603)
- **Features:**
  - Selectable N/A, 2 bar, or 3 bar VE Table (expanded to positive manifold pressure)
  - Boost Spark Adder (timing adjustment vs MAP above 100 kPa)
  - Expanded Desired Open Loop EQ Ratio Table
  - Spark Cut Engine Speed Limiter
  - Launch Control (spark cut limiter + spark adder + timed launch spark adder)
  - Flat Foot Shift (spark cut)
- **Tools:** TunerPro XDF, manual patching process
- **Notes:** Initial proof-of-concept. MVP feature set.

### V2.1 — Expanded Features (July 2021 – 2022)
- **Supported PCMs:** P01 (12212156, 12216125) + P59 (12587603)
- **Changes from V1:**
  - VE Table expanded to 15–375 kPa
  - Desired Open Loop EQ Ratio table expanded to 20–340 kPa
- **New Features:**
  - **Open Loop Boost Control** (via secondary fuel pump output — re-purposed EGR solenoid driver)
  - **Wideband Closed Loop Fueling** (0–5V wideband input)
  - **Lean Boost Cut Safety** (fuel/spark cut on lean condition under boost)
  - **Desired Air/Fuel Ratio Table** (RPM vs MAP — replaces Power Enrichment)
  - Disable Running Baro Update
- **Bug Fixes:** XDF mistakes corrected, patch separated from base tune
- **Important:** Last version supporting P01 PCMs.

### V3.0 — Major Rewrite (Patreon: Sept 2022, Public: April 2023)
- **Supported PCMs:** P59 ONLY (12587603)
  - P01 support dropped due to memory constraints on 512KB PCMs
  - V3 uses new features requiring the 1MB P59 flash space
- **New Features (relative to V2.1):**
  - **Boost OS Patcher** — dedicated tool for applying, upgrading, and reverting patches
  - VE Table expanded to **425 kPa** (N/A, 2 bar, or 4 bar selectable)
  - **Launch Control — Soft & Hard Limit** (spark cut + fuel cut)
  - **Timed Launch Spark Adder**
  - **Wideband Scaling** (configurable voltage-to-AFR mapping)
  - **Wideband Fault Delay Time** (debounce before fault trigger)
  - **Gen 4 MAF Calibration Table** (LS2/LS3/LS7 MAF sensor support)
  - **Disable MAF Fueling** (pure Speed Density mode)
  - **Over-Boost Spark Cut** (safety cut above configurable MAP threshold)
  - **Desired Air/Fuel Ratio** table (RPM vs MAP — replaces PE enrichment)
  - **Spark Cut Engine Speed Limiter — Soft & Hard Limit**
- **Flash Requirements:**
  - MUST use **PCM Hammer V20** only (V21 incompatible)
  - MUST flash via **Write OS, Calibration, and Boot** (parameter-only writes don't work due to custom OSID)
- **Tools included in zip:** TunerPro DLL, Boost OS V3 XDF, Boost OS Patcher

### V3.2 — Bug Fix (Patreon)
- **Fix:** Bug in 2 Bar VE Table selection

### V3.3 — Bug Fix (Patreon)
- **Fix:** Rich condition bug for 1 bar and 2 bar operating modes

### V3.4 — Latest Free V3 (on pcmhacking.net)
- Cumulative V3 with all fixes
- This is the **final freely available version** on pcmhacking.net
- Patreon versions (V4, V5) are paid/early-access

### V4.0 — Patreon Release (April 2023)
- **Full Feature Set:**
  - Selectable N/A, 2 bar, or 4 bar VE Table
  - Boost Spark Adder
  - Open Loop Boost Control
  - Wideband Closed Loop Fueling
  - Wideband Scaling
  - Wideband Fault Delay Time
  - Launch Control (Soft & Hard Limit)
  - Timed Launch Spark Adder
  - Flat Foot Shift (Spark Cut)
  - Engine Speed Limiter (Soft & Hard Limit)
  - Desired Air/Fuel Ratio (RPM vs MAP) — replaces PE
  - Gen 4 MAF Calibration Table
  - Disable MAF Fueling (Speed Density mode)
  - Over-Boost Spark Cut
  - **Flex Fuel sensor support** (ethanol content-based table blending)
  - **Dual Wideband Input** (Bank 1 and Bank 2)
  - **Coil-Near-Plug support** for V6 applications (e.g., 4.3L)
  - **MAF + Closed Loop Wideband** compatible

### V4.5 — Bug Fix (Patreon, August 2023)
- Bug fixes for V4 features
- Discord server created for community discussions

### V5.0 — Current Patreon Version (June 2024)
- **New in V5:**
  - 2 Bar Desired Air/Fuel Table (higher resolution for boosted regions)
  - Dual Wideband Input
  - 4 Input Pins for Wideband O2 (configurable ADC inputs)
  - Updated Patch Tool with improvements
- **Feature Requests solicited** via Patreon/Discord

---

## 3. How It Works — Technical Details

### Patching Architecture

1. **Base OS:** 12587603 (P59 1MB flash). This OS was chosen because:
   - It's the most feature-complete P59 OS
   - Has unused EGR code/subroutines that can be re-purposed
   - Has free space at end of calibration section (0x1FEF2 to 0x1FFDF — ~237 bytes in Speed Cal)
   - 1MB flash provides room for expanded tables beyond stock limits

2. **EGR Re-purposing:**
   - EGR solenoid driver pin re-wired to control a boost control solenoid (MAC valve)
   - EGR duty-cycle code re-purposed for PWM boost control
   - EGR RAM variables reclaimed for new features
   - The S10 EGR solenoid measures 8–9Ω at 12V — sufficient to drive a MAC boost control valve

3. **Custom OSID:**
   - Modified OS uses a new OSID not in PCM Hammer V21's database
   - V20 works because it doesn't validate the OSID
   - This is why "Write OS, Calibration, and Boot" is required

4. **Parameter Section:**
   - New parameters stored outside the standard 0x8000–0x1FFFF calibration range
   - Standard calibration-only write tools (HP Tuners, EFILive, PCM Hammer cal write) don't touch this area
   - **Consequence:** Every parameter change requires a full OS+Boot+Cal flash (~2–4 minutes per change)

5. **Boost OS Patcher:**
   - Standalone tool (likely .NET/WinForms application)
   - Applies binary patch to stock 12587603 bin
   - Handles version upgrades (e.g., V3.0 → V3.4)
   - Can revert to factory OS
   - Patches are applied to a bin file, not directly to the PCM

### Tuning Workflow

1. Read stock bin via PCM Hammer V20
2. Open bin in TunerPro with Boost OS XDF
3. Run Boost OS Patcher to apply patch to the bin
4. Configure all Boost OS parameters in TunerPro
5. Flash patched bin via PCM Hammer V20 — **Write OS, Calibration, and Boot**
6. Use PCM Logger for live data logging (~150 fps achieved on P59)

### Incompatibilities
- **HP Tuners / EFILive** cannot read or flash the patched OS (custom OSID not recognized)
- **PCM Hammer V21** incompatible (validates OSID and rejects unknown IDs)
- **P01 PCMs** not supported from V3 onward (512KB flash insufficient)
- **Calibration-only writes** won't update Boost OS parameters (they're outside the cal section)

---

## 4. Community Feedback & User Experiences

### Success Stories

- **RTLS1 Project:** User successfully runs Boost OS on a P59 with "15-375 kPa VE Table" and reports it works "perfectly." Achieved 150 fps logging rate with P59 PCM + PCM Logger. (pcmhacking.net forum)
- **Multiple testers:** turbo_v6 states V3 "has been tested by a number of people including myself"
- **4.3L V6 with Coil-Near-Plug:** Users discussing using Boost OS V3 for V6 applications

### Common Questions from Community

| Question | Answer |
|---|---|
| Does V3/V4 support MAF + closed loop wideband? | Yes, both can (turbo_v6 confirmed) |
| Can V3 be used on P01? | No, V3+ is P59 only. Use V2.1 for P01 |
| Can HP Tuners read/flash Boost OS? | No. Must use PCM Hammer V20 + TunerPro |
| Will flex fuel tables have higher resolution? | Question asked but not confirmed for free versions (possibly V4/V5 Patreon) |
| Can it monitor wideband on both banks? | Yes (dual wideband in V4/V5) |
| Is there live tuning support? | No, but PCM Logger can stream data at high rates |
| Does it work with DBW (ETC)? | Yes, if the base 12587603 OS supports DBW |
| Can I use the patch on a different OS (e.g., 12592433)? | Must convert/flash 12587603 first |

### Technical Critiques (from forum)

**vwnut8392** (after disassembling V3.4):
> "Why are the constants/tables after your code? This would make the user have to do a full write of the ECU every time with PCM Hammer. Why not move [tables before code]?"

This is a known architectural limitation — by placing parameters after the patched code in the custom section, every tuning change requires a full flash rather than a calibration-only write. This was a deliberate trade-off in V3's design, likely to simplify the patch structure.

**160plus** (V1 era):
> "After doing the initial OS flash, are all the tables/scalers changes done within the calibration section or is there data altered outside of the 0x8000–0x1FFFF range?"

This was the first community question identifying the calibration-section issue that persists through all versions.

### Feature Requests from Community

- **Anti-lag / Rolling anti-lag** — discussed but not implemented
- **Higher flex fuel table resolution** — requested by gilius
- **Closed loop wideband on both banks** — added in V4
- **Porting to Universal Patcher** — discussed but not completed
- **Live tuning capability** — multiple users interested
- **Better documentation on feature usage** — prompted the YouTube overview video

---

## 5. Known Issues & Limitations

### Flash/Memory Architecture
| Issue | Details |
|---|---|
| Full flash required for every change | Any Boost OS parameter change requires "Write OS, Calibration, and Boot" — takes 2–4 minutes per tune iteration |
| PCM Hammer V20 only | V21 incompatible; V20 must be sourced separately |
| No calibration-only updates | Parameters stored outside standard calibration range |

### Platform Limitations
| Issue | Details |
|---|---|
| P59 only (V3+) | P01/P04 users stuck on V2.1; 512KB flash too small for V3 features |
| Windows-only toolchain | TunerPro, PCM Hammer, Boost OS Patcher are Windows applications |
| No HP Tuners/EFILive compatibility | Locked into the open-source PCM Hammer + TunerPro ecosystem |

### Bugs Discovered & Fixed
| Version | Bug |
|---|---|
| V3.2 | 2-bar VE table selection broken |
| V3.3 | Rich condition at 1-bar and 2-bar modes |
| V4.5 | Undisclosed bug fixes for V4 |

### Functional Limitations
| Limitation | Details |
|---|---|
| No anti-lag | Frequently requested, not implemented |
| Open-loop boost control only | No closed-loop PID boost control (uses duty-cycle table) |
| Spark-cut only (no fuel cut for LC/FFS) | No combined fuel+spark cut strategies |
| No traction control | Not on feature list |
| No nitrous control | Not on feature list |
| No transmission control integration | P59 TCM control remains stock |
| PCM Logger dependent | No on-board datalogging; need laptop connected |

### Potential Bricking Risk
- Interrupting a full OS+Boot+Cal flash could brick the PCM
- Must have a stable power supply and reliable OBDII interface
- Recovery requires BDM or boot-mode programming if flash is interrupted

---

## 6. Distribution & Licensing

- **V1.0 through V3.4:** Free on pcmhacking.net forums
- **V4.0 through V5.0+:** Patreon (paid) — early access / exclusive features
- **Patreon tiers:** Various levels; V4/V5 access requires subscription
- **License model:** Free for personal use on free versions; Patreon terms for paid versions
- **XDF definitions:** Included with each release
- **Source code:** Not open source — binary patches only (distributed as bin patches via patcher tool)
- **Community contributions:** Feature suggestions via Patreon/Discord and development thread

---

## 7. Key Resources

| Resource | URL |
|---|---|
| V3 Release Thread | https://pcmhacking.net/forums/viewtopic.php?t=8172 |
| Development Thread | https://pcmhacking.net/forums/viewtopic.php?t=7195 |
| V2.1 Thread | https://pcmhacking.net/forums/viewtopic.php?t=7482 |
| V1 Thread | https://pcmhacking.net/forums/viewtopic.php?t=7463 |
| Turbo V6 Patreon | https://www.patreon.com/turbo_v6 |
| YouTube Overview (V3/V4) | https://www.youtube.com/watch?v=EWI_rwSQsas |
| YouTube Initial Release | https://www.youtube.com/watch?v=J3ATR6G7g5E |
| RTLS1 Success Story | https://pcmhacking.net/forums/viewtopic.php?t=7736 |

---

## 8. Relevance to open12587603 Project

For the **open12587603** open-source alternative to Boost OS, key takeaways:

1. **Base OS:** 12587603 is the correct target — it's the P59 OS with the most features and community support.
2. **Free space:** The calibration section has ~237 bytes free at 0x1FEF2–0x1FFDF, plus EGR code space can be reclaimed.
3. **Parameter placement matters:** Placing custom parameters within the standard calibration range (instead of after custom code) would enable calibration-only writes — a major usability improvement over Boost OS.
4. **EGR subsystem is the key enabler:** Re-purposing the EGR solenoid driver and its PI-loop code unlocks open-loop boost control without adding external hardware.
5. **Feature priorities from community:** Dual wideband, flex fuel blending, anti-lag/rolling anti-lag, closed-loop boost control are the most requested additions.
6. **PCM Hammer V21 compatibility:** If we can get the custom OSID registered in PCM Hammer, or design parameters to fit within standard calibration ranges, V21 compatibility becomes possible.
7. **P01 support:** Consider whether open12587603 should target both P01 and P59, since ~50% of the community is stuck on V2.1 due to P01 incompatibility.
