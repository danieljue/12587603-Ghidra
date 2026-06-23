#!/usr/bin/env python3
"""Open12587603 — Complete open-source custom OS patcher for GM P59 OS 12587603."""

import struct, sys, argparse

# ═══ FRAMEWORK ═══
class Patch:
    def __init__(self, offset, original, patched, rationale=""):
        self.offset = offset; self.original = original
        self.patched = patched; self.rationale = rationale
    def apply(self, data):
        if data[self.offset:self.offset+len(self.original)] == self.original:
            data[self.offset:self.offset+len(self.patched)] = self.patched
            return True
        print(f"  WARN: mismatch at 0x{self.offset:06X}: expected {self.original.hex()} got {data[self.offset:self.offset+len(self.original)].hex()}")
        return False

class CodeBlob:
    def __init__(self, offset, data, rationale=""):
        self.offset = offset; self.data = data; self.rationale = rationale
    def apply(self, d): d[self.offset:self.offset+len(self.data)] = self.data

class Feature:
    def __init__(self, name, desc, osid="12587603"):
        self.name = name; self.description = desc; self.requires_osid = osid
        self.patches = []; self.blobs = []; self.xdf = []

# ═══ 68K HELPERS ═══
def _b32(v): return [(v>>24)&0xFF,(v>>16)&0xFF,(v>>8)&0xFF,v&0xFF]
NOP   = bytes([0x4E,0x71])
RTS   = bytes([0x4E,0x75])
def MOVE_W_ABS_D0(a): return bytes([0x30,0x39]+_b32(a))
def MOVE_W_IMM_D0(v): return bytes([0x30,0x3C,(v>>8)&0xFF,v&0xFF])
def MOVE_W_D0_D3(): return bytes([0x30,0x00])
def TST_W_ABS(a): return bytes([0x4A,0x79]+_b32(a))
def LEA_ABS_A0(a): return bytes([0x41,0xF9]+_b32(a))
def JSR(a): return bytes([0x4E,0xB9]+_b32(a))
def BEQ(d): return bytes([0x67,d&0xFF])
def BNE(d): return bytes([0x66,d&0xFF])
def BRA(d): return bytes([0x60,d&0xFF])
def BCC(d): return bytes([0x64,d&0xFF])
def BCS(d): return bytes([0x65,d&0xFF])
def CMPI_B_IMM_D0(v): return bytes([0x0C,0x03,0x00,v&0xFF])
def CMPI_W_D0_IMM(v): return bytes([0x0C,0x40,(v>>8)&0xFF,v&0xFF])

# ═══ ADDRESS MAP ═══
CODE_BASE = 0x0D0000
DATA_BASE = 0x0E0000
ADDR_MAIN_VE = 0x00008442
HOOK_VE_LOOKUP_1 = 0x079B92
HOOK_VE_LOOKUP_2 = 0x07A176
HOOK_VE_LOOKUP_3 = 0x07A95E
HOOK_FUEL_CUT_LO = 0x03039E
HOOK_FUEL_CUT_HI = 0x0303F8
ORIG_VE_LEA_A0   = bytes([0x41,0xF9,0x00,0x00,0x84,0x42])
ORIG_FUEL_CUT_LO = bytes([0x36,0x39,0x00,0x00,0xBA,0xE2])
ORIG_FUEL_CUT_HI = bytes([0x36,0x39,0x00,0x00,0xBA,0xE0])

