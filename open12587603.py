#!/usr/bin/env python3
"""
Open12587603 — Open-source custom OS patcher for GM P59 OS 12587603

Usage:
    python3 open12587603.py --input stock.bin --output custom.bin \\
        --features launch_control --launch-rpm 4500 --generate-xdf

Features are defined in patches/*.json files.
Each patch specifies exact byte-level modifications with rationale.
"""

import json
import struct
import os
import sys
from pathlib import Path

# ─── Patch Framework ───────────────────────────────────────────────

class Patch:
    """A single byte-level modification to the BIN."""
    def __init__(self, offset: int, original: bytes, patched: bytes, rationale: str = ""):
        self.offset = offset
        self.original = original
        self.patched = patched
        self.rationale = rationale
    
    def apply(self, data: bytearray) -> bool:
        """Apply this patch. Returns True if original bytes matched."""
        if data[self.offset:self.offset + len(self.original)] == self.original:
            data[self.offset:self.offset + len(self.patched)] = self.patched
            return True
        print(f"  WARNING: Original bytes don't match at 0x{self.offset:06X}")
        print(f"    Expected: {self.original.hex()}")
        print(f"    Found:    {data[self.offset:self.offset+len(self.original)].hex()}")
        return False

class CodeBlob:
    """A binary blob (compiled 68k code or data table) placed in free space."""
    def __init__(self, offset: int, data: bytes, rationale: str = ""):
        self.offset = offset
        self.data = data
        self.rationale = rationale
    
    def apply(self, data: bytearray):
        data[self.offset:self.offset + len(self.data)] = self.data

class Feature:
    """A named feature composed of multiple patches and code blobs."""
    def __init__(self, name: str, description: str, requires_osid: str = "12587603"):
        self.name = name
        self.description = description
        self.requires_osid = requires_osid
        self.patches: list[Patch] = []
        self.blobs: list[CodeBlob] = []
        self.xdf_entries: list[dict] = []

# ─── Feature Definitions ───────────────────────────────────────────