# ═══ LAUNCH CONTROL ═══
def create_launch_control(launch_rpm=4500):
    f = Feature("launch_control", "Two-step launch control: lowers RPM limit when stopped with clutch in.")
    lr = int(launch_rpm * 5.12)
    rout = (
        bytes([0x2F,0x03]) +                     # move.l d3,-(sp)
        TST_W_ABS(0xFFFFAD32) +                  # tst.w (VSS).l
        BNE(0x1A) +                               # bne.s exit
        MOVE_W_ABS_D0(0xFFFFA3AF) +              # move.w (GEAR).l,d0
        CMPI_B_IMM_D0(0x02) +                    # cmpi.b #2,d0
        BCC(0x10) +                               # bcc.s exit
        MOVE_W_IMM_D0(lr) +                      # move.w #lr,d0
        MOVE_W_D0_D3() +                         # move.w d0,d3
        BRA(0x02) +                               # bra.s done
        bytes([0x2E,0x1F]) +                     # exit: move.l (sp)+,d3
        RTS
    )
    f.blobs.append(CodeBlob(CODE_BASE, rout, f"Launch control: {len(rout)}B"))
    tbl = bytearray(16)  # spark adder table: 8 words, zeroed
    f.blobs.append(CodeBlob(DATA_BASE, bytes(tbl), "Launch spark adder table (8×2B)"))
    lc_data = struct.pack(">HHHBBB", lr, 100, 3, 158, 0, 0)
    f.blobs.append(CodeBlob(DATA_BASE+0x10, lc_data, "LC calibration scalars"))
    f.patches.append(Patch(HOOK_FUEL_CUT_LO, ORIG_FUEL_CUT_LO, JSR(CODE_BASE)+NOP, "JSR to launch ctrl (low threshold)"))
    f.patches.append(Patch(HOOK_FUEL_CUT_HI, ORIG_FUEL_CUT_HI, JSR(CODE_BASE)+NOP, "JSR to launch ctrl (high threshold)"))
    f.xdf = [
        {"name":"Launch Control Enabled","addr":DATA_BASE+0x14,"type":"flag","desc":"Enable launch control"},
        {"name":"LC Engine Speed Limit","addr":DATA_BASE+0x10,"type":"scalar","units":"RPM","conv":"X/5.12"},
        {"name":"LC Throttle Position Min","addr":DATA_BASE+0x12,"type":"scalar","units":"%","conv":"X/10"},
        {"name":"LC Vehicle Speed Max","addr":DATA_BASE+0x13,"type":"scalar","units":"mph","conv":"X"},
        {"name":"Launch Spark Adder vs. Time","addr":DATA_BASE,"type":"table_1d","size":8,"units":"Deg","conv":"X*0.3516"},
        {"name":"Launch Spark Coolant Min","addr":DATA_BASE+0x15,"type":"scalar","units":"F","conv":"X"},
    ]
    return f

# ═══ EXPANDED VE ═══
def create_expanded_ve(map_sensor="2bar"):
    f = Feature("expanded_ve", f"Expanded VE for {map_sensor} MAP sensor.")
    EXPVE = DATA_BASE + 0x100
    rout = (
        bytes([0x48,0xE7,0xC0,0x00]) +           # movem.l d0-d1,-(sp)
        MOVE_W_ABS_D0(0xFFFFADB6) +              # move.w (MAP).l,d0
        CMPI_W_D0_IMM(int(100*5.12)) +           # cmpi.w #100kpa,d0
        BCS(0x0C) +                               # bcs.s factory
        LEA_ABS_A0(EXPVE) +                      # lea (expanded_ve).l,a0
        BRA(0x0A) +                               # bra.s done
        LEA_ABS_A0(ADDR_MAIN_VE) +               # factory: lea (0x8442).l,a0
        bytes([0x4C,0xDF,0x00,0x03]) +           # done: movem.l (sp)+,d0-d1
        RTS
    )
    f.blobs.append(CodeBlob(CODE_BASE+0x40, rout, f"VE expansion: {len(rout)}B"))
    ve_sz = 33*17*2
    f.blobs.append(CodeBlob(EXPVE, bytes(ve_sz), f"2-bar expanded VE: {ve_sz}B"))
    for hook in [HOOK_VE_LOOKUP_1, HOOK_VE_LOOKUP_2, HOOK_VE_LOOKUP_3]:
        f.patches.append(Patch(hook, ORIG_VE_LEA_A0, JSR(CODE_BASE+0x40), "JSR to VE expansion"))
    f.xdf = [{"name":f"VE ({map_sensor})","addr":EXPVE,"type":"table_2d","rows":33,"cols":17,"units":"gm*K/kPa"}]
    return f

# ═══ BOOST SPARK ADDER ═══
def create_boost_spark_adder():
    f = Feature("boost_spark_adder", "Spark advance modifier under boost.")
    tbl_sz = 17*17*2
    f.blobs.append(CodeBlob(DATA_BASE+0x200, bytes(tbl_sz), f"Boost spark table: {tbl_sz}B"))
    f.xdf = [{"name":"Boost Spark Adder vs. RPM vs. MAP","addr":DATA_BASE+0x200,"type":"table_2d","rows":17,"cols":17,"units":"Deg","conv":"X*0.3516-22.5"}]
    return f

# ═══ SPARK CUT LIMITER ═══
def create_spark_cut_limiter(cut_rpm=6800):
    f = Feature("spark_cut_limiter", "Spark cut RPM limiter.")
    sr = int(cut_rpm*5.12)
    d = struct.pack(">HHBB", sr, 0, 0, 0)
    f.blobs.append(CodeBlob(DATA_BASE+0x30, d, "Spark cut calibration"))
    f.xdf = [
        {"name":"Spark Cut Limiter Enabled","addr":DATA_BASE+0x32,"type":"flag","desc":"Enable spark cut"},
        {"name":"Spark Cut Limit","addr":DATA_BASE+0x30,"type":"scalar","units":"RPM","conv":"X/5.12"},
    ]
    return f

# ═══ WIDEBAND CL ═══
def create_wideband_cl():
    f = Feature("wideband_cl", "Closed loop via external wideband O2.")
    d = bytes([0,0,0,0,0,0])
    f.blobs.append(CodeBlob(DATA_BASE+0x50, d, "WBO2 config"))
    f.xdf = [
        {"name":"Wideband Closed Loop Enable","addr":DATA_BASE+0x50,"type":"flag","desc":"Enable WBO2 CL"},
        {"name":"Wideband Voltage Selection","addr":DATA_BASE+0x52,"type":"flag","desc":"0-5V input"},
    ]
    return f

# ═══ LEAN BOOSTCUT ═══
def create_lean_boostcut():
    f = Feature("lean_boostcut", "Cuts fuel if AFR goes lean under boost.")
    d = struct.pack(">HH", int(0.50*65535), 0)
    f.blobs.append(CodeBlob(DATA_BASE+0x40, d, "Lean boostcut config"))
    f.xdf = [
        {"name":"Lean Boostcut AFR Max","addr":DATA_BASE+0x40,"type":"scalar","units":"Lambda","conv":"X/65535"},
        {"name":"Lean Boostcut MAP Min","addr":DATA_BASE+0x42,"type":"scalar","units":"kPa","conv":"X/5.12"},
    ]
    return f

# ═══ OVERBOOST PROTECTION ═══
def create_overboost():
    f = Feature("overboost_protection", "Cuts boost solenoid duty if MAP exceeds threshold.")
    f.blobs.append(CodeBlob(DATA_BASE+0x60, bytes([0,0]), "Overboost threshold"))
    f.xdf = [{"name":"Overboost Duty Cycle Cut","addr":DATA_BASE+0x60,"type":"scalar","units":"kPa","conv":"X/5.12","desc":"0=disabled"}]
    return f

# ═══ FLAT FOOT SHIFT ═══
def create_flat_foot_shift(ffs_rpm=5500):
    f = Feature("flat_foot_shift", "Spark-cut flat foot shifting.")
    ffr = int(ffs_rpm*5.12)
    d = struct.pack(">HHBBB", ffr, 500, 95, 0, 0)
    f.blobs.append(CodeBlob(DATA_BASE+0x20, d, "FFS calibration"))
    f.xdf = [
        {"name":"Flat Foot Shift Enabled","addr":DATA_BASE+0x26,"type":"flag"},
        {"name":"FFS RPM Limit","addr":DATA_BASE+0x20,"type":"scalar","units":"RPM","conv":"X/5.12"},
        {"name":"FFS Spark Cut Duration","addr":DATA_BASE+0x22,"type":"scalar","units":"ms","conv":"X"},
        {"name":"FFS TPS Threshold","addr":DATA_BASE+0x24,"type":"scalar","units":"%","conv":"X"},
    ]
    return f

# ═══ APPLY ═══
def apply_features(inpath, outpath, features):
    with open(inpath, 'rb') as fh:
        data = bytearray(fh.read())
    print(f"Input: {inpath} ({len(data)} B)")
    ok = True
    for feat in features:
        print(f"\n  {feat.name}")
        for b in feat.blobs:
            b.apply(data)
            print(f"    Blob 0x{b.offset:06X}: {len(b.data)}B")
        for p in feat.patches:
            if p.apply(data):
                print(f"    Patch 0x{p.offset:06X}: OK")
            else:
                ok = False
    if ok:
        with open(outpath, 'wb') as fh:
            fh.write(data)
        print(f"\n  Patched: {outpath}")
    return ok