def create_launch_control(launch_rpm: int = 4500) -> Feature:
    """
    Launch Control for P59 OS 12587603.
    
    How it works:
    1. Custom 68k routine placed at 0xA0000 (OS5 free space)
    2. Routine checks VSS and clutch switch
    3. If VSS==0 AND clutch pressed: overrides RPM limit with launch RPM
    4. Hook: patch sub_30368 (fuel-cut limiter) to JSR to our routine
    
    The launch RPM table is placed at 0xC0000 (OS6 free space).
    """
    f = Feature(
        name="launch_control",
        description="RPM-based launch control. Limits engine speed when vehicle is stopped and clutch is engaged.",
        requires_osid="12587603"
    )
    
    # Scale: RPM * 5.12 = raw value
    launch_rpm_raw = int(launch_rpm * 5.12)
    launch_rpm_hi = struct.pack(">H", launch_rpm_raw)       # Cut fuel above this
    launch_rpm_lo = struct.pack(">H", launch_rpm_raw - 5)   # Re-enable fuel below this (1 RPM hysteresis)
    
    # ================================================================
    # LAUNCH CONTROL 68K SUBROUTINE
    # Place at 0xA0000 (OS5 free space, no checksum needed)
    # ================================================================
    #
    # Pseudocode:
    #   Read VSS from RAM
    #   If VSS > 0: return (use normal threshold)
    #   Read clutch switch
    #   If clutch not pressed: return (use normal threshold)  
    #   Load launch RPM from table indexed by gear
    #   Return with launch RPM as threshold
    #
    # Actual 68k assembly (hand-encoded):
    
    VSS_ADDR = 0xFFFFAD32    # Vehicle speed RAM address (to be verified)
    CLUTCH_ADDR = 0xFFFF8998 # Clutch/brake switch flags (to be verified)
    CLUTCH_BIT = 2            # Bit position for clutch switch (to be verified)
    LAUNCH_TABLE = 0x000C0000 # OS6 free space — launch RPM vs gear table
    
    launch_routine = bytes([
        # Entry: d3 already contains the selected overspeed threshold
        # We check launch conditions and override d3 if active
        
        # Check VSS
        0x4A, 0x39,  # tst.w (VSS_ADDR).l
        (VSS_ADDR >> 24) & 0xFF, (VSS_ADDR >> 16) & 0xFF,
        (VSS_ADDR >> 8) & 0xFF, VSS_ADDR & 0xFF,
        0x66, 0x18,  # bne.s return_normal  (VSS != 0, skip launch)
        
        # Check clutch switch
        0x08, 0x2D,  # btst #CLUTCH_BIT, (CLUTCH_ADDR).l
        CLUTCH_BIT & 0xFF,
        (CLUTCH_ADDR >> 24) & 0xFF, (CLUTCH_ADDR >> 16) & 0xFF,
        (CLUTCH_ADDR >> 8) & 0xFF, CLUTCH_ADDR & 0xFF,
        0x67, 0x10,  # beq.s return_normal  (clutch not pressed)
        
        # Launch mode active! Override threshold with launch RPM
        0x30, 0x3B,  # move.w (LAUNCH_TABLE,pc,d0.w*2), d0
        (LAUNCH_TABLE >> 24) & 0xFF, (LAUNCH_TABLE >> 16) & 0xFF,
        (LAUNCH_TABLE >> 8) & 0xFF, LAUNCH_TABLE & 0xFF,
        0x30, 0x00,  # move.w d0, d3  (d3 = launch RPM threshold)
        
        # Return to caller (falls through to normal overspeed check with modified d3)
        0x4E, 0x75,  # rts
    ])
    
    f.blobs.append(CodeBlob(
        offset=0xA0000,
        data=launch_routine,
        rationale="Launch control 68k subroutine: checks VSS/clutch, overrides RPM limit"
    ))
    
    # ================================================================
    # LAUNCH RPM TABLE (1D, indexed by gear)
    # Place at 0xC0000 (OS6 free space)
    # ================================================================
    # Index: gear 0-7 (park, reverse, neutral, 1st, 2nd, 3rd, 4th, 5th+)
    # Value: launch RPM limit (raw units = RPM * 5.12)
    launch_table = struct.pack(">8H",
        launch_rpm_raw,  # Park — no launch, but set anyway
        launch_rpm_raw,  # Reverse
        launch_rpm_raw,  # Neutral — standard launch limit
        launch_rpm_raw,  # 1st gear — standard launch limit
        launch_rpm_raw,  # 2nd gear — same (launch always in 1st)
        launch_rpm_raw,  # 3rd
        launch_rpm_raw,  # 4th
        launch_rpm_raw,  # 5th+
    )
    
    f.blobs.append(CodeBlob(
        offset=0xC0000,
        data=launch_table,
        rationale="Launch RPM vs gear table (8 words, 16 bytes)"
    ))
    
    # ================================================================
    # PATCH: Hook into sub_30368 (fuel-cut RPM limiter)
    # Replace threshold selection with JSR to our routine
    # ================================================================
    #
    # In sub_30368, the threshold is loaded at offset 0x30 (line 157270+0x30):
    #   move.w (FUEL_CU_KE_PN_ENGINE_OVERSPEED_LOW).l, d3
    #
    # We patch this to JSR to our launch control routine first:
    #   jsr 0xA0000
    #   nop  (pad to preserve alignment)
    #
    # The JSR takes 6 bytes, replacing a 6-byte move.w from absolute address
    
    # Find the exact patch address in the function
    # sub_30368 is at flash address 0x20000 + 0x10368 = 0x30368
    # The threshold load is at offset 0x36 from function start
    patch_addr = 0x30368 + 0x36  # = 0x3039E
    
    # Original: move.w (FUEL_CU_KE_PN_ENGINE_OVERSPEED_LOW).l, d3
    # This is: 0x3639 0x0000BAE2  — 6 bytes
    original_bytes = bytes([0x36, 0x39, 0x00, 0x00, 0xBA, 0xE2])
    
    # Patched: jsr 0xA0000 (0x4EB9 0x000A0000) — 6 bytes
    jsr_patch = bytes([0x4E, 0xB9, 0x00, 0x0A, 0x00, 0x00])
    
    f.patches.append(Patch(
        offset=patch_addr,
        original=original_bytes,
        patched=jsr_patch,
        rationale=f"JSR to launch control routine at 0xA0000. Original loaded overspeed threshold directly."
    ))
    
    # ================================================================
    # XDF ADDITIONS
    # ================================================================
    f.xdf_entries.append({
        "name": "Launch RPM Limit",
        "address": "0xC0000",
        "type": "1D_table",
        "size": 8,
        "units": "RPM",
        "conversion": "X / 5.12",
        "description": "RPM limit when launch control is active (VSS=0, clutch pressed)"
    })
    
    return f