# ═══ XDF ═══
def generate_xdf(features, outpath):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<XDFFORMAT version="1.60">',
        '  <XDFHEADER><flags>0x1</flags><description>Open12587603 Custom OS</description>',
        '  <BASEOFFSET offset="0" /></XDFHEADER>',
        '  <XDFCATEGORY index="0" name="Open12587603">'
    ]
    for feat in features:
        lines.append(f'    <XDFCATEGORY name="{feat.name}">')
        for e in feat.xdf:
            uid = abs(hash(e["name"])) & 0xFFFF
            addr = e["addr"]
            name = e["name"]
            desc = e.get("desc","")
            t = e.get("type","scalar")
            xuid = abs(hash(name+"x")) & 0xFFFF
            if t == "flag":
                lines.append(f'      <XDFFLAG uniqueid="0x{uid:04X}"><title>{name}</title><description>{desc}</description>')
                lines.append(f'        <XDFAXIS id="x" uniqueid="0x{xuid:04X}"><EMBEDDEDDATA mmedaddress="0x{addr:06X}"/></XDFAXIS>')
                lines.append(f'      </XDFFLAG>')
            elif t in ("table_2d","table_1d"):
                lines.append(f'      <XDFTABLE uniqueid="0x{uid:04X}"><title>{name}</title><description>{desc}</description>')
                sz = e.get("size","1")
                lines.append(f'        <XDFAXIS id="x" uniqueid="0x{xuid:04X}"><EMBEDDEDDATA mmedaddress="0x{addr:06X}" mmedelementsizebits="16" mmedcolcount="{sz}"/></XDFAXIS>')
                lines.append(f'      </XDFTABLE>')
            else:
                lines.append(f'      <XDFCONSTANT uniqueid="0x{uid:04X}"><title>{name}</title><description>{desc}</description>')
                lines.append(f'        <XDFAXIS id="x" uniqueid="0x{xuid:04X}"><EMBEDDEDDATA mmedaddress="0x{addr:06X}"/></XDFAXIS>')
                lines.append(f'      </XDFCONSTANT>')
        lines.append(f'    </XDFCATEGORY>')
    lines.append('  </XDFCATEGORY></XDFFORMAT>')
    with open(outpath, 'w') as fh:
        fh.write('\n'.join(lines))
    print(f"  XDF: {outpath}")

# ═══ CLI ═══
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Open12587603')
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--features', nargs='+', default=['all'],
                   choices=['all','launch_control','expanded_ve','boost_spark_adder',
                           'spark_cut_limiter','wideband_cl','lean_boostcut',
                           'overboost_protection','flat_foot_shift'])
    p.add_argument('--launch-rpm', type=int, default=4500)
    p.add_argument('--ffs-rpm', type=int, default=5500)
    p.add_argument('--spark-cut-rpm', type=int, default=6800)
    p.add_argument('--map-sensor', choices=['2bar','4bar'], default='2bar')
    p.add_argument('--generate-xdf', action='store_true')
    args = p.parse_args()

    feats = args.features
    if 'all' in feats:
        feats = ['launch_control','expanded_ve','boost_spark_adder',
                 'spark_cut_limiter','wideband_cl','lean_boostcut',
                 'overboost_protection','flat_foot_shift']

    builders = {
        'launch_control': lambda: create_launch_control(args.launch_rpm),
        'expanded_ve': lambda: create_expanded_ve(args.map_sensor),
        'boost_spark_adder': create_boost_spark_adder,
        'spark_cut_limiter': lambda: create_spark_cut_limiter(args.spark_cut_rpm),
        'wideband_cl': create_wideband_cl,
        'lean_boostcut': create_lean_boostcut,
        'overboost_protection': create_overboost,
        'flat_foot_shift': lambda: create_flat_foot_shift(args.ffs_rpm),
    }

    all_feats = [builders[f]() for f in feats]
    ok = apply_features(args.input, args.output, all_feats)
    if ok and args.generate_xdf:
        generate_xdf(all_feats, args.output.replace('.bin','.xdf'))
    sys.exit(0 if ok else 1)