# ─── Main Patcher ──────────────────────────────────────────────────

def apply_features(bin_path: str, output_path: str, features: list[Feature]) -> bool:
    """Apply all features to a stock BIN."""
    with open(bin_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Verify OSID
    osid_offset = 0x600
    osid_bytes = data[osid_offset:osid_offset+4]
    print(f"Input BIN: {bin_path}")
    print(f"Size: {len(data)} bytes")
    print(f"OSID bytes at 0x600: {osid_bytes.hex()}")
    
    success = True
    for feature in features:
        print(f"\nApplying: {feature.name} — {feature.description}")
        
        # Apply code blobs (no verification needed — they go in free space)
        for blob in feature.blobs:
            blob.apply(data)
            print(f"  Code blob at 0x{blob.offset:06X}: {len(blob.data)} bytes — {blob.rationale}")
        
        # Apply patches (verify original bytes)
        for patch in feature.patches:
            ok = patch.apply(data)
            if ok:
                print(f"  Patch at 0x{patch.offset:06X}: {patch.rationale}")
            else:
                success = False
    
    if success:
        with open(output_path, 'wb') as f:
            f.write(data)
        print(f"\nPatched BIN written to: {output_path}")
        print(f"Size: {len(data)} bytes")
        return True
    else:
        print("\nERROR: Some patches failed. Output NOT written.")
        return False


def generate_xdf(features: list[Feature], output_path: str):
    """Generate an XDF file for the patched features."""
    # Basic XDF header
    xdf = """<?xml version="1.0" encoding="UTF-8"?>
<XDFFORMAT version="1.60">
  <XDFHEADER>
    <flags>0x1</flags>
    <description>Open12587603 Custom OS — Open-source performance patches for P59 OS 12587603</description>
    <BASEOFFSET offset="0" />
    <DEFAULTS>
      <datasize>16</datasize>
      <sigdigits>2</sigdigits>
      <outputtype>1</outputtype>
    </DEFAULTS>
    <REGION type="0xFFFFFFFF" startaddress="0x000000" size="0x100000" regionflags="0x0" name="Full Flash" desc="1MB P59 Flash" />
  </XDFHEADER>
  <XDFCATEGORY index="0" name="Open12587603 Features">
"""
    
    for feature in features:
        xdf += f'    <XDFCATEGORY index="0" name="{feature.name}">\n'
        for entry in feature.xdf_entries:
            xdf += f"""      <XDFTABLE uniqueid="0x{hash(entry['name']) & 0xFFFF:04X}">
        <title>{entry['name']}</title>
        <description>{entry.get('description', '')}</description>
        <XDFAXIS id="x" uniqueid="0x{(hash(entry['name']+'x') & 0xFFFF):04X}">
          <EMBEDDEDDATA mmedtypeflags="0x02" mmedaddress="{entry['address']}" />
        </XDFAXIS>
      </XDFTABLE>
"""
        xdf += '    </XDFCATEGORY>\n'
    
    xdf += """  </XDFCATEGORY>
</XDFFORMAT>"""
    
    with open(output_path, 'w') as f:
        f.write(xdf)
    print(f"XDF written to: {output_path}")


# ─── CLI ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Open12587603 — Open-source P59 custom OS patcher')
    parser.add_argument('--input', required=True, help='Stock 12587603 BIN file')
    parser.add_argument('--output', required=True, help='Output patched BIN file')
    parser.add_argument('--features', nargs='+', choices=['launch_control'], 
                       default=['launch_control'], help='Features to apply')
    parser.add_argument('--launch-rpm', type=int, default=4500, help='Launch control RPM limit')
    parser.add_argument('--generate-xdf', action='store_true', help='Generate matching XDF file')
    
    args = parser.parse_args()
    
    features_to_apply = []
    if 'launch_control' in args.features:
        features_to_apply.append(create_launch_control(args.launch_rpm))
    
    # Apply patches
    ok = apply_features(args.input, args.output, features_to_apply)
    
    if ok and args.generate_xdf:
        xdf_path = args.output.replace('.bin', '.xdf')
        generate_xdf(features_to_apply, xdf_path)
    
    sys.exit(0 if ok else 1)
